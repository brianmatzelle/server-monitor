import threading
import time
import requests
import itertools
import random
from datetime import datetime

def random_pastel_color():
    """
    Returns an ANSI escape code for a random pastel-ish 24-bit (True Color) foreground.
    We'll pick each R, G, B in [180..255], which tends to look soft/pastel.
    """
    r = random.randint(180, 255)
    g = random.randint(180, 255)
    b = random.randint(180, 255)
    return f"\033[38;2;{r};{g};{b}m"

class ServerMonitor:
    def __init__(self, api_url):
        self.api_url = api_url
        self.server_is_up = True
        self.server_status_lock = threading.Lock()
        self.stop_spinner = threading.Event()

        self.last_ping_time = None
        self.time_since_last_ping = 0.0  # seconds elapsed since last ping

        self.spinner_chars = ["┌─", "└─", "└┐", "┌┘"]
        self.spinner_iterators = [itertools.cycle(self.spinner_chars) for _ in range(10)]

        # Generate one random pastel color per spinner slot
        self.spinner_colors = [random_pastel_color() for _ in range(10)]

    def is_server_up(self):
        try:
            response = requests.get(self.api_url, timeout=10)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def send_notification(self):
        print("Sending notification...")

    def spinner(self):
        """
        Runs continuously. Every 0.3s:
          - Update time_since_last_ping
          - Figure out how many 30s chunks have elapsed
          - Print that many rotating spinners, some fully replaced by their index
          - The rest remain hidden
        """
        spinner_refresh = 0.3
        while not self.stop_spinner.is_set():
            time.sleep(spinner_refresh)
            with self.server_status_lock:
                self.time_since_last_ping += spinner_refresh

                # Calculate how many 30-s chunks we've crossed
                chunk_count = int(self.time_since_last_ping // 30.0)
                if chunk_count > 10:
                    chunk_count = 10

                spinners_to_show = []
                for i in range(chunk_count):
                    # Get the next symbol for spinner i
                    spinner_symbol = next(self.spinner_iterators[i])

                    # ~30% chance to replace spinner symbol with its index
                    if random.random() < 0.3:
                        spinner_symbol = f" {str(i)} "

                    # Wrap with the spinner's pastel color
                    colored_symbol = f"{random_pastel_color()}{spinner_symbol}\033[0m"
                    
                    # Add a bit of random spacing
                    colored_symbol += " " * random.randint(0, 1)
                    spinners_to_show.append(colored_symbol)

                # status (OK / DOWN)
                if self.server_is_up:
                    color = "\033[92m"  # green
                    status_text = "OK"
                else:
                    color = "\033[91m"  # red
                    status_text = "DOWN"

                # Show last ping time or "N/A" if none yet
                ping_time_str = (self.last_ping_time.strftime('%Y-%m-%d %H:%M:%S')
                                 if self.last_ping_time else "N/A")

                loading_bar = "".join(spinners_to_show)

                # Overwrite the same line with carriage return
                print(f"\r[{ping_time_str}] {color}{status_text}\033[0m {loading_bar}",
                      end='', flush=True)

    def run(self):
        # Immediate ping so we don't start with [N/A]
        initial_status = self.is_server_up()
        self.last_ping_time = datetime.now()
        self.server_is_up = initial_status

        spinner_thread = threading.Thread(target=self.spinner, daemon=True)
        spinner_thread.start()

        try:
            while True:
                time.sleep(1)
                with self.server_status_lock:
                    # If we've accumulated 300s (>= 10 chunks * 30s), do a ping
                    if self.time_since_last_ping >= 300.0:
                        status = self.is_server_up()
                        self.last_ping_time = datetime.now()

                        was_up = self.server_is_up
                        self.server_is_up = status

                        # Print a newline so the next message starts fresh
                        print()

                        # If server just went down
                        if was_up and not status:
                            print("[!] Server just went DOWN, sending notification...")
                            self.send_notification()

                        self.time_since_last_ping = 0.0

                        # Reset each spinner iterator so the next bar starts fresh
                        for i in range(10):
                            self.spinner_iterators[i] = itertools.cycle(self.spinner_chars)

        except KeyboardInterrupt:
            print("\nCaught Ctrl+C, shutting down...")
        finally:
            self.stop_spinner.set()
            spinner_thread.join()
            print("Exiting.")

if __name__ == "__main__":
    monitor = ServerMonitor(api_url="https://api.spacebots.io:8443/ping")
    monitor.run()

