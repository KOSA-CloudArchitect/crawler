from api.crawling_review import coupang_crawling, _now_kst_iso
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
    result = coupang_crawling(args)

    return result or 0

def run_product_one_multi_process(url: str, job_id: str, review_cnt: int, expected_count=None, counter_lock=None):
    if review_cnt >= 300:
        page_divide = [0,1,2]
    else:
        if review_cnt  < 100:
            review_cnt = 100
        page_divide = list(range(review_cnt // 100))

    job_ids = [job_id for _ in page_divide]
    urls = [url for _ in page_divide]
    multi_cpu = cpu_count() // 2
    print("[INFO] multi processor 갯수: ", multi_cpu)
    with Pool(processes=multi_cpu) as pool:
        counts = pool.map(_worker_wrapper, zip(urls, job_ids, page_divide))

    total = sum(counts)
    if expected_count is not None and counter_lock is not None:
        with counter_lock:
            expected_count.value += int(total)
    return total

def run_multi_process(url_list: list, job_id: str, expected_count=None, counter_lock=None) -> None:
    # CPU 절반 사용
    multi_cpu = cpu_count() // 2
    print("[INFO] multi processor 갯수: ", multi_cpu)

    job_ids = [job_id for _ in url_list]
    with Pool(processes=multi_cpu) as pool:
        counts = pool.map(_worker_wrapper, zip(url_list, job_ids))

    total = sum(counts)
    if expected_count is not None and counter_lock is not None:
        with counter_lock:
            expected_count.value += int(total)
    return total

# 여러 상품 멀티 크롤링
def multi_crawling_run(url_list: list, job_id: str, is_crawling_running: bool, expected_count=None, counter_lock=None) -> None:
    try:

        print(f"[INFO] 멀티프로세스 크롤링 작업 시작: {job_id}")

        total = run_multi_process(url_list, job_id, expected_count, counter_lock)
        
        # Kafka에 크롤링 작업 완료 메시지 전송
        final_count = int(expected_count.value) if expected_count is not None else int(total)
        data = {"job_id": job_id, "status": "done", "step": "collection", "expected_count": final_count, "completed_at": _now_kst_iso()}
        print(data)
        send_to_kafka_bridge(data, "job-control-topic")
            
        print('[INFO] 크롤링 요청 작업 완료')
    except Exception as e:
        data = {"job_id": job_id, "status": "fail", "step": "collection", "completed_at": _now_kst_iso()}
        send_to_kafka_bridge(data, "job-control-topic")
        print(f'[ERROR] {job_id} 작업 중 에러가 발생했습니다: ',e)
        traceback.print_exc()
    finally:
        try:
            is_crawling_running.value = False
        except Exception as e:
            print(f"[WARN] 상태 업데이트 실패(무시): {e}")

# 특정 상품 멀티 크롤링
def multi_product_one_crawling_run(url: str, job_id: str, review_cnt: int, is_crawling_running: bool, expected_count=None, counter_lock=None) -> None:
    try:

        print(f"[INFO] 멀티프로세스 크롤링 작업 시작: {job_id}")

        # 가상 디스플레이 시작
        #start_xvfb()     

        total = run_product_one_multi_process(url, job_id, review_cnt, expected_count, counter_lock)
        
        # Kafka에 크롤링 작업 완료 메시지 전송
        final_count = int(expected_count.value) if expected_count is not None else int(total)
        data = {"job_id": job_id, "status": "done", "step": "collection", "expected_count": final_count, "completed_at": _now_kst_iso()}
        print(data)
        send_to_kafka_bridge(data, "job-control-topic")

        print('[INFO] 크롤링 요청 작업 완료')
    except Exception as e:
        data = {"job_id": job_id, "status": "fail", "step": "collection", "completed_at": _now_kst_iso()}
        send_to_kafka_bridge(data, "job-control-topic")
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