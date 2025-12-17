#!/usr/bin/env python3
import subprocess
import sys

def run(cmd):
    print(f">>> {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        sys.exit(result.returncode)

def main():
    run(["docker", "compose", "down"])
    run(["docker", "compose", "up", "-d", "--build"])

if __name__ == "__main__":
    main()

