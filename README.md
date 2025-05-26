# DL_Flash - Video Resource Stress Testing Tool

## Project Introduction
DL_Flash is a Python tool for stress testing video resources. It can simulate multi-threaded downloads to test the performance of servers under high concurrent download requests.

## Main Features
- Multi-threaded concurrent download testing
- Support for proxy servers
- Random User-Agent and Referer to simulate real requests
- Configurable target download volume
- Real-time progress display

## Installation Requirements
```bash
pip install requests tqdm
```

## Usage
```bash
python main.py --url <video_url> --threads <number_of_threads> --total-mb <total_download_size_in_MB> [--use-proxy]
```

### Parameters Description
- `--url`: URL of the video resource to be tested
- `--threads`: Number of concurrent threads (default: 1)
- `--total-mb`: Total download target in MB (default: 1024 MB)
- `--use-proxy`: Enable proxy server (optional)

## Configuration Options
At the top of the main.py file, you can find the following configurable items:
- USER_AGENTS: List of supported user agents
- REFERERS: List of reference source addresses
- PROXIES: List of proxy servers
- LOG_FILE: Log file path

## Log Recording
All operation logs will be recorded in the specified log file, default is stress_test.log

## Notes
- Please ensure compliance with the terms of service of the target server and relevant laws and regulations
- Do not abuse this tool in production environments
- Modify the proxy server list to use your own proxy services