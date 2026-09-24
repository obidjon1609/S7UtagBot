#!/usr/bin/env python3
"""
Hot reload skripti - kod o'zgarganda avtomatik restart
"""
import os
import subprocess
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, bot_process):
        self.bot_process = bot_process
        self.last_restart = time.time()
    
    def on_modified(self, event):
        if event.src_path.endswith('.py') and time.time() - self.last_restart > 2:
            print(f"🔄 {event.src_path} o'zgardi, botni restart qilmoqda...")
            self.restart_bot()
            self.last_restart = time.time()
    
    def restart_bot(self):
        if self.bot_process:
            self.bot_process.terminate()
            self.bot_process.wait()
        
        print("🚀 Botni qayta ishga tushirish...")
        self.bot_process = subprocess.Popen([os.path.join('.venv', 'Scripts', 'python'), 'pro.tag.10.py'])

def main():
    print("🔥 Hot reload modda ishga tushdi - kod o'zgarganda avtomatik restart")
    
    # Botni boshlash
    bot_process = subprocess.Popen([os.path.join('.venv', 'Scripts', 'python'), 'pro.tag.10.py'])
    
    # File change observer
    event_handler = FileChangeHandler(bot_process)
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Hot reload to'xtatildi")
        observer.stop()
        if bot_process:
            bot_process.terminate()
            bot_process.wait()
    
    observer.join()

if __name__ == "__main__":
    main()
