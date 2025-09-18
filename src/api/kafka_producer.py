import requests
import json
import os
from datetime import datetime, timezone, timedelta
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

# KST(Asia/Seoul) 현재 시각 ISO 문자열 생성 (중복 정의하여 순환 의존성 방지)
def _now_kst_iso() -> str:
    try:
        if ZoneInfo is not None:
            return datetime.now(ZoneInfo("Asia/Seoul")).isoformat()
    except Exception:
        pass
    return datetime.now(timezone(timedelta(hours=9))).isoformat()

# 카프카 전송
def send_to_kafka_bridge(message: dict, topic: str = "realtime-review-collection-topic") -> None:
    """
    Kafka Bridge에 dictionary 메시지를 전송하는 간단한 함수

    :param message: 보낼 데이터 (dict)
    :param topic: 보낼 토픽 이름 (기본값: realtime-review-collection-topic)
    """
    # 환경변수에서 bridge host를 가져오고, 없으면 기본값 사용
    bridge_host = os.environ.get("KAFKA_BRIDGE_HOST", "k8s-kafka-mybridge-4558db5d39-117a05bf86d57daa.elb.ap-northeast-2.amazonaws.com")
    bridge_url = f"http://{bridge_host}:8080"
    url = f"{bridge_url}/topics/{topic}"
    headers = {"Content-Type": "application/vnd.kafka.json.v2+json"}

    # job_id를 key로 사용 (없으면 오류)
    job_id = message.get("job_id")
    if job_id is None:
        raise ValueError("Kafka 전송 실패: message에 'job_id'가 필요합니다")

    payload = {"records": [{"key": str(job_id), "value": message}]}

    try:
        res = requests.post(url, headers=headers, data=json.dumps(payload), timeout=5)
        res.raise_for_status()
        #print(f"[INFO] kafka bridge 메시지 전송 성공: {message}")
    except Exception as e:
        raise RuntimeError(f"Kafka 전송 실패: {e}")


def send_crawling_completion(job_id: str, count: int, topic: str = "job-control-topic") -> None:
    """
    크롤링 작업 완료 메시지를 Kafka에 전송하는 함수
    
    :param job_id: 작업 ID
    :param count: 크롤링된 데이터 개수
    :param topic: Kafka 토픽 이름 (기본값: job-control-topic)
    """
    final_count = int(count)
    
    # count가 0이면 실패 처리
    if final_count == 0:
        data = {
            "job_id": job_id, 
            "status": "fail", 
            "step": "collection", 
            "failure_reason": "review count 0", 
            "expected_count": final_count, 
            "completed_at": _now_kst_iso()
        }
        print(data)
        send_to_kafka_bridge(data, topic)
        print('[WARN] 크롤링된 데이터가 없어 작업을 실패로 처리합니다.')
    else:
        data = {
            "job_id": job_id, 
            "status": "done", 
            "step": "collection", 
            "expected_count": final_count, 
            "completed_at": _now_kst_iso()
        }
        print(data)
        send_to_kafka_bridge(data, topic)


def send_crawling_error(job_id: str, error_message: str = None, topic: str = "job-control-topic") -> None:
    """
    크롤링 작업 에러 메시지를 Kafka에 전송하는 함수
    
    :param job_id: 작업 ID
    :param error_message: 에러 메시지 (선택사항)
    :param topic: Kafka 토픽 이름 (기본값: job-control-topic)
    """
    data = {
        "job_id": job_id, 
        "status": "fail", 
        "step": "collection", 
        "completed_at": _now_kst_iso()
    }
    
    if error_message:
        data["failure_reason"] = error_message
    
    print(data)
    send_to_kafka_bridge(data, topic)

if __name__ == "__main__":
    BRIDGE = "http://k8s-kafka-mybridge-c20dbe855f-1e0ba73150b32ea1.elb.ap-northeast-2.amazonaws.com:8080"
    TOPIC = "realtime-review-collection-topic"

    data = {"job_id": "test-001", "status": "done"}
    ok = send_to_kafka_bridge(data)
    print("OK" if ok else "FAIL")