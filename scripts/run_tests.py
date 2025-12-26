#!/usr/bin/env python3
"""
Test runner script with options for different test types
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd):
    """Run command and return exit code"""
    result = subprocess.run(cmd, shell=True, capture_output=False)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Run tests for FastApp")
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "auth", "device", "jwt", "migration", "db", "all"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run tests with coverage"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--file",
        help="Run specific test file"
    )
    
    args = parser.parse_args()
    
    # Base command
    cmd = ["uv", "run", "pytest"]
    
    # Add verbosity
    if args.verbose:
        cmd.append("-vv")
    
    # Add coverage if requested
    if args.coverage:
        cmd.extend([
            "--cov=core",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-fail-under=80"
        ])
    
    # Add specific test type or file
    if args.file:
        cmd.append(args.file)
    elif args.type != "all":
        cmd.append(f"-m {args.type}")
    
    # Add test directory
    cmd.append("tests/")
    
    # Run tests
    print(f"Running: {' '.join(cmd)}")
    exit_code = run_command(' '.join(cmd))
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
        
        if args.coverage:
            print("\n📊 Coverage report generated in htmlcov/")
    else:
        print(f"\n❌ Tests failed with exit code {exit_code}")
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
