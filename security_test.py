#!/usr/bin/env python
"""
Security testing script for PizzaCone project.
Runs security checks based on OWASP Top 10.
"""

import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def run_command(cmd, description):
    """Run a command and report results."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(cmd, shell=True, cwd=BASE_DIR)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running {description}: {e}")
        return False


def main():
    """Run all security tests."""
    print("PizzaCone Security Testing Suite")
    print(f"Running from: {BASE_DIR}")
    
    results = {}
    
    # 1. Django deployment checks
    results['Django Deploy Check'] = run_command(
        'python manage.py check --deploy',
        'Django Deployment Security Check'
    )
    
    # 2. Django security checks
    results['Django Check'] = run_command(
        'python manage.py check',
        'Django System Checks'
    )
    
    # 3. Run tests
    results['Unit Tests'] = run_command(
        'python manage.py test',
        'Unit Tests'
    )
    
    # 4. Code quality (if flake8 is installed)
    try:
        subprocess.run(['flake8', '--version'], capture_output=True, check=True)
        results['Flake8 Linting'] = run_command(
            'flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics',
            'Flake8 Linting'
        )
    except:
        print("\n⚠️  Flake8 not installed. Install with: pip install flake8")
    
    # 5. Security scanning (if bandit is installed)
    try:
        subprocess.run(['bandit', '--version'], capture_output=True, check=True)
        results['Bandit Security'] = run_command(
            'bandit -r . --skip B101,B601 -q',
            'Bandit Security Scan'
        )
    except:
        print("\n⚠️  Bandit not installed. Install with: pip install bandit")
    
    # 6. Dependency checks (if safety is installed)
    try:
        subprocess.run(['safety', '--version'], capture_output=True, check=True)
        results['Safety Check'] = run_command(
            'safety check --json',
            'Safety Dependency Check'
        )
    except:
        print("\n⚠️  Safety not installed. Install with: pip install safety")
    
    # 7. Audit dependencies (if pip-audit is installed)
    try:
        subprocess.run(['pip-audit', '--version'], capture_output=True, check=True)
        results['Pip Audit'] = run_command(
            'pip-audit --desc',
            'Pip Audit - Python Dependency Vulnerabilities'
        )
    except:
        print("\n⚠️  Pip-audit not installed. Install with: pip install pip-audit")
    
    # Print summary
    print("\n" + "="*60)
    print("SECURITY TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All security checks passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} security check(s) failed. Review output above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
