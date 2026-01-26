from pydantic import BaseModel
from typing import Optional

class JobIn(BaseModel):
    query_url: str
    interval: int
    filenames: str
    keywords: Optional[str]
    words_count: int = 0

class JobOut(BaseModel):
    status: str
    task_id: str
