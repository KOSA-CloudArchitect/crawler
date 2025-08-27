from pydantic import BaseModel

class CrawlRequest(BaseModel):
    keyword: str
    max_links: int

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