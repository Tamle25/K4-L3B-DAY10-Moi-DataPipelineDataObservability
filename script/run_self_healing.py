"""Script khoi chay Automated Self-Healing Pipeline (Hang muc Bonus B2)."""
import sys
from pathlib import Path

# Them src vao sys.path
root = Path(__file__).resolve().parents[1]
src = root / "src"
if str(src) not in sys.path:
    sys.path.insert(0, str(src))

from core.config import load_settings
from pipelines.self_healing import run_self_healing_pipeline


def main():
    settings = load_settings()
    run_self_healing_pipeline(settings)


if __name__ == "__main__":
    main()
