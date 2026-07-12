import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from texttests.script_runner import run_script

def main():
    text = sys.stdin.read().strip()
    if not text:
        return
    for actual, _ in run_script(text):
        print("\n".join(actual))

if __name__ == "__main__":
    main()
