"""Keep tests independent of the user's real sandbox environment and ledger."""
import os
import tempfile
from pathlib import Path

_test_dir = tempfile.TemporaryDirectory(prefix="agentgate-pytest-")
os.environ["PAYMENT_MODE"] = "simulated"
os.environ["DATABASE_URL"] = ""
os.environ["AGENTGATE_OWNER_TOKEN"] = "test-owner-key"
os.environ["AGENTGATE_IRIS_TOKEN"] = "test-iris-key"
os.environ["AGENTGATE_NOVA_TOKEN"] = "test-nova-key"
os.environ["AGENTGATE_DB_PATH"] = str(Path(_test_dir.name) / "isolated-api.db")
