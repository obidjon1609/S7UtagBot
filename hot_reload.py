import os
import subprocess
import sys
import time
import hashlib


def get_file_hash(filepath):
    try:
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return None


def main():
    script_path = os.path.join(os.path.dirname(__file__), "pro.tag.10.py")
    
    if not os.path.exists(script_path):
        print(script_path + " fayli topilmadi!")
        return

    process = None
    last_hash = get_file_hash(script_path)

    print("Hot reload rejimi faol. " + script_path + " kuzatilmoqda...")
    print("Fayl o'zgarganda bot avtomatik qayta ishga tushadi.")
    print("To'xtatish uchun Ctrl+C bosing.")
    sys.stdout.flush()

    def start_bot():
        nonlocal process
        if process:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass
        
        print("Bot ishga tushirilmoqda: " + script_path)
        sys.stdout.flush()
        process = subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            encoding='utf-8',
            errors='ignore'
        )

    start_bot()

    try:
        while True:
            time.sleep(2)
            
            current_hash = get_file_hash(script_path)
            if current_hash and current_hash != last_hash:
                print(script_path + " o'zgardi. Qayta ishga tushirilmoqda...")
                sys.stdout.flush()
                last_hash = current_hash
                start_bot()
            
            # Bot loglarini chiqarish
            if process:
                try:
                    line = process.stdout.readline()
                    if line:
                        print(line.strip())
                        sys.stdout.flush()
                except:
                    pass
                    
    except KeyboardInterrupt:
        print("\nHot reload to'xtatildi.")
        sys.stdout.flush()
        if process:
            process.terminate()


if __name__ == "__main__":
    main()