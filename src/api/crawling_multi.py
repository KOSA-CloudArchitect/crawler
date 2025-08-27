from api.crawling_review import coupang_crawling
from api.driver_setup import start_xvfb

from multiprocessing import Pool, cpu_count, freeze_support, set_start_method
from datetime import datetime
import traceback


set_start_method("spawn", force=True)

def generate_job_id():
    now = datetime.now()
    return "job_" + now.strftime("%Y%m%d_%H%M%S")

def run_multi_process(url_list: list, job_id: str) -> None:
    # CPU 절반 사용
    print("[INFO] multi processor 수: ",cpu_count()//2)

    job_ids = [job_id for _ in url_list]
    with Pool(processes=3) as pool:
        pool.map(coupang_crawling, zip(url_list, job_ids))

# 전체 파이프라인
#def crawling_run(keyword: str, max_link: int, is_crawling_running: bool ) -> None:
def crawling_run() -> None:
    try:
        #freeze_support()
        job_id = generate_job_id()
        print(f"[INFO] 생성된 작업 ID: {job_id}")

        # 가상 디스플레이 시작
        start_xvfb()    
        
        # 크롤링 멀티프로세싱
        #product_link_list = get_product_links(keyword, max_link)
        links = [
            "https://www.coupang.com/vp/products/4548468621?itemId=13569079594&vendorItemId=80822526378&pickType=COU_PICK&q=%EC%B2%AD%EC%86%8C%EA%B8%B0&searchId=d78155d52759146&sourceType=search&itemsCount=36&searchRank=6&rank=6",
            "https://www.coupang.com/vp/products/6224605496?itemId=12196225924&vendorItemId=85326747347&sourceType=srp_product_ads&clickEventId=4745aa00-8150-11f0-8196-f228a66d645a&korePlacement=15&koreSubPlacement=1&clickEventId=4745aa00-8150-11f0-8196-f228a66d645a&korePlacement=15&koreSubPlacement=1"
        ]
        run_multi_process(links, job_id)
        
            
        # spark server 작업 완료 알람
        #notify_spark_server(storage_dir)
        

        print('[INFO] 크롤링 요청 작업 완료')
    except Exception as e:
        print(f'[ERROR] {job_id} 작업 중 에러가 발생했습니다: ',e)
        traceback.print_exc()
    finally:
        print("종료")
        #is_crawling_running.value = False

if __name__=="__main__":
    # search_url = '청소기'
    # max_link = 10
    # freeze_support()
    # product_link_list = get_product_links(search_url, max_link)
    # run_multi_process(product_link_list)
    crawling_run()