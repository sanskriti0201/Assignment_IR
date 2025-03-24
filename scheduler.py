import time
import subprocess
import logging

# Configure logging
logging.basicConfig(filename="scheduler.log", level=logging.INFO, format="%(asctime)s - %(message)s")

def run_crawler():
    logging.info("Running crawler...")
    try:
        subprocess.run(["python", "crawler.py"], check=True)
        logging.info("Crawler completed successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Crawler failed with error: {e}")

def schedule_crawler(interval=2592000):  # 30 days in seconds
    while True:
        run_crawler()
        logging.info(f"Waiting for {interval // 86400} days before the next run...")
        time.sleep(interval)

if __name__ == "__main__":
    schedule_crawler()
