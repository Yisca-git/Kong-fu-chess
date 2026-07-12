import os
import pytest
from texttests.script_runner import run_script

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "scripts")


def _load_scripts():
    scripts = []
    for filename in sorted(os.listdir(SCRIPTS_DIR)):
        if filename.endswith(".kfc"):
            path = os.path.join(SCRIPTS_DIR, filename)
            scripts.append((filename, open(path).read()))
    return scripts


@pytest.mark.parametrize("filename,text", _load_scripts())
def test_script(filename, text):
    results = run_script(text)
    for actual, expected in results:
        assert actual == expected, (
            f"\n--- {filename} ---\nExpected:\n" + "\n".join(expected) +
            "\nActual:\n" + "\n".join(actual)
        )
