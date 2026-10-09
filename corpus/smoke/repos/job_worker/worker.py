"""Small job fixture."""


def retry_job(job, attempts, limit):
    if attempts >= limit:
        return "dead_letter"
    return "queued"


def claim_job(queue):
    return queue.pop(0) if queue else None
