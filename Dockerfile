# Dockerfile for crawler (arm64 compatible)

# 1. 베이스 이미지 선택 (이전과 동일)
FROM python:3.9-bullseye

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. Debian 저장소를 통해 arm64용 Chromium 및 관련 도구 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 4. Python 라이브러리 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 애플리케이션 코드 복사
COPY ./src ./src
COPY README.md .

# 6. 컨테이너 실행 시 실행할 명령어
CMD ["python", "src/main.py"]
