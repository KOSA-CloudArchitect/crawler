# Dockerfile for crawler

# 1. 베이스 이미지를 slim이 아닌 풀 버전으로 변경
FROM python:3.9-bullseye

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 필요한 패키지 설치 및 Chrome 설치
#    apt-get update와 install을 한 줄에 실행하여 Docker 레이어 캐시 문제를 방지합니다.
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    unzip \
    && wget -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install -y /tmp/chrome.deb \
    && rm /tmp/chrome.deb \
    && wget -O /tmp/chromedriver.zip https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/116.0.5845.96/linux64/chromedriver-linux64.zip \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && rm /tmp/chromedriver.zip \
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
