#!/usr/bin/env python3
"""
Run tests for new features
"""

import subprocess
import sys

def run_test(test_file, description):
    """Run a specific test file"""
    print(f"\n{'='*60}")
    print(f"Running {description}")
    print(f"{'='*60}")
    
    result = subprocess.run(
        ["uv", "run", "pytest", test_file, "-v"],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print("Errors:")
        print(result.stderr)
    
    return result.returncode == 0

def main():
    """Run all new feature tests"""
    tests = [
        ("tests/test_db_config.py", "Database Configuration Tests"),
        ("tests/test_migrations.py", "Migration System Tests"),
        ("tests/test_device_management.py", "Device Management Tests"),
        ("tests/test_jwt_refresh.py", "JWT Refresh Token Tests"),
        ("tests/test_auth_integration.py", "Authentication Integration Tests"),
    ]
    
    passed = 0
    failed = 0
    
    for test_file, description in tests:
        if run_test(test_file, description):
            passed += 1
            print(f"✅ {description} PASSED")
        else:
            failed += 1
            print(f"❌ {description} FAILED")
    
    print(f"\n{'='*60}")
    print(f"Test Summary")
    print(f"{'='*60}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")
    
    if failed > 0:
        print("\n❌ Some tests failed!")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()
