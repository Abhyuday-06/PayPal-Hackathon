from decimal import Decimal
import time
import httpx
from .gateway import GateError


class ProviderError(RuntimeError):
    def __init__(self, status, name, issues):
        self.status, self.name, self.issues = status, name, issues
        self.safe_message = "PayPal " + name + (": " + ", ".join(issues) if issues else "")
        super().__init__(self.safe_message)


class SimulatedPayments:
    mode = "simulated"

    def create(self, p):
        return {"order_id": "SIM-" + p["id"][:16], "approval_url": None}

    def capture(self, p, allow_new=True):
        if not allow_new:
            raise GateError("EXPIRED", "An expired approval cannot initiate a capture.")
        return {"id": "SIM-CAP-" + p["id"][:16], "amount_cents": p["amount_cents"], "currency": "USD", "mode": self.mode, "status": "COMPLETED"}

    def reconcile(self, p):
        return p.get("receipt")


class PayPalSandbox:
    mode = "paypal"
    base = "https://api-m.sandbox.paypal.com"

    def __init__(self, client_id, secret, merchant_id, frontend_url):
        if not all((client_id, secret, merchant_id)):
            raise RuntimeError("PayPal mode requires sandbox client ID, secret, and merchant ID in backend/.env.")
        self.client_id, self.secret, self.merchant_id = client_id, secret, merchant_id
        self.frontend_url = frontend_url.rstrip("/")

    def request(self, method, path, body=None, request_id=None):
        if method == "GET" and path.startswith("/v2/checkout/orders/") and len(path.split("/")) == 5:
            from .sdk import read_order
            return read_order(self.client_id, self.secret, path.rsplit("/", 1)[1])
        with httpx.Client(timeout=20) as client:
            auth = client.post(self.base + "/v1/oauth2/token", auth=(self.client_id, self.secret), data={"grant_type": "client_credentials"})
            auth.raise_for_status()
            headers = {"Authorization": "Bearer " + auth.json()["access_token"], "Content-Type": "application/json", "Prefer": "return=representation"}
            if request_id:
                headers["PayPal-Request-Id"] = request_id
            payload = {"content": body} if isinstance(body, (bytes, str)) else {"json": body}
            result = client.request(method, self.base + path, headers=headers, **payload)
            if result.status_code >= 400:
                # Do not expose tokens, credentials, or raw provider customer data.
                data = result.json()
                raise ProviderError(result.status_code, data.get("name", "API_ERROR"), [d.get("issue", "UNKNOWN") for d in data.get("details", [])])
            return result.json()

    def create(self, p):
        amount = f"{Decimal(p['amount_cents']) / 100:.2f}"
        body = {
            "intent": "CAPTURE",
            "purchase_units": [{"reference_id": p["id"], "custom_id": p["id"], "payee": {"merchant_id": self.merchant_id}, "amount": {"currency_code": "USD", "value": amount}}],
            "payment_source": {"paypal": {"experience_context": {
                "brand_name": "AgentGate Sandbox", "user_action": "PAY_NOW", "shipping_preference": "NO_SHIPPING",
                "return_url": self.frontend_url + "/?payment=" + p["id"],
                "cancel_url": self.frontend_url + "/?cancelled=" + p["id"],
            }}},
        }
        order = self.request("POST", "/v2/checkout/orders", body, "order-" + p["id"])
        link = next((x["href"] for x in order.get("links", []) if x["rel"] in ("payer-action", "approve")), None)
        if not link or not link.startswith("https://www.sandbox.paypal.com/"):
            raise RuntimeError("PayPal did not provide a sandbox buyer approval link.")
        return {"order_id": order["id"], "approval_url": link}

    def validate(self, order, p):
        units = order.get("purchase_units", [])
        if order.get("id") != p["order_id"] or order.get("intent") != "CAPTURE" or len(units) != 1:
            raise GateError("ORDER_MISMATCH", "PayPal returned an order outside this approval.")
        unit = units[0]
        amount = unit.get("amount", {})
        cents = Decimal(amount.get("value", "-1")) * 100
        if cents != p["amount_cents"] or amount.get("currency_code") != p["currency"] or unit.get("custom_id") != p["id"] or unit.get("payee", {}).get("merchant_id") != self.merchant_id:
            raise GateError("ORDER_MISMATCH", "The PayPal amount, currency, reference, or merchant differs from the approved cart.")

    def receipt(self, order, p):
        self.validate(order, p)
        captures = order["purchase_units"][0].get("payments", {}).get("captures", [])
        if len(captures) != 1 or captures[0].get("status") != "COMPLETED":
            raise RuntimeError("Capture is not confirmed; reconciliation is required.")
        cap = captures[0]
        if Decimal(cap["amount"]["value"]) * 100 != p["amount_cents"] or cap["amount"]["currency_code"] != p["currency"]:
            raise RuntimeError("Capture amount mismatch; retain the budget reservation.")
        return {"id": cap["id"], "amount_cents": p["amount_cents"], "currency": p["currency"], "mode": self.mode, "status": "COMPLETED"}

    def capture(self, p, allow_new=True):
        path = "/v2/checkout/orders/" + p["order_id"]
        order = self.request("GET", path)
        self.validate(order, p)
        if order.get("status") == "COMPLETED":
            return self.receipt(order, p)
        if not allow_new or p["expires_at"] <= time.time():
            raise GateError("EXPIRED", "Approval expired. No new payment can be captured; uncertain funds remain reserved.")
        if order.get("status") != "APPROVED":
            raise GateError("BUYER_APPROVAL_REQUIRED", "Complete the PayPal sandbox buyer approval before capture.")
        self.request("POST", path + "/capture", {}, "cap-" + p["id"])
        # Read the full authoritative order after capture so reconciliation and fresh
        # capture share the same amount/merchant/reference verification.
        try:
            return self.receipt(self.request("GET", path), p)
        except GateError as exc:
            # After a capture POST, a verification mismatch is an uncertain financial
            # outcome, not a harmless preflight policy rejection.
            raise RuntimeError("Post-capture verification failed; retain funds.") from exc

    def reconcile(self, p):
        order = self.request("GET", "/v2/checkout/orders/" + p["order_id"])
        self.validate(order, p)
        return self.receipt(order, p) if order.get("status") == "COMPLETED" else None

    def verify_webhook(self, headers, raw_body, webhook_id):
        import json
        from urllib.parse import urlparse
        names = ["paypal-transmission-id", "paypal-transmission-time", "paypal-cert-url", "paypal-auth-algo", "paypal-transmission-sig"]
        if not webhook_id or any(not headers.get(k) for k in names):
            raise GateError("WEBHOOK_NOT_VERIFIABLE", "Webhook configuration or signature headers are missing.", 400)
        cert = urlparse(headers["paypal-cert-url"])
        if cert.scheme != "https" or cert.hostname not in ("api.sandbox.paypal.com", "api-m.sandbox.paypal.com") or not cert.path.startswith("/v1/notifications/certs/"):
            raise GateError("INVALID_CERTIFICATE_URL", "Only sandbox PayPal certificate URLs are accepted.", 400)
        data = {"transmission_id": headers[names[0]], "transmission_time": headers[names[1]], "cert_url": headers[names[2]], "auth_algo": headers[names[3]], "transmission_sig": headers[names[4]], "webhook_id": webhook_id}
        # Preserve the exact event JSON instead of reserializing signed content.
        body = json.dumps(data)[:-1] + ', "webhook_event": ' + raw_body.decode("utf-8") + "}"
        result = self.request("POST", "/v1/notifications/verify-webhook-signature", body)
        if result.get("verification_status") != "SUCCESS":
            raise GateError("INVALID_WEBHOOK_SIGNATURE", "PayPal rejected the webhook signature.", 401)
        return True
