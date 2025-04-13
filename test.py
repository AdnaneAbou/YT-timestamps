from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class Handler(FileSystemEventHandler):
    def on_created(self, event):
        print(f"New file: {event.src_path}")

observer = Observer()
observer.schedule(Handler(), path="C:/", recursive=True)
observer.start()
try:
    while True: pass
except KeyboardInterrupt:
    observer.stop()
observer.join()