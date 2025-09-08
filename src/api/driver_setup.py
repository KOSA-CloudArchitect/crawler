import os
import subprocess
import time
import psutil 
import undetected_chromedriver as uc
from fake_useragent import UserAgent

import shutil
import tempfile
import sys
import traceback

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
    print("[INFO] Starting virtual display...")
    os.environ["DISPLAY"] = ":99"
    if not is_xvfb_running():
        subprocess.Popen(['Xvfb', ':99', '-screen', '0', '1920x1080x24'])
        time.sleep(2)
    else:
        print("[INFO] Xvfb already running.")

# pip를 사용하여 undetected-chromedriver 설치
def install_undetected_chromedriver():
    """undetected-chromedriver 자동 설치"""
    print("[INFO] Installing undetected-chromedriver...")
    try:
        # pip를 사용하여 undetected-chromedriver 설치
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "undetected-chromedriver"])
        print("[INFO] undetected-chromedriver 설치 완료")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] undetected-chromedriver 설치 실패: {e}")
        return False

#chromedriver 경로 찾기
def find_chromedriver_path():
    # 기본 경로들 확인
    possible_paths = [
        '/root/.local/share/undetected_chromedriver/undetected_chromedriver',
        '/usr/local/bin/chromedriver',
        '/usr/bin/chromedriver',
        '/opt/chromedriver/chromedriver'
    ]
    
    for path in possible_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path
    
    # PATH에서 chromedriver 찾기
    chromedriver_path = shutil.which('chromedriver')
    if chromedriver_path:
        return chromedriver_path
    
    return None


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

    try:
        # chromedriver 경로 찾기
        uc_path = find_chromedriver_path()
        
        if uc_path:
            print(f"[INFO] Found chromedriver at: {uc_path}")
            driver = uc.Chrome(
                driver_executable_path=uc_path,
                options=options,
                enable_cdp_events=True,
                incognito=True
            )
        else:
            print("[INFO]chromedriver not found, attempting to install...")
            if install_undetected_chromedriver():
                # 설치 후 다시 경로 찾기
                uc_path = find_chromedriver_path()
                if uc_path:
                    print(f"[INFO] Using installed chromedriver at: {uc_path}")
                    driver = uc.Chrome(
                        driver_executable_path=uc_path,
                        options=options,
                        enable_cdp_events=True,
                        incognito=True
                    )
                else:
                    print("[INFO] Installation completed but chromedriver path not found, using default...")
                    driver = uc.Chrome(
                        options=options,
                        enable_cdp_events=True,
                        incognito=True
                    )
            else:
                print("[INFO] Installation failed, using default chromedriver...")
                driver = uc.Chrome(
                    options=options,
                    enable_cdp_events=True,
                    incognito=True
                )
                
    except Exception as e:
        print(f"[ERROR] 드라이버 설정 실패: {e}")
        traceback.print_exc()
        # 에러 발생 시 기본 설정으로 재시도
        try:
            print("⚠ Retrying with default settings...")
            driver = uc.Chrome(
                options=options,
                enable_cdp_events=True,
                incognito=True
            )
        except Exception as e2:
            print(f"[ERROR] 기본 설정으로도 드라이버 설정 실패: {e2}")
            raise e2

    return driver