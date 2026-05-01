#!/usr/bin/env python3

# Sets up a Python virtual environment, installs dependencies, and runs the downloader.
import subprocess
import sys
import os

pip_executable = os.path.join('myenv', 'bin', 'pip')
python_executable = os.path.join('myenv', 'bin', 'python')
playwright_executable = os.path.join('myenv', 'bin', 'playwright')

subprocess.run([sys.executable, '-m', 'venv', 'myenv'])
subprocess.run([pip_executable, 'install', 'playwright', 'pyyaml'])
subprocess.run([playwright_executable, 'install', 'chromium'])
subprocess.run([python_executable, './download.py'])
