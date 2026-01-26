from app.db import SessionLocal
from app.models import Job

def save_job(job_in):
    db = SessionLocal()
    try:
        job = Job(**job_in.dict())
        db.add(job)
        db.commit()
        db.refresh(job)

        job.job_id = f"JOB-{job.id}"
        db.commit()
        db.refresh(job)

        return job
    finally:
        db.close()