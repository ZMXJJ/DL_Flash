import requests
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from tqdm import tqdm
import logging
import argparse

# =================== Configurable Settings ===================
# List of User-Agent strings to simulate different browsers/clients
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
]

# List of Referer headers to simulate coming from different search engines or sites
REFERERS = [
    "https://www.google.com/   ",  # Simulate coming from Google search
    "https://www.bing.com/   ",    # Simulate coming from Bing search
    "https://www.yahoo.com/   ",   # Simulate coming from Yahoo search
    ""                            # No referer
]

# List of proxy servers (format: 'http://user:pass@ip:port' or 'http://ip:port')
# Proxies can be used to distribute requests or bypass restrictions
PROXIES = [
    # "http://192.168.1.100:8080", # Example proxy, currently disabled
]

# File path for logging events and errors
LOG_FILE = "stress_test.log"
# Size of data chunks to read/write at a time during download (1MB)
CHUNK_SIZE = 1024 * 1024  

# ================ Global Variables ================
# Tracks the cumulative amount of data downloaded across all threads
total_downloaded = 0
# A lock to ensure safe modification of shared variables (total_downloaded, pbar) by multiple threads
lock = threading.Lock()
# Flag to signal all threads to stop downloading once the target size is reached
stop_flag = False
# Variable to hold the tqdm progress bar object for updates
pbar = None  

# ================ Logging Configuration ================
# Configure the logging module to write to LOG_FILE with INFO level and a specific format
logging.basicConfig(
    filename=LOG_FILE,          # Log file path
    level=logging.INFO,         # Minimum level of messages to log (INFO and above)
    format='%(asctime)s - %(levelname)s - %(message)s' # Log message format
)

# ================ Core Functions ================
def get_random_headers():
    """
    Generates a dictionary of HTTP headers with randomly selected User-Agent and Referer.
    This helps to make requests appear more like they come from real browsers.
    """
    return {
        "User-Agent": random.choice(USER_AGENTS), # Randomly pick a User-Agent
        "Referer": random.choice(REFERERS)       # Randomly pick a Referer
    }

def get_proxy(enable_proxy):
    """
    Returns a dictionary containing proxy settings if proxies are enabled and available.
    Otherwise, returns None.
    
    Args:
        enable_proxy (bool): Flag indicating whether to use a proxy.
        
    Returns:
        dict or None: Proxy dictionary for requests or None.
    """
    if enable_proxy and PROXIES: # Check if proxy usage is enabled and proxy list is not empty
        proxy = random.choice(PROXIES) # Randomly select a proxy from the list
        # Return a dictionary suitable for the 'proxies' parameter in requests.get()
        # Handles both http and https requests with the same proxy
        return {"http": proxy, "https": proxy} 
    return None # Return None if no proxy should be used

def download_video(url, enable_proxy, chunk_size=CHUNK_SIZE):
    """
    Downloads video data from a given URL in chunks, updating global download stats.
    Runs within a thread.
    
    Args:
        url (str): The URL of the video resource to download.
        enable_proxy (bool): Whether to use a proxy for this request.
        chunk_size (int): The size of data chunks to read at a time.
    """
    # Access global variables to update download progress and control
    global total_downloaded, stop_flag, pbar
    
    # Get randomized headers for the request
    headers = get_random_headers()
    # Get proxy settings for the request
    proxy = get_proxy(enable_proxy)

    try:
        # Make a GET request with streaming enabled to download large files efficiently
        # 'stream=True' prevents loading the entire response into memory at once
        with requests.get(url, stream=True, headers=headers, proxies=proxy, timeout=10) as r:
            # Check if the request was successful (status code 200)
            if r.status_code != 200:
                # Log a warning if the status code indicates an error
                logging.warning(f"[Error] Status code {r.status_code} for {url}")
                print(f"[Error] Status code {r.status_code}") # Also print to console
                return # Exit the function if the request failed

            # Initialize a counter for data downloaded by this specific thread
            downloaded = 0
            
            # Iterate over the response data in chunks
            for chunk in r.iter_content(chunk_size=chunk_size):
                # Check if the chunk is not None (can happen if connection drops)
                if chunk is not None:
                    # Calculate the size of the current chunk
                    chunk_len = len(chunk)
                    # Add the chunk size to this thread's counter
                    downloaded += chunk_len
                    
                    # Acquire the lock before modifying shared variables
                    with lock:
                        # Add the chunk size to the global total downloaded bytes
                        total_downloaded += chunk_len
                        
                        # Update the progress bar if it exists
                        if pbar:
                            pbar.update(chunk_len) 
                            
                        # Check if the global download target has been reached
                        # If so, set the stop flag for all threads
                        if total_downloaded >= target_total_bytes:
                            stop_flag = True
                            
                # Check the stop flag inside the loop to potentially exit early
                if stop_flag:
                    break # Break the loop if stop flag is set
                    
            # Log the amount of data downloaded by this thread upon completion or exit
            logging.info(f"[Thread] Downloaded {downloaded / (1024 * 1024):.2f} MB")
            
    # Catch any exceptions that occur during the request or download process
    except Exception as e:
        # Log the full exception details including traceback
        logging.error(f"[Exception] {e}", exc_info=True)
        print(f"[Exception] {e}") # Also print the error to console

def stress_test(url, threads=1, target_total_mb=1024, enable_proxy=False):
    """
    Orchestrates the stress test by managing threads and overall download progress.
    
    Args:
        url (str): The URL of the video resource to download.
        threads (int): The number of concurrent threads to use.
        target_total_mb (int): The total amount of data to download (in MB) before stopping.
        enable_proxy (bool): Whether to enable proxy usage for requests.
    """
    # Access global variables to reset state for a new test
    global total_downloaded, stop_flag, pbar
    
    # Reset the stop flag and total downloaded counter before starting
    stop_flag = False
    total_downloaded = 0

    # Calculate the target download size in bytes from MB
    global target_total_bytes
    target_total_bytes = target_total_mb * 1024 * 1024

    # Print initial test configuration to the console
    print(f"🚀 Starting stress test on URL: {url}")
    print(f"🧵 Threads: {threads}, 📦 Target Total: {target_total_mb} MB")
    print(f"🔌 Use Proxy: {'Yes' if enable_proxy else 'No'}")
    # Log the start of the test with its parameters
    logging.info(f"Starting stress test on {url}, Threads={threads}, Target={target_total_mb} MB, Use Proxy={enable_proxy}")

    # Create a tqdm progress bar to visualize download progress
    # 'total' is the target size in bytes, 'unit' and 'unit_scale' make it human-readable (e.g., KB, MB)
    # 'desc' sets the label for the progress bar
    with tqdm(total=target_total_bytes, unit='B', unit_scale=True, desc="Progress") as pbar:
        # Assign the created progress bar to the global variable so threads can update it
        # Note: This assignment is within the 'with' block's scope, which is acceptable here
        # because the threads that use it are also launched within this scope.
        globals()['pbar'] = pbar 
        
        # Create a ThreadPoolExecutor to manage the specified number of worker threads
        with ThreadPoolExecutor(max_workers=threads) as executor:
            # List to hold Future objects representing the running tasks
            futures = []
            
            # Main loop to keep submitting download tasks until the target is met or stop is requested
            while not stop_flag: # Continue looping while the stop flag is False
                # Double-check if the target has been reached inside the loop condition
                if total_downloaded >= target_total_bytes:
                    break # Exit the loop if target is reached
                
                # Submit a new download task to the thread pool
                # This schedules the 'download_video' function to run with the given arguments
                future = executor.submit(download_video, url, enable_proxy)
                # Add the Future object to the list to track its status later
                futures.append(future)
                
                # Brief pause before submitting the next task to avoid overwhelming the system/start
                time.sleep(0.1) 

            # Wait for all submitted tasks (futures) to complete, even if the target was reached
            # This ensures all threads finish their current download attempts gracefully
            # The results are not used, so we just iterate through the completed futures
            for future in as_completed(futures):
                pass # 'pass' does nothing, just iterates to completion

    # Print the final total amount of data downloaded to the console
    print(f"✅ Total downloaded: {total_downloaded / (1024 * 1024):.2f} MB")
    # Log the final total amount of data downloaded
    logging.info(f"Total downloaded: {total_downloaded / (1024 * 1024):.2f} MB")
    # Print a message indicating the stress test has finished
    print("🏁 Stress test completed.")

# ================ Main Program Entry Point ================
# This block runs only if the script is executed directly (not imported as a module)
if __name__ == "__main__":
    # Create an ArgumentParser object to handle command-line arguments
    parser = argparse.ArgumentParser(description="Stress test video resource downloader.")
    
    # Add required and optional command-line arguments
    # --url: The video URL to test (required)
    parser.add_argument("--url", required=True, help="Video URL to stress test.")
    # --threads: Number of concurrent threads (optional, defaults to 1)
    parser.add_argument("--threads", type=int, default=1, help="Number of concurrent threads.")
    # --total-mb: Total download target size in MB (optional, defaults to 1024)
    parser.add_argument("--total-mb", type=int, default=1024, help="Total download size in MB.")
    # --use-proxy: Flag to enable proxy usage (optional, action='store_true' means it sets the value to True if present)
    parser.add_argument("--use-proxy", action="store_true", help="Enable using proxy servers.")

    # Parse the command-line arguments provided by the user
    args = parser.parse_args()

    # Call the main stress_test function with the parsed arguments
    stress_test(args.url, args.threads, args.total_mb, args.use_proxy)
