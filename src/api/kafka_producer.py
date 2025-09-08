import requests
import json

def send_to_kafka_bridge(message: dict):
    """
    Kafka Bridge에 dictionary 메시지를 전송하는 간단한 함수

    :param bridge_url: Kafka Bridge HTTP 주소 (예: http://<NLB_DNS>:8080)
    :param topic: 보낼 토픽 이름
    :param message: 보낼 데이터 (dict)
    """
    bridge_url = "http://k8s-kafka-mybridge-c20dbe855f-1e0ba73150b32ea1.elb.ap-northeast-2.amazonaws.com:8080"
    topic = "realtime-review-collection-topic"
    url = f"{bridge_url}/topics/{topic}"
    headers = {"Content-Type": "application/vnd.kafka.json.v2+json"}
    payload = {"records": [{"value": message}]}

    try:
        res = requests.post(url, headers=headers, data=json.dumps(payload), timeout=5)
        res.raise_for_status()
        #print(f"[INFO] kafka bridge 메시지 전송 성공: {message}")
    except Exception as e:
        print(f"[ERROR] kafka bridge 전송 실패: {e}")



if __name__ == "__main__":
    BRIDGE = "http://k8s-kafka-mybridge-c20dbe855f-1e0ba73150b32ea1.elb.ap-northeast-2.amazonaws.com:8080"
    TOPIC = "realtime-review-collection-topic"

    data = {"job_id": "test-001", "status": "done"}
    send_to_kafka_bridge(data)