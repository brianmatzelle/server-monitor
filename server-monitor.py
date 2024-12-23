import os
import time
import requests
from datetime import datetime
import sys
import itertools
import random

# make sure these environment variables are set 
PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")
PUSHOVER_USER = os.getenv("PUSHOVER_USER")

if not PUSHOVER_TOKEN or not PUSHOVER_USER:
    sys.stderr.write("Error: Environment variables PUSHOVER_TOKEN and PUSHOVER_USER are not set.\n")
    sys.exit(1)

API_URL = 'https://api.spacebots.io:8443/ping'
CHECK_INTERVAL = 300  # in seconds

# ANSI escape codes for colors
RED = '\033[91m'
GREEN = '\033[92m'
RESET = '\033[0m'

#spinner_chars = itertools.cycle("|/-\\")  # Our mini-pipes spinner
spinner_chars = itertools.cycle(["┌─", "└─", "└┐", "┌┘"])

def is_server_up():
    try:
        response = requests.get(API_URL, timeout=10)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def send_notification():
    message = f'Server {API_URL} is down!'
    requests.post('https://api.pushover.net/1/messages.json', data={
        'token': PUSHOVER_TOKEN,
        'user': PUSHOVER_USER,
        'message': message
    })

while True:
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if not is_server_up():
        print(f"[{current_time}] {RED}The server is down!{RESET}")
        send_notification()
    else:
        # Grab the next spinner character
        spin = next(spinner_chars)
        #spin = random_emoji()
        # Print a single line log entry that’s a bit more fun than "OK"
        print(f"[{current_time}] {GREEN}OK {spin}{RESET}")
    time.sleep(CHECK_INTERVAL)


def random_emoji():
    return random.choice(["🚀", "🌟", "💫", "🪐", "🌖", "👾"])
