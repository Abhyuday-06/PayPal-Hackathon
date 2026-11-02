from concurrent.futures import ThreadPoolExecutor
from tempfile import TemporaryDirectory
from pathlib import Path
import time
from .gateway import Gateway, GateError
from .payments import SimulatedPayments


def run_lab():
    """Deterministic boundary checks, not a live-model security benchmark."""
    results = []
    with TemporaryDirectory(prefix="agentgate-lab-") as folder:
        def case(name, expected, run):
            start = time.perf_counter()
            g = Gateway(str(Path(folder) / (str(len(results)) + ".db")), SimulatedPayments())
            try:
                passed, observed = run(g)
            except Exception as exc:
                passed, observed = False, type(exc).__name__ + ": " + str(exc)
            results.append({"name": name, "expected": expected, "observed": observed, "passed": passed, "duration_ms": round((time.perf_counter() - start) * 1000)})

        def request(g, sku="cable-20", agent="iris", ttl=600):
            return g.propose(agent, [{"sku": sku, "quantity": 1}], ttl=ttl)

        def purchase(g):
            p = request(g)
            g.approve(p["id"], p["cart_hash"])
            g.order(p["id"], p["cart_hash"])
            g.capture(p["id"], p["cart_hash"])
            m = g.state()["mandates"][0]
            return m["spent_cents"] == 2000 and m["reserved_cents"] == 0, "$20 spent; $80 available"

        def policy_block(g, sku, code):
            p = request(g, sku)
            return p["state"] == "blocked" and p.get("block_code") == code, p.get("block_code", p["state"])

        def denied(fn, code):
            try:
                fn()
                return False, "Unexpectedly allowed"
            except GateError as exc:
                return exc.code == code, exc.code

        def concurrent(g):
            a, b = request(g, "mic-80"), request(g, "mic-80", "nova")
            def approve(p):
                try:
                    return g.approve(p["id"], p["cart_hash"])["state"]
                except GateError as exc:
                    return exc.code
            with ThreadPoolExecutor(max_workers=2) as pool:
                outcomes = list(pool.map(approve, [a, b]))
            m = g.state()["mandates"][0]
            return sorted(outcomes) == ["BUDGET_EXCEEDED", "approved"] and m["reserved_cents"] == 8000, "One $80 reservation; the other blocked"

        def expired(g):
            p = request(g, ttl=1)
            original = g.clock()
            g.clock = lambda: original + 2
            return denied(lambda: g.approve(p["id"], p["cart_hash"]), "NOT_APPROVABLE")

        def tampered(g):
            p = request(g)
            g.approve(p["id"], p["cart_hash"])
            return denied(lambda: g.order(p["id"], "a-different-cart"), "CART_CHANGED")

        def replay(g):
            p = request(g)
            g.approve(p["id"], p["cart_hash"])
            g.order(p["id"], p["cart_hash"])
            first = g.capture(p["id"], p["cart_hash"])
            second = g.capture(p["id"], p["cart_hash"])
            return first["receipt"] == second["receipt"] and g.state()["mandates"][0]["spent_cents"] == 2000, "Same receipt returned; $20 spent once"

        def unapproved(g):
            p = request(g)
            return denied(lambda: g.order(p["id"], p["cart_hash"]), "APPROVAL_REQUIRED")

        def released(g):
            p = request(g, "mic-80")
            g.approve(p["id"], p["cart_hash"])
            g.cancel(p["id"])
            return g.state()["mandates"][0]["available_cents"] == 10000, "$100 available after cancellation"

        case("Legitimate purchase", "Allow a permitted $20 cart", purchase)
        case("Oversized cart", "Reject the $140 rig", lambda g: policy_block(g, "rig-140", "TRANSACTION_LIMIT"))
        case("Unapproved merchant", "Reject the external seller", lambda g: policy_block(g, "external-20", "MERCHANT_NOT_ALLOWED"))
        case("Injected product fixture", "Reject the disallowed watch proposal", lambda g: policy_block(g, "watch-300", "CATEGORY_NOT_ALLOWED"))
        case("Concurrent agents", "Only one $80 cart can reserve the $100 budget", concurrent)
        case("Expired approval", "Reject the expired proposal", expired)
        case("Cart changed after approval", "Reject a changed cart fingerprint", tampered)
        case("Repeated capture", "Spend once and return the same receipt", replay)
        case("Missing owner approval", "Prevent payment creation", unapproved)
        case("Cancelled reservation", "Release unused funds", released)
    return {"kind": "deterministic_gateway_suite", "payment_mode": "simulated", "uses_live_model": False, "passed": sum(r["passed"] for r in results), "total": len(results), "results": results}
