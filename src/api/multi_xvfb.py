import os, time, subprocess, socket, atexit, random
from contextlib import contextmanager
from pathlib import Path

XVFB_BIN = "/usr/bin/Xvfb"   # Rocky9 기본 위치 (which Xvfb 로 확인)
X11_SOCK_DIR = "/tmp/.X11-unix"

def _is_display_in_use(display_num: int) -> bool:
    """소켓 파일 /tmp/.X11-unix/X<display> 유무로 사용중 여부 확인"""
    return Path(f"{X11_SOCK_DIR}/X{display_num}").exists()

def _find_free_display(start=90, end=200) -> int:
    """비어 있는 DISPLAY 번호 탐색"""
    for d in range(start, end):
        if not _is_display_in_use(d):
            # 락파일이 남아있는 좀비 케이스도 있으니, 실제로 붙어지는지 소켓 대기에서 확인
            return d
    raise RuntimeError("No free Xvfb display available")

def _wait_for_x_socket(display_num: int, timeout=5.0):
    """Xvfb 소켓이 열릴 때까지 대기"""
    sock_path = f"{X11_SOCK_DIR}/X{display_num}"
    start = time.time()
    while time.time() - start < timeout:
        if Path(sock_path).exists():
            return True
        time.sleep(0.05)
    return False

@contextmanager
def xvfb_display(width=1600, height=2400, depth=24, display_num=None):
    """
    프로세스/스레드 로컬로 Xvfb를 띄우고 DISPLAY 환경변수를 설정.
    종료 시 자동으로 프로세스 정리.
    """
    need_kill = False
    proc = None
    old_display = os.environ.get("DISPLAY")
    try:
        if display_num is None:
            display_num = _find_free_display()

        cmd = [
            XVFB_BIN, f":{display_num}",
            "-screen", "0", f"{width}x{height}x{depth}",
            "-nolisten", "tcp",
            "-ac",  # 접근 제어 끔(로컬 전용이면 문제 없음)
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        need_kill = True

        if not _wait_for_x_socket(display_num, timeout=6.0):
            raise RuntimeError(f"Xvfb failed to start on :{display_num}")

        # 현재 프로세스에 DISPLAY 지정
        os.environ["DISPLAY"] = f":{display_num}"

        # 혹시 프로세스가 죽어도 정리되도록
        def _cleanup():
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=2)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass
        atexit.register(_cleanup)

        yield f":{display_num}"

    finally:
        if old_display is not None:
            os.environ["DISPLAY"] = old_display
        else:
            os.environ.pop("DISPLAY", None)

        if need_kill and proc and proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=2)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass