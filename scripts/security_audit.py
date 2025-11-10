"""
Security Audit Script for System Monitoring Platform
Checks for common vulnerabilities and security issues
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple

class SecurityAuditor:
    """Security audit and vulnerability scanner"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.issues = []
        self.warnings = []
        self.info = []
    
    def audit(self) -> Dict:
        """Run complete security audit"""
        print("🔒 Starting Security Audit...")
        print("=" * 60)
        
        self.check_secrets_in_code()
        self.check_sql_injection()
        self.check_xss_vulnerabilities()
        self.check_insecure_dependencies()
        self.check_weak_crypto()
        self.check_env_file_security()
        self.check_cors_configuration()
        self.check_rate_limiting()
        self.check_input_validation()
        
        return self.generate_report()
    
    def check_secrets_in_code(self):
        """Check for hardcoded secrets"""
        print("\n📋 Checking for hardcoded secrets...")
        
        secret_patterns = [
            (r'password\s*=\s*["\']([^"\']+)["\']', 'Hardcoded password'),
            (r'api_key\s*=\s*["\']([^"\']+)["\']', 'Hardcoded API key'),
            (r'secret\s*=\s*["\']([^"\']+)["\']', 'Hardcoded secret'),
            (r'token\s*=\s*["\']([^"\']+)["\']', 'Hardcoded token'),
            (r'aws_access_key_id\s*=\s*["\']([^"\']+)["\']', 'AWS credentials'),
        ]
        
        for py_file in self.project_root.rglob("*.py"):
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                for pattern, message in secret_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        # Exclude if it's a placeholder or example
                        if 'your_' not in match.group(1).lower() and 'example' not in match.group(1).lower():
                            self.issues.append({
                                'file': str(py_file.relative_to(self.project_root)),
                                'issue': message,
                                'line': content[:match.start()].count('\n') + 1
                            })
        
        print(f"  ✓ Checked for hardcoded secrets")
    
    def check_sql_injection(self):
        """Check for SQL injection vulnerabilities"""
        print("\n📋 Checking for SQL injection risks...")
        
        sql_patterns = [
            r'execute\([^)]*\+',  # String concatenation in execute
            r'execute\([^)]*%',   # String formatting in execute
            r'execute\([^)]*\.format\(',  # Format string in execute
        ]
        
        for py_file in self.project_root.rglob("*.py"):
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                for pattern in sql_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        self.warnings.append({
                            'file': str(py_file.relative_to(self.project_root)),
                            'issue': 'Potential SQL injection - use parameterized queries',
                            'line': content[:match.start()].count('\n') + 1
                        })
        
        print(f"  ✓ Checked for SQL injection vulnerabilities")
    
    def check_xss_vulnerabilities(self):
        """Check for XSS vulnerabilities"""
        print("\n📋 Checking for XSS vulnerabilities...")
        
        xss_patterns = [
            r'\.innerHTML\s*=',
            r'dangerouslySetInnerHTML',
            r'st\.markdown\([^,)]+,\s*unsafe_allow_html\s*=\s*True',
        ]
        
        for file in self.project_root.rglob("*.py"):
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                for pattern in xss_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        self.warnings.append({
                            'file': str(file.relative_to(self.project_root)),
                            'issue': 'Potential XSS vulnerability - sanitize user input',
                            'line': content[:match.start()].count('\n') + 1
                        })
        
        print(f"  ✓ Checked for XSS vulnerabilities")
    
    def check_insecure_dependencies(self):
        """Check for known vulnerable dependencies"""
        print("\n📋 Checking for insecure dependencies...")
        
        vulnerable_versions = {
            'django': ['< 3.2.15', '< 4.0.7'],
            'requests': ['< 2.28.0'],
            'urllib3': ['< 1.26.5'],
            'fastapi': ['< 0.68.1'],
        }
        
        req_files = list(self.project_root.rglob("requirements*.txt"))

        for req_file in req_files:
            with open(req_file, 'r', encoding='utf-8') as f:
                for raw in f:
                    line = raw.strip()
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue

                    # Take the first token (handles inline comments or extras)
                    token = line.split()[0]

                    # Normalize package and version parsing
                    package = None
                    version = None

                    if '==' in token:
                        package, version = token.split('==', 1)
                    elif any(op in token for op in ['>=', '<=', '>', '<', '~=']):
                        # Skip range specifiers for now (could be handled more precisely)
                        parts = re.split(r'(>=|<=|~=|>|<)', token)
                        package = parts[0]
                    else:
                        # No version pinned
                        package = token

                    # Remove extras like uvicorn[standard]
                    package = package.split('[')[0].strip()

                    if package.lower() in vulnerable_versions:
                        issue_msg = f'Check {package}' + (f'=={version}' if version else '')
                        self.info.append({
                            'file': str(req_file.relative_to(self.project_root)),
                            'issue': issue_msg + ' for known vulnerabilities',
                            'line': 0
                        })
        
        print(f"  ✓ Checked dependency versions")
    
    def check_weak_crypto(self):
        """Check for weak cryptographic algorithms"""
        print("\n📋 Checking for weak cryptography...")
        
        weak_crypto = [
            (r'hashlib\.md5', 'MD5 is cryptographically broken'),
            (r'hashlib\.sha1', 'SHA1 is weak, use SHA256+'),
            (r'DES|RC4|RC2', 'Weak encryption algorithm'),
        ]
        
        for py_file in self.project_root.rglob("*.py"):
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                for pattern, message in weak_crypto:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        self.warnings.append({
                            'file': str(py_file.relative_to(self.project_root)),
                            'issue': message,
                            'line': content[:match.start()].count('\n') + 1
                        })
        
        print(f"  ✓ Checked cryptographic algorithms")
    
    def check_env_file_security(self):
        """Check .env file security"""
        print("\n📋 Checking .env file security...")
        
        env_file = self.project_root / '.env'
        env_example = self.project_root / '.env.example'
        gitignore = self.project_root / '.gitignore'
        
        if env_file.exists():
            self.warnings.append({
                'file': '.env',
                'issue': '.env file exists - ensure it\'s in .gitignore',
                'line': 0
            })
        
        if not env_example.exists():
            self.warnings.append({
                'file': '.env.example',
                'issue': 'Missing .env.example template file',
                'line': 0
            })
        
        if gitignore.exists():
            with open(gitignore, 'r') as f:
                content = f.read()
                if '.env' not in content:
                    self.issues.append({
                        'file': '.gitignore',
                        'issue': '.env not in .gitignore - secrets may be exposed!',
                        'line': 0
                    })
        else:
            self.issues.append({
                'file': '.gitignore',
                'issue': 'Missing .gitignore file',
                'line': 0
            })
        
        print(f"  ✓ Checked .env file security")
    
    def check_cors_configuration(self):
        """Check CORS configuration"""
        print("\n📋 Checking CORS configuration...")
        
        for py_file in self.project_root.rglob("*.py"):
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Check for wildcard CORS
                if 'allow_origins=["*"]' in content or "allow_origins=['*']" in content:
                    self.warnings.append({
                        'file': str(py_file.relative_to(self.project_root)),
                        'issue': 'CORS configured with wildcard (*) - security risk',
                        'line': content.find('allow_origins')
                    })
        
        print(f"  ✓ Checked CORS configuration")
    
    def check_rate_limiting(self):
        """Check for rate limiting implementation"""
        print("\n📋 Checking for rate limiting...")
        
        has_rate_limiting = False
        
        for py_file in self.project_root.rglob("*.py"):
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                if 'RateLimiter' in content or '@limiter' in content or 'rate_limit' in content:
                    has_rate_limiting = True
                    break
        
        if not has_rate_limiting:
            self.warnings.append({
                'file': 'API endpoints',
                'issue': 'No rate limiting detected - add rate limiting to prevent abuse',
                'line': 0
            })
        
        print(f"  ✓ Checked rate limiting")
    
    def check_input_validation(self):
        """Check for input validation"""
        print("\n📋 Checking input validation...")
        
        for py_file in self.project_root.rglob("*.py"):
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Look for request data without validation
                if 'request.form' in content or 'request.json' in content:
                    if 'validate' not in content and 'BaseModel' not in content:
                        self.warnings.append({
                            'file': str(py_file.relative_to(self.project_root)),
                            'issue': 'Request data used without validation - use Pydantic models',
                            'line': 0
                        })
        
        print(f"  ✓ Checked input validation")
    
    def generate_report(self) -> Dict:
        """Generate security audit report"""
        print("\n" + "=" * 60)
        print("🔒 SECURITY AUDIT REPORT")
        print("=" * 60)
        
        total_issues = len(self.issues) + len(self.warnings) + len(self.info)
        
        print(f"\n📊 Summary:")
        print(f"  🔴 Critical Issues: {len(self.issues)}")
        print(f"  🟡 Warnings: {len(self.warnings)}")
        print(f"  🔵 Info: {len(self.info)}")
        print(f"  📈 Total Findings: {total_issues}")
        
        if self.issues:
            print(f"\n🔴 CRITICAL ISSUES ({len(self.issues)}):")
            for issue in self.issues:
                print(f"  ⚠️  {issue['file']}:{issue['line']}")
                print(f"      {issue['issue']}")
        
        if self.warnings:
            print(f"\n🟡 WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings[:10]:  # Show first 10
                print(f"  ⚠️  {warning['file']}:{warning['line']}")
                print(f"      {warning['issue']}")
            
            if len(self.warnings) > 10:
                print(f"  ... and {len(self.warnings) - 10} more warnings")
        
        print("\n" + "=" * 60)
        
        if len(self.issues) == 0:
            print("✅ No critical security issues found!")
        else:
            print("⚠️  Please address critical issues before deployment")
        
        print("=" * 60)
        
        return {
            'issues': self.issues,
            'warnings': self.warnings,
            'info': self.info,
            'total': total_issues
        }

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    auditor = SecurityAuditor(project_root)
    report = auditor.audit()
    
    # Exit with error code if critical issues found
    sys.exit(1 if report['issues'] else 0)
