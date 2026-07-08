import subprocess
import json
import os
import re
from datetime import date

ROOT = os.path.join(os.path.dirname(__file__), '..')
HTML_FILE = os.path.join(os.path.dirname(__file__), 'test_progress.html')
RESULTS_FILE = os.path.join(os.path.dirname(__file__), 'test_results.json')

result = subprocess.run(
    ['py', '-m', 'pytest', 'tests/', '-v', '--tb=no', '-q'],
    capture_output=True, text=True, cwd=ROOT
)

passed = failed = 0
for line in result.stdout.splitlines():
    if ' passed' in line:
        for part in line.split():
            if part.isdigit():
                passed = int(part)
                break
    if ' failed' in line:
        for part in line.split():
            if part.isdigit():
                failed = int(part)
                break

data = []
if os.path.exists(RESULTS_FILE):
    with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

data.append({'date': str(date.today()), 'passed': passed, 'failed': failed, 'note': ''})

with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# inject data into HTML
with open(HTML_FILE, 'r', encoding='utf-8') as f:
    html = f.read()

html = re.sub(
    r'(<script id="injected-data" type="application/json">).*?(</script>)',
    r'\g<1>' + json.dumps(data, ensure_ascii=False) + r'\2',
    html, flags=re.DOTALL
)

with open(HTML_FILE, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"{passed} passed, {failed} failed -> updated test_progress.html")
