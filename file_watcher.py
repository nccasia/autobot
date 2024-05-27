import sys
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, service_to_restart):
        self.service_to_restart = service_to_restart

    def on_any_event(self, event):
        if event.is_directory:
            return None
        elif (
            event.event_type == "created"
            or event.event_type == "deleted"
        ):
            logging.info(f"Received event - {event.event_type} on {event.src_path}")
            self.restart_service()

    def restart_service(self):
        logging.info(f"Restarting service: {self.service_to_restart}")
        command = f"sudo systemctl restart {self.service_to_restart}"
        os.system(command)
        logging.info("Service restarted successfully")


if __name__ == "__main__":
    directory_to_watch = "data"
    service_to_restart = sys.argv[1] if len(sys.argv) > 1 else None

    event_handler = FileChangeHandler(service_to_restart)
    observer = Observer()
    observer.schedule(event_handler, path=directory_to_watch, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
