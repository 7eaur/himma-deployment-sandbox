import os
import time

def main():
    print("Worker starting...", flush=True)
    # Simple loop for now
    while True:
        time.sleep(10)
        print("Worker heartbeat", flush=True)

if __name__ == "__main__":
    main()
