import requests
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from tqdm import tqdm
import logging
import argparse


# =================== 可配置项 ===================
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
]

REFERERS = [
    "https://www.google.com/ ",
    "https://www.bing.com/ ",
    "https://www.yahoo.com/ ",
    ""
]

# 示例格式：'http://user:pass@ip:port'
PROXIES = [
    # "http://192.168.1.100:8080",
]

LOG_FILE = "stress_test.log"
CHUNK_SIZE = 1024 * 1024  # 每次读取 1MB

# ================ 全局变量 ================
total_downloaded = 0
lock = threading.Lock()
stop_flag = False
pbar = None  # tqdm 进度条对象

# ================ 日志设置 ================
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ================ 核心函数 ================
def get_random_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Referer": random.choice(REFERERS)
    }

def get_proxy(enable_proxy):
    if enable_proxy and PROXIES:
        proxy = random.choice(PROXIES)
        return {"http": proxy, "https": proxy}
    return None

def download_video(url, enable_proxy, chunk_size=CHUNK_SIZE):
    global total_downloaded, stop_flag, pbar
    headers = get_random_headers()
    proxy = get_proxy(enable_proxy)

    try:
        with requests.get(url, stream=True, headers=headers, proxies=proxy, timeout=10) as r:
            if r.status_code != 200:
                logging.warning(f"[Error] Status code {r.status_code} for {url}")
                print(f"[Error] Status code {r.status_code}")
                return

            downloaded = 0
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk is not None:
                    downloaded += len(chunk)
                    with lock:
                        total_downloaded += len(chunk)
                        if pbar:
                            pbar.update(len(chunk))
                        if total_downloaded >= target_total_bytes:
                            stop_flag = True
                if stop_flag:
                    break
            logging.info(f"[Thread] Downloaded {downloaded / (1024 * 1024):.2f} MB")
    except Exception as e:
        logging.error(f"[Exception] {e}", exc_info=True)
        print(f"[Exception] {e}")

def stress_test(url, threads=1, target_total_mb=1024, enable_proxy=False):
    global total_downloaded, stop_flag, pbar
    stop_flag = False
    total_downloaded = 0

    global target_total_bytes
    target_total_bytes = target_total_mb * 1024 * 1024

    print(f"🚀 Starting stress test on URL: {url}")
    print(f"🧵 Threads: {threads}, 📦 Target Total: {target_total_mb} MB")
    print(f"🔌 Use Proxy: {'Yes' if enable_proxy else 'No'}")
    logging.info(f"Starting stress test on {url}, Threads={threads}, Target={target_total_mb} MB, Use Proxy={enable_proxy}")

    with tqdm(total=target_total_bytes, unit='B', unit_scale=True, desc="Progress") as pbar:
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = []
            while not stop_flag:
                if total_downloaded >= target_total_bytes:
                    break
                future = executor.submit(download_video, url, enable_proxy)
                futures.append(future)
                time.sleep(0.1)

            for future in as_completed(futures):
                pass

    print(f"✅ Total downloaded: {total_downloaded / (1024 * 1024):.2f} MB")
    logging.info(f"Total downloaded: {total_downloaded / (1024 * 1024):.2f} MB")
    print("🏁 Stress test completed.")

# ================ 主程序入口 ================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stress test video resource downloader.")
    parser.add_argument("--url", required=True, help="Video URL to stress test.")
    parser.add_argument("--threads", type=int, default=1, help="Number of concurrent threads.")
    parser.add_argument("--total-mb", type=int, default=1024, help="Total download size in MB.")
    parser.add_argument("--use-proxy", action="store_true", help="Enable using proxy servers.")

    args = parser.parse_args()

    stress_test(args.url, args.threads, args.total_mb, args.use_proxy)