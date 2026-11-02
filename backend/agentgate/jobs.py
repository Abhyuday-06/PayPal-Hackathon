import json
import time
import uuid
from threading import Event, Thread
from .gateway import GateError


class Jobs:
    def __init__(self, gateway):
        self.gateway = gateway

    def enqueue(self, kind, payload, db=None):
        job = {"id": uuid.uuid4().hex, "kind": kind, "state": "queued", "payload": payload, "created_at": time.time(), "updated_at": time.time(), "lease_until": 0, "attempts": 0, "progress": 0, "rows": []}
        if db is not None:
            db.execute("INSERT INTO jobs VALUES (?, ?)", (job["id"], json.dumps(job)))
        else:
            with self.gateway.tx() as conn:
                conn.execute("INSERT INTO jobs VALUES (?, ?)", (job["id"], json.dumps(job)))
        return job

    def get(self, jid):
        with self.gateway.tx() as db:
            row = db.execute("SELECT data FROM jobs WHERE id=?", (jid,)).fetchone()
        if not row:
            raise GateError("NOT_FOUND", "That job does not exist.", 404)
        return json.loads(row[0])

    def list(self, kind=None):
        with self.gateway.tx() as db:
            jobs = [json.loads(row[0]) for row in db.execute("SELECT data FROM jobs").fetchall()]
        return sorted([j for j in jobs if kind is None or j["kind"] == kind], key=lambda j: j["created_at"], reverse=True)[:30]

    def update(self, job, **changes):
        with self.gateway.tx() as db:
            row = db.execute("SELECT data FROM jobs WHERE id=?", (job["id"],)).fetchone()
            current = json.loads(row[0])
            if job.get("lease_token") and current.get("lease_token") != job["lease_token"]:
                raise GateError("JOB_LEASE_LOST", "Another worker recovered this job.")
            current.update(changes, updated_at=time.time(), lease_until=time.time() + 240)
            db.execute("UPDATE jobs SET data=? WHERE id=?", (json.dumps(current), job["id"]))
        return current

    def claim(self):
        with self.gateway.tx() as db:
            jobs = [json.loads(r[0]) for r in db.execute("SELECT data FROM jobs").fetchall()]
            for job in sorted(jobs, key=lambda j: j["created_at"]):
                if (job["state"] == "queued" and job.get("next_run_at", 0) <= time.time()) or (job["state"] == "running" and job.get("lease_until", 0) < time.time()):
                    job.update(state="running", lease_token=uuid.uuid4().hex, lease_until=time.time() + 240, attempts=job["attempts"] + 1)
                    db.execute("UPDATE jobs SET data=? WHERE id=?", (json.dumps(job), job["id"]))
                    return job
        return None


class Worker:
    def __init__(self, jobs, handlers):
        self.jobs, self.handlers = jobs, handlers
        self.stopped = Event()
        self.thread = Thread(target=self.run, name="agentgate-worker", daemon=True)

    def start(self):
        self.thread.start()

    def stop(self):
        self.stopped.set()
        self.thread.join(timeout=2)

    def run(self):
        while not self.stopped.is_set():
            job = None
            try:
                job = self.jobs.claim()
                if job:
                    self.handlers[job["kind"]](job)
            except Exception as exc:
                if job:
                    try:
                        retry = job["kind"] == "reconcile" and job["attempts"] < 5
                        self.jobs.update(job, state="queued" if retry else "failed", next_run_at=time.time() + min(2 ** job["attempts"] * 2, 60), error=exc.message if isinstance(exc, GateError) else type(exc).__name__)
                    except Exception:
                        pass
            self.stopped.wait(1)
