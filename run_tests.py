"""
Test runner script for Discord bot.

Usage:
    python run_tests.py                  # Run all tests
    python run_tests.py --verbose        # Verbose output
    python run_tests.py --coverage       # With coverage report
    python run_tests.py --quick          # Run only fast tests
"""

import subprocess
import sys
import argparse


def run_tests(verbose=False, coverage=False, quick=False):
    """Run the test suite."""
    cmd = [sys.executable, "-m", "pytest", "tests/"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=core", "--cov-report=term-missing"])
        print("📊 Running tests with coverage report...\n")
    else:
        if not verbose:
            # Default to minimal output
            cmd.append("-q")
    
    if quick:
        cmd.extend(["-m", "not slow"])
        print("⚡ Running fast tests only...\n")
    
    print(f"Command: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Run Discord bot tests")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-c", "--coverage", action="store_true", help="Include coverage report")
    parser.add_argument("-q", "--quick", action="store_true", help="Skip slow tests")
    
    args = parser.parse_args()
    
    try:
        exit_code = run_tests(
            verbose=args.verbose,
            coverage=args.coverage,
            quick=args.quick
        )
        sys.exit(exit_code)
    except FileNotFoundError:
        print("❌ pytest is not installed. Install with:")
        print("   pip install pytest")
        if args.coverage:
            print("   pip install pytest-cov")
        sys.exit(1)


if __name__ == "__main__":
    main()
