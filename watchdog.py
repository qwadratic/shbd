import subprocess
import time

def check_webhook():
    # Check if webhook screen session exists
    result = subprocess.run(['screen', '-ls'], capture_output=True, text=True)
    
    # Check if 'wh' session is running
    if 'wh' not in result.stdout:
        print("Webhook not running, starting it...")
        # Start webhook in a new screen session
        subprocess.run(['screen', '-S', 'wh', '-dm', 'python', 'webhook.py'])
        print("Webhook started")
    else:
        print("Webhook is running")

if __name__ == "__main__":
    while True:
        check_webhook()
        # Check every 60 seconds
        time.sleep(60)
