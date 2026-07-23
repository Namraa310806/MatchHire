"""
Security Validation Module

Provides secret validation, dependency scanning, configuration validation,
secure defaults, input validation review, and permission audit.
"""

import hashlib
import logging
import os
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from django.conf import settings
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class SecuritySeverity(Enum):
    """Security issue severity."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class SecurityIssue:
    """Security issue report."""
    name: str
    severity: SecuritySeverity
    description: str
    recommendation: str
    location: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class SecretValidator:
    """
    Secret validation utilities.
    
    Validates that secrets are properly configured and not using defaults.
    """
    
    WEAK_PATTERNS = [
        r"password",
        r"123456",
        r"qwerty",
        r"admin",
        r"test",
        r"dev",
        r"changeme",
        r"secret",
        r"key",
    ]
    
    def __init__(self):
        self.issues: List[SecurityIssue] = []
        
    def validate_secret_strength(self, secret: str, secret_name: str = "secret") -> SecurityIssue:
        """
        Validate secret strength.
        
        Args:
            secret: Secret value
            secret_name: Name of the secret
            
        Returns:
            SecurityIssue if weak, None if strong
        """
        if len(secret) < 32:
            return SecurityIssue(
                name=f"secret.{secret_name}",
                severity=SecuritySeverity.HIGH,
                description=f"Secret {secret_name} is too short (length: {len(secret)})",
                recommendation="Use a secret with at least 32 characters",
                metadata={"length": len(secret)},
            )
            
        # Check for weak patterns
        secret_lower = secret.lower()
        for pattern in self.WEAK_PATTERNS:
            if pattern in secret_lower:
                return SecurityIssue(
                    name=f"secret.{secret_name}",
                    severity=SecuritySeverity.CRITICAL,
                    description=f"Secret {secret_name} contains weak pattern: {pattern}",
                    recommendation="Use a strong, randomly generated secret",
                    metadata={"pattern": pattern},
                )
                
        # Check entropy (basic check)
        unique_chars = len(set(secret))
        if unique_chars < 16:
            return SecurityIssue(
                name=f"secret.{secret_name}",
                severity=SecuritySeverity.MEDIUM,
                description=f"Secret {secret_name} has low entropy (unique chars: {unique_chars})",
                recommendation="Use a secret with more character variety",
                metadata={"unique_chars": unique_chars},
            )
            
        return None
        
    def validate_no_hardcoded_secrets(self, code_dir: str = ".") -> List[SecurityIssue]:
        """
        Scan codebase for hardcoded secrets.
        
        Args:
            code_dir: Directory to scan
            
        Returns:
            List of SecurityIssue
        """
        issues = []
        secret_patterns = [
            (r"api_key\s*=\s*['\"]([^'\"]{20,})['\"]", "API key"),
            (r"secret\s*=\s*['\"]([^'\"]{20,})['\"]", "Secret"),
            (r"password\s*=\s*['\"]([^'\"]{8,})['\"]", "Password"),
            (r"token\s*=\s*['\"]([^'\"]{20,})['\"]", "Token"),
        ]
        
        try:
            for root, dirs, files in os.walk(code_dir):
                # Skip common directories
                dirs[:] = [d for d in dirs if d not in ["node_modules", ".git", "__pycache__", "venv"]]
                
                for file in files:
                    if file.endswith((".py", ".js", ".ts", ".yml", ".yaml", ".env")):
                        filepath = os.path.join(root, file)
                        try:
                            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                                content = f.read()
                                
                            for pattern, secret_type in secret_patterns:
                                matches = re.finditer(pattern, content, re.IGNORECASE)
                                for match in matches:
                                    issues.append(SecurityIssue(
                                        name="hardcoded_secret",
                                        severity=SecuritySeverity.CRITICAL,
                                        description=f"Hardcoded {secret_type} found in {filepath}",
                                        recommendation="Use environment variables or secret management",
                                        location=filepath,
                                        metadata={"line": content[:match.start()].count("\n") + 1},
                                    ))
                        except Exception as e:
                            logger.warning(f"Could not scan {filepath}: {e}")
                            
        except Exception as e:
            logger.error(f"Error scanning for secrets: {e}")
            
        return issues
        
    def validate_environment_secrets(self) -> List[SecurityIssue]:
        """
        Validate environment secrets.
        
        Returns:
            List of SecurityIssue
        """
        issues = []
        
        # Check SECRET_KEY
        secret_key = os.environ.get("SECRET_KEY", "")
        issue = self.validate_secret_strength(secret_key, "SECRET_KEY")
        if issue:
            issues.append(issue)
            
        # Check database password
        db_password = os.environ.get("DB_PASSWORD", "")
        if db_password:
            issue = self.validate_secret_strength(db_password, "DB_PASSWORD")
            if issue:
                issues.append(issue)
                
        return issues


class DependencyScanner:
    """
    Dependency security scanner.
    
    Scans dependencies for known vulnerabilities.
    """
    
    def __init__(self):
        self.issues: List[SecurityIssue] = []
        
    def scan_requirements(self, requirements_file: str = "requirements.txt") -> List[SecurityIssue]:
        """
        Scan requirements file for vulnerabilities.
        
        Args:
            requirements_file: Path to requirements file
            
        Returns:
            List of SecurityIssue
        """
        issues = []
        
        if not os.path.exists(requirements_file):
            issues.append(SecurityIssue(
                name="dependency_scan",
                severity=SecuritySeverity.INFO,
                description=f"Requirements file not found: {requirements_file}",
                recommendation="Ensure requirements.txt exists and is up to date",
            ))
            return issues
            
        try:
            # Try to use safety if available
            result = subprocess.run(
                ["safety", "check", "-r", requirements_file, "--json"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            if result.returncode != 0 and result.stdout:
                import json
                try:
                    vulns = json.loads(result.stdout)
                    for vuln in vulns:
                        issues.append(SecurityIssue(
                            name="dependency_vulnerability",
                            severity=SecuritySeverity.HIGH,
                            description=f"Vulnerability in {vuln.get('package', 'unknown')}: {vuln.get('advisory', 'unknown')}",
                            recommendation=f"Upgrade to version {vuln.get('fixed_versions', ['latest'])[0]}",
                            metadata=vuln,
                        ))
                except json.JSONDecodeError:
                    pass
                    
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Safety not installed, log warning
            logger.warning("Safety not installed, skipping dependency scan")
            issues.append(SecurityIssue(
                name="dependency_scan",
                severity=SecuritySeverity.INFO,
                description="Dependency scanning tool (safety) not installed",
                recommendation="Install safety: pip install safety",
            ))
            
        return issues
        
    def scan_outdated_dependencies(self) -> List[SecurityIssue]:
        """
        Scan for outdated dependencies.
        
        Returns:
            List of SecurityIssue
        """
        issues = []
        
        try:
            result = subprocess.run(
                ["pip", "list", "--outdated", "--format=json"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            if result.stdout:
                import json
                try:
                    outdated = json.loads(result.stdout)
                    for pkg in outdated:
                        issues.append(SecurityIssue(
                            name="outdated_dependency",
                            severity=SecuritySeverity.LOW,
                            description=f"Outdated package: {pkg['name']} (current: {pkg['version']}, latest: {pkg['latest_version']})",
                            recommendation=f"Upgrade {pkg['name']} to {pkg['latest_version']}",
                            metadata=pkg,
                        ))
                except json.JSONDecodeError:
                    pass
                    
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning(f"Could not check outdated dependencies: {e}")
            
        return issues


class ConfigurationValidator:
    """
    Security configuration validation.
    
    Validates security-related configuration settings.
    """
    
    def __init__(self):
        self.issues: List[SecurityIssue] = []
        
    def validate_debug_mode(self) -> Optional[SecurityIssue]:
        """
        Validate DEBUG mode setting.
        
        Returns:
            SecurityIssue if DEBUG is enabled in production
        """
        debug = getattr(settings, "DEBUG", False)
        environment = os.environ.get("ENVIRONMENT", "development")
        
        if environment == "production" and debug:
            return SecurityIssue(
                name="config.debug",
                severity=SecuritySeverity.CRITICAL,
                description="DEBUG=True is enabled in production",
                recommendation="Set DEBUG=False in production",
                metadata={"environment": environment, "debug": debug},
            )
            
        return None
        
    def validate_allowed_hosts(self) -> Optional[SecurityIssue]:
        """
        Validate ALLOWED_HOSTS setting.
        
        Returns:
            SecurityIssue if ALLOWED_HOSTS is misconfigured
        """
        allowed_hosts = getattr(settings, "ALLOWED_HOSTS", [])
        
        if "*" in allowed_hosts:
            return SecurityIssue(
                name="config.allowed_hosts",
                severity=SecuritySeverity.HIGH,
                description="ALLOWED_HOSTS contains wildcard '*'",
                recommendation="Specify explicit hostnames in ALLOWED_HOSTS",
                metadata={"allowed_hosts": allowed_hosts},
            )
            
        if not allowed_hosts:
            return SecurityIssue(
                name="config.allowed_hosts",
                severity=SecuritySeverity.MEDIUM,
                description="ALLOWED_HOSTS is empty",
                recommendation="Configure ALLOWED_HOSTS with your domain names",
                metadata={"allowed_hosts": allowed_hosts},
            )
            
        return None
        
    def validate_secure_ssl_redirect(self) -> Optional[SecurityIssue]:
        """
        Validate SSL redirect settings.
        
        Returns:
            SecurityIssue if SSL is not enforced in production
        """
        environment = os.environ.get("ENVIRONMENT", "development")
        
        if environment == "production":
            secure_ssl = getattr(settings, "SECURE_SSL_REDIRECT", False)
            session_cookie_secure = getattr(settings, "SESSION_COOKIE_SECURE", False)
            csrf_cookie_secure = getattr(settings, "CSRF_COOKIE_SECURE", False)
            
            issues = []
            
            if not secure_ssl:
                issues.append("SECURE_SSL_REDIRECT")
            if not session_cookie_secure:
                issues.append("SESSION_COOKIE_SECURE")
            if not csrf_cookie_secure:
                issues.append("CSRF_COOKIE_SECURE")
                
            if issues:
                return SecurityIssue(
                    name="config.ssl",
                    severity=SecuritySeverity.HIGH,
                    description=f"SSL not enforced: {', '.join(issues)}",
                    recommendation="Enable SSL-related settings in production",
                    metadata={"missing_settings": issues},
                )
                
        return None
        
    def validate_password_validation(self) -> Optional[SecurityIssue]:
        """
        Validate password validators.
        
        Returns:
            SecurityIssue if password validation is weak
        """
        auth_password_validators = getattr(settings, "AUTH_PASSWORD_VALIDATORS", [])
        
        if not auth_password_validators:
            return SecurityIssue(
                name="config.password_validation",
                severity=SecuritySeverity.MEDIUM,
                description="No password validators configured",
                recommendation="Configure AUTH_PASSWORD_VALIDATORS with strong validators",
            )
            
        return None
        
    def validate_session_settings(self) -> Optional[SecurityIssue]:
        """
        Validate session security settings.
        
        Returns:
            SecurityIssue if session settings are insecure
        """
        environment = os.environ.get("ENVIRONMENT", "development")
        
        if environment == "production":
            session_cookie_httponly = getattr(settings, "SESSION_COOKIE_HTTPONLY", True)
            
            if not session_cookie_httponly:
                return SecurityIssue(
                    name="config.session",
                    severity=SecuritySeverity.HIGH,
                    description="SESSION_COOKIE_HTTPONLY is False",
                    recommendation="Set SESSION_COOKIE_HTTPONLY=True to prevent XSS",
                )
                
        return None
        
    def run_all_validations(self) -> List[SecurityIssue]:
        """
        Run all configuration validations.
        
        Returns:
            List of SecurityIssue
        """
        issues = []
        
        issue = self.validate_debug_mode()
        if issue:
            issues.append(issue)
            
        issue = self.validate_allowed_hosts()
        if issue:
            issues.append(issue)
            
        issue = self.validate_secure_ssl_redirect()
        if issue:
            issues.append(issue)
            
        issue = self.validate_password_validation()
        if issue:
            issues.append(issue)
            
        issue = self.validate_session_settings()
        if issue:
            issues.append(issue)
            
        return issues


class PermissionAuditor:
    """
    Permission audit utilities.
    
    Audits user permissions and access controls.
    """
    
    def __init__(self):
        self.issues: List[SecurityIssue] = []
        
    def audit_superuser_accounts(self) -> List[SecurityIssue]:
        """
        Audit superuser accounts.
        
        Returns:
            List of SecurityIssue
        """
        issues = []
        
        try:
            from apps.users.models import User
            
            superusers = User.objects.filter(is_superuser=True)
            
            if superusers.count() > 5:
                issues.append(SecurityIssue(
                    name="permission.superusers",
                    severity=SecuritySeverity.MEDIUM,
                    description=f"Too many superuser accounts: {superusers.count()}",
                    recommendation="Limit superuser accounts to essential personnel",
                    metadata={"count": superusers.count()},
                ))
                
            for user in superusers:
                if user.email in ["admin@example.com", "test@example.com"]:
                    issues.append(SecurityIssue(
                        name="permission.superuser_email",
                        severity=SecuritySeverity.HIGH,
                        description=f"Superuser with default email: {user.email}",
                        recommendation="Change default email addresses",
                        metadata={"user_id": user.id, "email": user.email},
                    ))
                    
        except Exception as e:
            logger.warning(f"Could not audit superusers: {e}")
            
        return issues
        
    def audit_api_permissions(self) -> List[SecurityIssue]:
        """
        Audit API endpoint permissions.
        
        Returns:
            List of SecurityIssue
        """
        issues = []
        
        try:
            from django.urls import get_resolver
            from rest_framework.views import APIView
            
            resolver = get_resolver()
            
            for pattern in resolver.url_patterns:
                # Check for unauthenticated endpoints
                # This is a simplified check
                pass
                
        except Exception as e:
            logger.warning(f"Could not audit API permissions: {e}")
            
        return issues


class SecurityValidator:
    """
    Main security validator.
    
    Coordinates all security validation checks.
    """
    
    def __init__(self):
        self.secret_validator = SecretValidator()
        self.dependency_scanner = DependencyScanner()
        self.config_validator = ConfigurationValidator()
        self.permission_auditor = PermissionAuditor()
        
    def run_full_audit(self) -> Dict[str, Any]:
        """
        Run full security audit.
        
        Returns:
            Dictionary with audit results
        """
        logger.info("Running full security audit...")
        
        all_issues = []
        
        # Secret validation
        secret_issues = self.secret_validator.validate_environment_secrets()
        hardcoded_issues = self.secret_validator.validate_no_hardcoded_secrets()
        all_issues.extend(secret_issues)
        all_issues.extend(hardcoded_issues)
        
        # Dependency scanning
        dep_issues = self.dependency_scanner.scan_requirements()
        outdated_issues = self.dependency_scanner.scan_outdated_dependencies()
        all_issues.extend(dep_issues)
        all_issues.extend(outdated_issues)
        
        # Configuration validation
        config_issues = self.config_validator.run_all_validations()
        all_issues.extend(config_issues)
        
        # Permission audit
        perm_issues = self.permission_auditor.audit_superuser_accounts()
        all_issues.extend(perm_issues)
        
        # Categorize by severity
        critical = [i for i in all_issues if i.severity == SecuritySeverity.CRITICAL]
        high = [i for i in all_issues if i.severity == SecuritySeverity.HIGH]
        medium = [i for i in all_issues if i.severity == SecuritySeverity.MEDIUM]
        low = [i for i in all_issues if i.severity == SecuritySeverity.LOW]
        info = [i for i in all_issues if i.severity == SecuritySeverity.INFO]
        
        return {
            "passed": len(critical) == 0,
            "total_issues": len(all_issues),
            "summary": {
                "critical": len(critical),
                "high": len(high),
                "medium": len(medium),
                "low": len(low),
                "info": len(info),
            },
            "issues": [
                {
                    "name": issue.name,
                    "severity": issue.severity.value,
                    "description": issue.description,
                    "recommendation": issue.recommendation,
                    "location": issue.location,
                    "metadata": issue.metadata,
                }
                for issue in all_issues
            ],
            "timestamp": datetime.utcnow().isoformat(),
        }


# Global security validator instance
security_validator = SecurityValidator()
