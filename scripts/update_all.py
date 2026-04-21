import subprocess
import sys

SCRIPTS = [
    "scripts/pull_zillow.py",
    "scripts/clean_zillow.py",
    "scripts/pull_fred.py",
    "scripts/clean_fred.py",
    "scripts/merge_data.py",
    "scripts/calculate_affordability.py",
    "scripts/export_dashboard.py"
]

def run_script(script):
    print(f"\nRunning {script}...")
    result = subprocess.run([sys.executable, script], check=True)
    return result

def main():
    for script in SCRIPTS:
        run_script(script)

    print("\nAll pipeline steps completed successfully.")

if __name__ == "__main__":
    main()