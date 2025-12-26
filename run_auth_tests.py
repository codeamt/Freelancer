#!/usr/bin/env python
"""Script to run auth-related tests"""

import subprocess
import sys
from pathlib import Path


def run_tests(test_type="all"):
    """Run auth tests"""
    project_root = Path(__file__).parent
    
    if test_type == "unit":
        # Run unit tests for auth
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/unit/test_auth.py",
            "tests/unit/test_auth_multi_role.py",
            "-v",
            "-m", "unit"
        ]
    elif test_type == "integration":
        # Run integration tests for auth
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/integration/test_auth_routes.py",
            "tests/integration/test_auth_multi_role.py",
            "-v",
            "-m", "integration"
        ]
    elif test_type == "role":
        # Run role-specific tests
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/unit/test_auth_multi_role.py",
            "tests/integration/test_auth_multi_role.py",
            "-v",
            "-m", "role"
        ]
    elif test_type == "oauth":
        # Run OAuth-specific tests
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/unit/test_auth_multi_role.py::test_oauth_role_mapping",
            "tests/integration/test_auth_multi_role.py::test_oauth_role_selection_flow",
            "tests/integration/test_auth_multi_role.py::test_oauth_role_selection_submission",
            "tests/integration/test_auth_multi_role.py::test_session_based_oauth_flow",
            "-v",
            "-m", "oauth"
        ]
    else:
        # Run all auth tests
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/unit/test_auth.py",
            "tests/unit/test_auth_multi_role.py",
            "tests/integration/test_auth_routes.py",
            "tests/integration/test_auth_multi_role.py",
            "-v"
        ]
    
    print(f"Running command: {' '.join(cmd)}")
    print("=" * 80)
    
    # Run the tests
    result = subprocess.run(cmd, cwd=project_root)
    
    return result.returncode


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run auth tests")
    parser.add_argument(
        "--type",
        choices=["all", "unit", "integration", "role", "oauth"],
        default="all",
        help="Type of tests to run"
    )
    
    args = parser.parse_args()
    
    exit_code = run_tests(args.type)
    sys.exit(exit_code)
