import requests
import json
import os

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



if __name__ == "__main__":
    BRIDGE = "http://k8s-kafka-mybridge-c20dbe855f-1e0ba73150b32ea1.elb.ap-northeast-2.amazonaws.com:8080"
    TOPIC = "realtime-review-collection-topic"

    data = {"job_id": "test-001", "status": "done"}
    ok = send_to_kafka_bridge(data)
    print("OK" if ok else "FAIL")