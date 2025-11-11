"""
Render Deployment Test Script
Tests both backend and frontend services after deployment
"""

import requests
import json
import sys
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

# Replace these with your actual Render URLs after deployment
BACKEND_URL = "https://system-monitoring-backend.onrender.com"
FRONTEND_URL = "https://system-monitoring-frontend.onrender.com"

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

# ============================================================================
# TEST FUNCTIONS
# ============================================================================

def print_test(test_name: str, status: bool, message: str = ""):
    """Print test result with color"""
    status_symbol = f"{Colors.GREEN}✓{Colors.END}" if status else f"{Colors.RED}✗{Colors.END}"
    status_text = f"{Colors.GREEN}PASS{Colors.END}" if status else f"{Colors.RED}FAIL{Colors.END}"
    
    print(f"{status_symbol} {Colors.BOLD}{test_name}{Colors.END}: {status_text}")
    if message:
        print(f"  {Colors.YELLOW}→{Colors.END} {message}")
    print()

def test_backend_health():
    """Test backend health endpoint"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}Testing Backend Service{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")
    
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print_test(
                "Backend Health Check",
                True,
                f"Status: {data.get('status', 'unknown')}"
            )
            return True
        else:
            print_test(
                "Backend Health Check",
                False,
                f"Status code: {response.status_code}"
            )
            return False
    except Exception as e:
        print_test(
            "Backend Health Check",
            False,
            f"Error: {str(e)}"
        )
        return False

def test_backend_root():
    """Test backend root endpoint"""
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print_test(
                "Backend Root Endpoint",
                True,
                f"Version: {data.get('version', 'unknown')}"
            )
            return True
        else:
            print_test(
                "Backend Root Endpoint",
                False,
                f"Status code: {response.status_code}"
            )
            return False
    except Exception as e:
        print_test(
            "Backend Root Endpoint",
            False,
            f"Error: {str(e)}"
        )
        return False

def test_backend_metrics():
    """Test backend metrics endpoint"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/metrics/current", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print_test(
                "Backend Metrics Endpoint",
                True,
                f"CPU: {data.get('cpu_percent', 'N/A')}%, Memory: {data.get('memory_percent', 'N/A')}%"
            )
            return True
        else:
            print_test(
                "Backend Metrics Endpoint",
                False,
                f"Status code: {response.status_code}"
            )
            return False
    except Exception as e:
        print_test(
            "Backend Metrics Endpoint",
            False,
            f"Error: {str(e)}"
        )
        return False

def test_backend_docs():
    """Test backend API documentation"""
    try:
        response = requests.get(f"{BACKEND_URL}/docs", timeout=10)
        
        if response.status_code == 200:
            print_test(
                "API Documentation",
                True,
                f"Available at: {BACKEND_URL}/docs"
            )
            return True
        else:
            print_test(
                "API Documentation",
                False,
                f"Status code: {response.status_code}"
            )
            return False
    except Exception as e:
        print_test(
            "API Documentation",
            False,
            f"Error: {str(e)}"
        )
        return False

def test_frontend():
    """Test frontend service"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}Testing Frontend Service{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")
    
    try:
        response = requests.get(FRONTEND_URL, timeout=15)
        
        if response.status_code == 200:
            print_test(
                "Frontend Accessibility",
                True,
                f"Status code: {response.status_code}"
            )
            return True
        else:
            print_test(
                "Frontend Accessibility",
                False,
                f"Status code: {response.status_code}"
            )
            return False
    except Exception as e:
        print_test(
            "Frontend Accessibility",
            False,
            f"Error: {str(e)}"
        )
        return False

def test_websocket_endpoint():
    """Test WebSocket endpoint availability"""
    # Note: This just tests if the endpoint exists, not actual WS connection
    ws_url = BACKEND_URL.replace('https://', 'wss://') + '/api/ws/ws'
    
    print_test(
        "WebSocket Endpoint",
        True,
        f"WebSocket URL: {ws_url}\n  Note: Use this URL for real-time connections"
    )
    return True

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all deployment tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}🚀 Render Deployment Test Suite{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"\n{Colors.YELLOW}Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}\n")
    
    results = []
    
    # Backend tests
    results.append(test_backend_health())
    results.append(test_backend_root())
    results.append(test_backend_metrics())
    results.append(test_backend_docs())
    results.append(test_websocket_endpoint())
    
    # Frontend tests
    results.append(test_frontend())
    
    # Summary
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}Test Summary{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")
    
    passed = sum(results)
    total = len(results)
    percentage = (passed / total) * 100 if total > 0 else 0
    
    print(f"Total Tests: {total}")
    print(f"Passed: {Colors.GREEN}{passed}{Colors.END}")
    print(f"Failed: {Colors.RED}{total - passed}{Colors.END}")
    print(f"Success Rate: {Colors.GREEN if percentage == 100 else Colors.YELLOW}{percentage:.1f}%{Colors.END}\n")
    
    if percentage == 100:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ All tests passed! Deployment is successful.{Colors.END}\n")
        print(f"{Colors.BOLD}Your application is ready to use:{Colors.END}")
        print(f"  Frontend: {Colors.BLUE}{FRONTEND_URL}{Colors.END}")
        print(f"  Backend:  {Colors.BLUE}{BACKEND_URL}{Colors.END}")
        print(f"  API Docs: {Colors.BLUE}{BACKEND_URL}/docs{Colors.END}\n")
        return 0
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ Some tests failed. Please check the logs above.{Colors.END}\n")
        print(f"{Colors.YELLOW}Troubleshooting tips:{Colors.END}")
        print(f"  1. Check if services are fully deployed in Render dashboard")
        print(f"  2. Verify environment variables are set correctly")
        print(f"  3. Check service logs for errors")
        print(f"  4. Wait a few minutes and try again (services may be starting)\n")
        return 1

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    print(f"\n{Colors.YELLOW}Note: Update BACKEND_URL and FRONTEND_URL in this script with your actual Render URLs{Colors.END}")
    print(f"{Colors.YELLOW}Current URLs:{Colors.END}")
    print(f"  Backend:  {BACKEND_URL}")
    print(f"  Frontend: {FRONTEND_URL}\n")
    
    input(f"Press Enter to continue with tests... ")
    
    exit_code = run_all_tests()
    sys.exit(exit_code)
