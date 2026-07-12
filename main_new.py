import sys
from texttests.script_runner import run_script


def main():
    text = sys.stdin.read().strip()
    if not text:
        return

    results = run_script(text)

    all_passed = True
    for i, (actual, expected) in enumerate(results, 1):
        if actual == expected:
            print(f"print board {i}: PASS")
        else:
            all_passed = False
            print(f"print board {i}: FAIL")
            print(f"  expected: {expected}")
            print(f"  actual:   {actual}")

    if not results:
        print("No print board commands found.")


if __name__ == "__main__":
    main()
