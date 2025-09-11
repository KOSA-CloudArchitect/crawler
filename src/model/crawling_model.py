from pydantic import BaseModel

class CrawlRequest(BaseModel):
    url_list: list
    job_id: str

class CrawlProductOneRequest(BaseModel):
    url: str
    job_id: str
    review_cnt: int

class crawlResponse(BaseModel):
    message: str
    status: str

class InfoListRequest(BaseModel):
    keyword: str
    max_links: int

class InfoListResponse(BaseModel):
    message: str
    status: str
    info_list: list