import platform
import sys
from app.runtime import version_text

def run_health_check():
    return {
        "application": version_text(),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "architecture": platform.machine(),
    }

if __name__ == "__main__":
    for key, value in run_health_check().items():
        print(f"{key}: {value}")
