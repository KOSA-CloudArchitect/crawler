from pydantic import BaseModel

class CrawlRequest(BaseModel):
    product_id: str
    url_list: list
    job_id: str

class CrawlProductOneRequest(BaseModel):
    product_id: str
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