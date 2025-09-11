from contextlib import asynccontextmanager

from api.crawling_multi import multi_crawling_run, multi_product_one_crawling_run
from api.crawling_info_list import get_info_list

from model.crawling_model import CrawlRequest,CrawlProductOneRequest, crawlResponse, InfoListRequest

from fastapi import FastAPI, HTTPException
from multiprocessing import Process, Manager
import uvicorn
import asyncio
from concurrent.futures import ProcessPoolExecutor
import logging
#logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)



# app 시작/종료 작업 설정
@asynccontextmanager
async def lifespan(app:FastAPI):
    """
    애플리케이션 시작 시 Manager와 공유 변수를 초기화합니다.
    이는 모든 FastAPI 워커 프로세스에서 단 한 번만 실행
    """
    print("애플리케이션 시작: Manager 및 공유 상태 변수 초기화")
    # manager와 status를 app.state에 저장하여 전역적으로 접근 가능
    app.state.manager = Manager()
    app.state.is_crawling_running = app.state.manager.Value('b', False)
    #print(f"초기 is_crawling_running.value: {app.state.is_crawling_running.value}")
    
    yield # yield 이전 코드는 fastapi시작할 때 실행됨 / 이후 코드는 종료될 때 실행
    
    print("애플리케이션 종료: Manager 종료")
    if hasattr(app.state, 'manager'):
        app.state.manager.shutdown()

# app 실행
app = FastAPI(lifespan=lifespan)

# 크롤링 요청
@app.post("/crawl/product_multi")
def start_crawling(req: CrawlRequest):
    try:
        # 요청 데이터 확인

        url_list = req.url_list
        job_id = req.job_id

        # 크롤링 상태 확인
        is_crawling_running = app.state.is_crawling_running
        print(f"[INFO] job_id: {job_id} 여러 상품에 대한 실시간 분석 요청이 들어왔습니다.")

        # 상태를 True로 설정하고 새 프로세스 실행
        if is_crawling_running.value == True:
            print("[INFO] 작업이 이미 실행중이라 요청을 반려합니다.")
            return {"status": "processing", "message": "작업이 이미 실행 중입니다."}
        
        is_crawling_running.value = True
        print(f"[INFO] job_id: {job_id} 여러 상품에 대한 크롤링 작업을 실행합니다.")

        # 크롤링 작업 실행
        p = Process(target=multi_crawling_run, args=(url_list, job_id, is_crawling_running))
        p.start()

        return {"status": "started", "message": f"'job_id: {job_id}'에 여러 상품에 대한 크롤링 작업을 시작했습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 한 상품 멀티 프로세싱 크롤링 요청
@app.post("/crawl/product_one")
def start_crawling(req: CrawlProductOneRequest):
    try:
        # 요청 데이터 확인
        url = req.url
        job_id = req.job_id
        review_cnt = req.review_cnt

        # 크롤링 상태 확인
        is_crawling_running = app.state.is_crawling_running
        print(f"[INFO] job_id: {job_id} 특정 상품에 대한 실시간 분석 요청이 들어왔습니다.")

        # 상태를 True로 설정하고 새 프로세스 실행
        if is_crawling_running.value == True:
            print("[INFO] 작업이 이미 실행중이라 요청을 반려합니다.")
            return {"status": "processing", "message": "작업이 이미 실행 중입니다."}
        
        is_crawling_running.value = True
        print(f"[INFO]  job_id: {job_id} 특정 상품 분석 크롤링 작업을 실행합니다.")

        # 크롤링 작업 실행
        p = Process(target=multi_product_one_crawling_run, args=(url, job_id, review_cnt, is_crawling_running))
        p.start()

        return {"status": "started", "message": f"'job_id: {job_id} 대한 특정 상품 분석 크롤링 작업을 시작했습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 상품 정보 목록 요청
# 비동기로 상품 정보 목록 추출 (테스트용 - 결과를 바로 반환)
# response: [{url, product_code, img, title, final_price, origin_price, review_count, review_rating}, ...]
@app.post("/info_list")
async def get_info_list_async(req: InfoListRequest):
    try:
        # 요청 데이터 확인
        keyword = req.keyword
        max_links = req.max_links
        print(f"[INFO] {keyword} 상품 정보 목록 요청이 들어왔습니다.")

        # 크롤링 상태 확인
        is_crawling_running = app.state.is_crawling_running
        if is_crawling_running.value == True:
            return {"status": "processing", "message": "작업이 이미 실행 중입니다."}

        is_crawling_running.value = True
        
        try:
            # ProcessPoolExecutor를 사용하여 별도 프로세스에서 실행
            with ProcessPoolExecutor(max_workers=1) as executor:
                loop = asyncio.get_event_loop()
                info_list = await loop.run_in_executor(
                    executor, 
                    get_info_list, 
                    keyword, 
                    max_links
                )
            
            print(f"[INFO] {keyword} 상품 정보 목록 추출 완료: {len(info_list)}개 상품")
            
            # 결과를 바로 response에 담아서 반환
            if len(info_list) == 0:
                return {
                    "status": "error", 
                    "message": f"'{keyword}'에 대한 정보 목록을 찾을 수 없습니다.",
                    "info_list": []
                }
            else:
                return {
                    "status": "success", 
                    "message": f"'{keyword}'에 대한 정보 목록을 반환했습니다.",
                    "info_list": info_list
                }
                
        except Exception as e:
            print(f"[ERROR] 상품 정보 목록 추출 중 에러: {e}")
            return {
                "status": "error",
                "message": f"상품 정보 목록 추출 중 에러가 발생했습니다: {str(e)}",
                "info_list": []
            }
        finally:
            is_crawling_running.value = False
            print(f"[INFO] {keyword} 상품 정보 목록 작업 완료")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# 상품 정보 목록 상태 확인
@app.get("/info_list/status/{keyword}")
async def get_info_list_status(keyword: str):
    """상품 정보 목록 추출 상태를 확인하는 엔드포인트"""
    try:
        is_crawling_running = app.state.is_crawling_running
        
        if is_crawling_running.value:
            return {
                "status": "processing",
                "message": f"'{keyword}'에 대한 상품 정보 목록을 추출 중입니다."
            }
        else:
            return {
                "status": "completed",
                "message": f"'{keyword}'에 대한 상품 정보 목록 추출이 완료되었습니다."
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    #freeze_support()  # Windows 필수
    try:
        from multiprocessing import set_start_method
        set_start_method("spawn", force=True)
    except Exception:
        pass
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)