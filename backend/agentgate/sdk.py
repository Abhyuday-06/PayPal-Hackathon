"""Read authoritative orders with the APIMatic-generated PayPal Server SDK.

Signatures verified against paypal-server-sdk 2.4.0 and the official Context
Plugin's Python guidance. Logging stays disabled; credentials never enter reports.
"""
from paypalserversdk.api_helper import APIHelper
from paypalserversdk.configuration import Environment
from paypalserversdk.http.auth.o_auth_2 import ClientCredentialsAuthCredentials
from paypalserversdk.paypal_serversdk_client import PaypalServersdkClient


def read_order(client_id, secret, order_id):
    client = PaypalServersdkClient(environment=Environment.SANDBOX, timeout=20, max_retries=0, logging_configuration=None, client_credentials_auth_credentials=ClientCredentialsAuthCredentials(o_auth_client_id=client_id, o_auth_client_secret=secret))
    try:
        response = client.orders.get_order({"id": order_id})
    except Exception:
        raise RuntimeError("PayPal SDK order lookup failed. Check provider availability and private sandbox credentials.") from None
    if response.status_code != 200 or response.body.id != order_id:
        raise RuntimeError("SDK returned an unexpected order response.")
    return APIHelper.to_dictionary(response.body)
