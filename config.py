import os
from dotenv import load_dotenv

load_dotenv()

# discord setup
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))
STATUS_CHANNEL_ID = int(os.getenv('STATUS_CHANNEL_ID'))
# parse comma-separated user IDs from env
ping_users_str = os.getenv('PING_USERS', '')
PING_USERS = [int(uid.strip()) for uid in ping_users_str.split(',') if uid.strip()]

# where to store data
RESULTS_FILE = "floor_plans.json"
MARKDOWN_FILE = "floor_plans.md"

# site config
TARGET_URL = os.getenv('TARGET_URL')
TARGET_XPATH = os.getenv('TARGET_XPATH')
PAGE_LOAD_TIMEOUT = 3
WEBDRIVER_WAIT_TIMEOUT = 15
WINDOW_SIZE = "1920,1080"

# scraper setup
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

# basic anti detection options
CHROME_OPTIONS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-blink-features=AutomationControlled",
    "--headless"
]

CHROME_EXPERIMENTAL_OPTIONS = {
    "excludeSwitches": ["enable-automation"],
    "useAutomationExtension": False
}
