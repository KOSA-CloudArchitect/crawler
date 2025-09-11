# Python 3.11 slim 이미지를 베이스로 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Chrome 설치를 위한 Google Chrome 공식 GPG 키 추가
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/googlechrome-linux-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/googlechrome-linux-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list

# Chrome 140 최신 버전 설치
RUN apt-get update && apt-get install -y \
    google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Chrome 140에 맞는 최신 ChromeDriver 설치 (새로운 저장소 사용)
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}') && \
    echo "Chrome version: $CHROME_VERSION" && \
    # Chrome 115+ 버전용 새로운 ChromeDriver 저장소에서 최신 버전 다운로드
    CHROMEDRIVER_VERSION=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_${CHROME_VERSION%.*}") && \
    echo "ChromeDriver version: $CHROMEDRIVER_VERSION" && \
    wget -O /tmp/chromedriver.zip "https://storage.googleapis.com/chrome-for-testing-public/$CHROMEDRIVER_VERSION/linux64/chromedriver-linux64.zip" && \
    unzip /tmp/chromedriver.zip -d /tmp/ && \
    mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver && \
    rm -rf /tmp/chromedriver* /tmp/chromedriver-linux64

# requirements.txt 복사 및 Python 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# undetected-chromedriver 미리 설치 (네트워크 문제 방지)
RUN pip install --no-cache-dir undetected-chromedriver

# 소스 코드 복사
COPY src/ ./src/

# 포트 8000 노출
EXPOSE 8000

# 환경 변수 설정
ENV PYTHONPATH=/app/src
ENV DISPLAY=:99

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/proxy/status || exit 1

# 애플리케이션 실행
WORKDIR /app/src
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

