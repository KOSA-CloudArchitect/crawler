# Dockerfile for crawler

# 1. 베이스 이미지 선택 (Python 3.9)
FROM python:3.9-slim

# 2. Selenium 구동에 필요한 시스템 의존성(Chrome, ChromeDriver) 설치
RUN apt-get update && apt-get install -y wget unzip && rm -rf /var/lib/apt/lists/*
RUN wget -O /tmp/chromedriver.zip https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/116.0.5845.96/linux64/chromedriver-linux64.zip && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    rm /tmp/chromedriver.zip
RUN wget -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get install -y /tmp/chrome.deb && \
    rm /tmp/chrome.deb

# 3. 작업 디렉토리 설정
WORKDIR /app

# 4. Python 라이브러리 설치 (코드 복사 전 실행하여 캐시 활용)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 애플리케이션 코드 복사
COPY ./src ./src
COPY README.md .

# 6. 컨테이너 실행 시 실행할 명령어 (진입점: src/main.py)
CMD ["python", "src/main.py"]
