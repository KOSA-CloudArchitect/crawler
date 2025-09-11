from api.crawling_review import coupang_crawling
from api.driver_setup import start_xvfb
from api.kafka_producer import send_to_kafka_bridge

from multiprocessing import Pool, cpu_count, freeze_support
from datetime import datetime
import traceback
import time
import random


def generate_job_id():
    now = datetime.now()
    return "job_" + now.strftime("%Y%m%d_%H%M%S")

 # 시작 지터로 사이트 측 레이트 리밋 완화
def _worker_wrapper(args):
    time.sleep(random.uniform(0.0, 1.5))
    return coupang_crawling(args)

def run_product_one_multi_process(url: str, job_id: str, review_cnt: int):
    if review_cnt >= 300:
        page_divide = [0,1,2]
    else:
        page_divide = list(range(review_cnt // 100))

    job_ids = [job_id for _ in page_divide]
    urls = [url for _ in page_divide]

    with Pool(processes=3) as pool:
        pool.map(_worker_wrapper, zip(urls, job_ids, page_divide))

def run_multi_process(url_list: list, job_id: str) -> None:
    # CPU 절반 사용
    multi_cpu = cpu_count() // 2
    print("[INFO] multi processor 수: ", multi_cpu)

    job_ids = [job_id for _ in url_list]
    with Pool(processes=multi_cpu) as pool:
        pool.map(_worker_wrapper, zip(url_list, job_ids))

# 여러 상품 멀티 크롤링
def multi_crawling_run(url_list: list, job_id: str, is_crawling_running: bool) -> None:
    try:

        print(f"[INFO] 멀티프로세스 크롤링 작업 시작: {job_id}")

        run_multi_process(url_list, job_id)
        
        # Kafka에 크롤링 작업 완료 메시지 전송
        data = {"job_id": job_id, "status": "done"}
        send_to_kafka_bridge(data)
            
        print('[INFO] 크롤링 요청 작업 완료')
    except Exception as e:
        data = {"job_id": job_id, "status": "fail"}
        send_to_kafka_bridge(data)
        print(f'[ERROR] {job_id} 작업 중 에러가 발생했습니다: ',e)
        traceback.print_exc()
    finally:
        try:
            is_crawling_running.value = False
        except Exception as e:
            print(f"[WARN] 상태 업데이트 실패(무시): {e}")

# 특정 상품 멀티 크롤링
def multi_product_one_crawling_run(url: str, job_id: str, review_cnt: int, is_crawling_running: bool) -> None:
    try:

        print(f"[INFO] 멀티프로세스 크롤링 작업 시작: {job_id}")

        # 가상 디스플레이 시작
        #start_xvfb()     

        run_product_one_multi_process(url, job_id, review_cnt)
        
        # Kafka에 크롤링 작업 완료 메시지 전송
        data = {"job_id": job_id, "status": "done"}
        send_to_kafka_bridge(data)

        print('[INFO] 크롤링 요청 작업 완료')
    except Exception as e:
        print(f'[ERROR] {job_id} 작업 중 에러가 발생했습니다: ',e)
        traceback.print_exc()
    finally:
        try:
            is_crawling_running.value = False
        except Exception as e:
            print(f"[WARN] 상태 업데이트 실패(무시): {e}")

if __name__=="__main__":
    # search_url = '청소기'
    # max_link = 10
    # freeze_support()
    # product_link_list = get_product_links(search_url, max_link)
    # run_multi_process(product_link_list)
    multi_crawling_run()