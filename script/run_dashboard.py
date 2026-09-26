"""Script khoi chay Streamlit Observability & Drift Dashboard (Hạng mục Bonus B1)."""
from pathlib import Path
import subprocess
import sys


def main():
    root = Path(__file__).resolve().parents[1]
    app_path = root / "src" / "web" / "dashboard.py"
    if not app_path.exists():
        print(f"Khong tim thay dashboard tai {app_path}")
        sys.exit(1)

    print("====================================================================")
    print(" 🛡️  KHOI DONG RAG OBSERVABILITY & DRIFT DASHBOARD (BONUS B1)")
    print("====================================================================")
    print(f" Ung dung: {app_path}")
    print(" Dashboard dang khoi dong tren: http://localhost:8501")
    print(" Nhan Ctrl+C de dung server.")
    print("====================================================================")

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.port=8501",
        "--server.headless=true",
        "--theme.base=light",
    ]
    try:
        subprocess.run(cmd, cwd=str(root))
    except KeyboardInterrupt:
        print("\nDa dung Dashboard.")


if __name__ == "__main__":
    main()
