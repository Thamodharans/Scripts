from app.sheets import update_job

def register_job(row, status, links=None, error=None):
    if status == "done":
        update_job(row, status, "\n".join(links.values()))
    elif status == "failed":
        update_job(row, status, error)
    else:
        update_job(row, status)
