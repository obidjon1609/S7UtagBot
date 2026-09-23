#!/usr/bin/env python3
"""
PythonAnywhere uchun Telegram bot setup script
"""

import os
import sys
import subprocess

def main():
    print("PythonAnywhere uchun Telegram bot setup")
    
    # Virtual environment yaratish
    venv_path = os.path.expanduser("~/myenv")
    if not os.path.exists(venv_path):
        print(f"Virtual environment yaratilmoqda: {venv_path}")
        subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)
    
    # Dependencies o'rnatish
    print("Dependencies o'rnatilmoqda...")
    pip_path = os.path.join(venv_path, "bin", "pip")
    requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    subprocess.run([pip_path, "install", "-r", requirements_path], check=True)
    
    print("Setup tugadi!")
    print(f"Botni ishga tushirish uchun: {venv_path}/bin/python pro.tag.10.py")

if __name__ == "__main__":
    main()
