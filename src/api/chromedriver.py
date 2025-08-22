import os
import subprocess
import time
import psutil 
import undetected_chromedriver as uc
from fake_useragent import UserAgent


# Step 1: Xvfb 실행 여부 확인
def is_xvfb_running():
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            if 'Xvfb' in proc.info['name'] or (proc.info['cmdline'] and 'Xvfb' in ' '.join(proc.info['cmdline'])):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False


# Step 2: Xvfb 시작 (중복 방지)
def start_xvfb():
    print("▶ Starting virtual display...")
    os.environ["DISPLAY"] = ":99"
    if not is_xvfb_running():
        subprocess.Popen(['Xvfb', ':99', '-screen', '0', '1920x1080x24'])
        time.sleep(2)
    else:
        print("✔ Xvfb already running.")


def setup_driver() -> uc.Chrome:
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    # options.add_argument("--headless=new")  # Headless 제거
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--start-maximized")
    options.add_argument("--incognito")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    random_ua = UserAgent().random
    options.add_argument(f'user-agent={random_ua}')

    driver = uc.Chrome(
        options=options,
        enable_cdp_events=True,
        incognito=True
    )
    return driver