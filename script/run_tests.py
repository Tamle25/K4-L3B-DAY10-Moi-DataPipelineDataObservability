import os
from pathlib import Path
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def main():
    root = Path(__file__).resolve().parents[1]
    src_dir = root / "src"
    
    # Uu tien su dung Python trong virtualenv neu co
    venv_py = root / ".venv" / "Scripts" / "python.exe"
    executable = str(venv_py) if venv_py.exists() else sys.executable

    print("====================================================================")
    print(" [TEST SUITE] THUC THI AUTOMATED PYTEST SUITE & COVERAGE (BONUS B3)")
    print("====================================================================")
    print(f" Thu muc du an : {root}")
    print(f" Python binary : {executable}")
    print(" Chay pytest voi coverage report tren source module...")
    print("====================================================================")

    env = os.environ.copy()
    current_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{src_dir}{os.pathsep}{current_pythonpath}" if current_pythonpath else str(src_dir)

    cmd = [
        executable,
        "-m",
        "pytest",
        "tests",
        "-v",
        "--tb=short",
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-report=html:data/reports/coverage_html",
    ]

    result = subprocess.run(cmd, cwd=str(root), env=env)
    if result.returncode == 0:
        print("\n====================================================================")
        print(" [SUCCESS] TAT CA CAC TESTS DEU PASS XUAT SAC!")
        print("    Bao cao HTML da duoc luu tai: data/reports/coverage_html/index.html")
        print("====================================================================")
    else:
        print("\n[FAILED] Co loi trong qua trinh kiem thu.")
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
