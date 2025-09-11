# Python 3.11 slim 이미지를 베이스로 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 arm64용 Chromium, 드라이버, 기타 도구 설치 (단일 레이어)
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    curl \
    xvfb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt 복사 및 Python 패키지 설치 (레이어 캐싱 활용)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 현재 디렉토리의 모든 소스 코드를 WORKDIR(/app)에 복사
COPY . .

# 포트 8000 노출
EXPOSE 8000

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV DISPLAY=:99

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/proxy/status || exit 1

# 애플리케이션 실행
WORKDIR /app/src
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
