import subprocess
import sys

# Run pytest
result = subprocess.run([sys.executable, "-m", "pytest", "tests/test_health.py", "-v"], 
                       capture_output=True, text=True)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)
