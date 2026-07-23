"""
Environment and Configuration Validation

Provides validation for environment variables, configuration,
and startup diagnostics.
"""

import logging
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from django.conf import settings
from decouple import config

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Validation severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationResult:
    """Result of a validation check."""
    name: str
    severity: ValidationSeverity
    message: str
    passed: bool
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class EnvironmentValidator:
    """
    Environment variable validation.
    
    Validates that required environment variables are set and valid.
    """
    
    REQUIRED_VARS = {
        "SECRET_KEY": {"required": True, "description": "Django secret key"},
        "DB_NAME": {"required": True, "description": "Database name"},
        "DB_USER": {"required": True, "description": "Database user"},
        "DB_PASSWORD": {"required": True, "description": "Database password"},
        "DB_HOST": {"required": True, "description": "Database host"},
        "DB_PORT": {"required": True, "description": "Database port"},
        "REDIS_URL": {"required": True, "description": "Redis URL"},
    }
    
    OPTIONAL_VARS = {
        "SENTRY_DSN": {"required": False, "description": "Sentry DSN for error tracking"},
        "ELASTICSEARCH_HOSTS": {"required": False, "description": "Elasticsearch hosts"},
        "ALLOWED_HOSTS": {"required": False, "description": "Allowed hosts for Django"},
        "CORS_ALLOWED_ORIGINS": {"required": False, "description": "CORS allowed origins"},
    }
    
    def __init__(self):
        self.results: List[ValidationResult] = []
        
    def validate_required_vars(self) -> List[ValidationResult]:
        """
        Validate required environment variables.
        
        Returns:
            List of validation results
        """
        results = []
        
        for var_name, config in self.REQUIRED_VARS.items():
            value = os.environ.get(var_name)
            
            if value is None or value == "":
                results.append(ValidationResult(
                    name=f"env.{var_name}",
                    severity=ValidationSeverity.ERROR,
                    message=f"Required environment variable {var_name} is not set",
                    passed=False,
                    metadata={"description": config["description"]},
                ))
            else:
                results.append(ValidationResult(
                    name=f"env.{var_name}",
                    severity=ValidationSeverity.INFO,
                    message=f"Environment variable {var_name} is set",
                    passed=True,
                    metadata={"description": config["description"]},
                ))
                
        self.results.extend(results)
        return results
        
    def validate_optional_vars(self) -> List[ValidationResult]:
        """
        Validate optional environment variables.
        
        Returns:
            List of validation results
        """
        results = []
        
        for var_name, config in self.OPTIONAL_VARS.items():
            value = os.environ.get(var_name)
            
            if value is None or value == "":
                results.append(ValidationResult(
                    name=f"env.{var_name}",
                    severity=ValidationSeverity.WARNING,
                    message=f"Optional environment variable {var_name} is not set",
                    passed=True,  # Optional vars don't fail validation
                    metadata={"description": config["description"]},
                ))
            else:
                results.append(ValidationResult(
                    name=f"env.{var_name}",
                    severity=ValidationSeverity.INFO,
                    message=f"Environment variable {var_name} is set",
                    passed=True,
                    metadata={"description": config["description"]},
                ))
                
        self.results.extend(results)
        return results
        
    def validate_secret_key(self) -> ValidationResult:
        """
        Validate SECRET_KEY strength.
        
        Returns:
            ValidationResult
        """
        secret_key = os.environ.get("SECRET_KEY", "")
        
        if len(secret_key) < 32:
            return ValidationResult(
                name="env.SECRET_KEY",
                severity=ValidationSeverity.ERROR,
                message=f"SECRET_KEY is too short (length: {len(secret_key)}, minimum: 32)",
                passed=False,
                metadata={"length": len(secret_key)},
            )
        elif secret_key in ["change-me", "dev", "test", "production"]:
            return ValidationResult(
                name="env.SECRET_KEY",
                severity=ValidationSeverity.ERROR,
                message="SECRET_KEY is using a default/insecure value",
                passed=False,
            )
        else:
            return ValidationResult(
                name="env.SECRET_KEY",
                severity=ValidationSeverity.INFO,
                message="SECRET_KEY is properly configured",
                passed=True,
                metadata={"length": len(secret_key)},
            )
            
    def validate_debug_mode(self) -> ValidationResult:
        """
        Validate DEBUG mode setting.
        
        Returns:
            ValidationResult
        """
        debug = config("DEBUG", default=False, cast=bool)
        environment = config("ENVIRONMENT", default="development")
        
        if environment == "production" and debug:
            return ValidationResult(
                name="env.DEBUG",
                severity=ValidationSeverity.ERROR,
                message="DEBUG=True is not allowed in production",
                passed=False,
                metadata={"environment": environment, "debug": debug},
            )
        elif environment == "production" and not debug:
            return ValidationResult(
                name="env.DEBUG",
                severity=ValidationSeverity.INFO,
                message="DEBUG is correctly set to False in production",
                passed=True,
                metadata={"environment": environment, "debug": debug},
            )
        else:
            return ValidationResult(
                name="env.DEBUG",
                severity=ValidationSeverity.INFO,
                message=f"DEBUG={debug} in {environment} environment",
                passed=True,
                metadata={"environment": environment, "debug": debug},
            )
            
    def validate_database_url(self) -> ValidationResult:
        """
        Validate database connection string format.
        
        Returns:
            ValidationResult
        """
        db_host = os.environ.get("DB_HOST", "")
        db_port = os.environ.get("DB_PORT", "")
        
        if not db_host:
            return ValidationResult(
                name="env.DB_HOST",
                severity=ValidationSeverity.ERROR,
                message="DB_HOST is not set",
                passed=False,
            )
            
        try:
            port = int(db_port)
            if not (1 <= port <= 65535):
                return ValidationResult(
                    name="env.DB_PORT",
                    severity=ValidationSeverity.ERROR,
                    message=f"DB_PORT is invalid: {db_port}",
                    passed=False,
                )
        except ValueError:
            return ValidationResult(
                name="env.DB_PORT",
                severity=ValidationSeverity.ERROR,
                message=f"DB_PORT is not a valid integer: {db_port}",
                passed=False,
            )
            
        return ValidationResult(
            name="env.DATABASE",
            severity=ValidationSeverity.INFO,
            message="Database configuration is valid",
            passed=True,
            metadata={"host": db_host, "port": db_port},
        )
        
    def validate_redis_url(self) -> ValidationResult:
        """
        Validate Redis URL format.
        
        Returns:
            ValidationResult
        """
        redis_url = os.environ.get("REDIS_URL", "")
        
        if not redis_url:
            return ValidationResult(
                name="env.REDIS_URL",
                severity=ValidationSeverity.ERROR,
                message="REDIS_URL is not set",
                passed=False,
            )
            
        if not redis_url.startswith("redis://"):
            return ValidationResult(
                name="env.REDIS_URL",
                severity=ValidationSeverity.ERROR,
                message="REDIS_URL must start with redis://",
                passed=False,
            )
            
        return ValidationResult(
            name="env.REDIS_URL",
            severity=ValidationSeverity.INFO,
            message="Redis URL is valid",
            passed=True,
        )
        
    def run_all_validations(self) -> Dict[str, Any]:
        """
        Run all environment validations.
        
        Returns:
            Dictionary with validation summary
        """
        self.results = []
        
        # Run all validations
        self.validate_required_vars()
        self.validate_optional_vars()
        self.results.append(self.validate_secret_key())
        self.results.append(self.validate_debug_mode())
        self.results.append(self.validate_database_url())
        self.results.append(self.validate_redis_url())
        
        # Calculate summary
        errors = [r for r in self.results if r.severity == ValidationSeverity.ERROR]
        warnings = [r for r in self.results if r.severity == ValidationSeverity.WARNING]
        
        return {
            "passed": len(errors) == 0,
            "total_checks": len(self.results),
            "errors": len(errors),
            "warnings": len(warnings),
            "results": [
                {
                    "name": r.name,
                    "severity": r.severity.value,
                    "message": r.message,
                    "passed": r.passed,
                    "metadata": r.metadata,
                }
                for r in self.results
            ],
        }


class ConfigurationValidator:
    """
    Django settings validation.
    
    Validates Django configuration settings.
    """
    
    def __init__(self):
        self.results: List[ValidationResult] = []
        
    def validate_installed_apps(self) -> ValidationResult:
        """
        Validate INSTALLED_APPS configuration.
        
        Returns:
            ValidationResult
        """
        required_apps = [
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "rest_framework",
            "apps.search",
        ]
        
        installed = getattr(settings, "INSTALLED_APPS", [])
        missing = [app for app in required_apps if app not in installed]
        
        if missing:
            return ValidationResult(
                name="config.INSTALLED_APPS",
                severity=ValidationSeverity.ERROR,
                message=f"Missing required apps: {', '.join(missing)}",
                passed=False,
                metadata={"missing": missing},
            )
        else:
            return ValidationResult(
                name="config.INSTALLED_APPS",
                severity=ValidationSeverity.INFO,
                message="All required apps are installed",
                passed=True,
            )
            
    def validate_database_config(self) -> ValidationResult:
        """
        Validate database configuration.
        
        Returns:
            ValidationResult
        """
        databases = getattr(settings, "DATABASES", {})
        
        if "default" not in databases:
            return ValidationResult(
                name="config.DATABASES",
                severity=ValidationSeverity.ERROR,
                message="Default database configuration is missing",
                passed=False,
            )
            
        db_config = databases["default"]
        required_keys = ["ENGINE", "NAME", "USER", "PASSWORD", "HOST", "PORT"]
        missing_keys = [key for key in required_keys if key not in db_config]
        
        if missing_keys:
            return ValidationResult(
                name="config.DATABASES",
                severity=ValidationSeverity.ERROR,
                message=f"Missing database config keys: {', '.join(missing_keys)}",
                passed=False,
                metadata={"missing": missing_keys},
            )
        else:
            return ValidationResult(
                name="config.DATABASES",
                severity=ValidationSeverity.INFO,
                message="Database configuration is valid",
                passed=True,
            )
            
    def validate_cache_config(self) -> ValidationResult:
        """
        Validate cache configuration.
        
        Returns:
            ValidationResult
        """
        caches = getattr(settings, "CACHES", {})
        
        if "default" not in caches:
            return ValidationResult(
                name="config.CACHES",
                severity=ValidationSeverity.WARNING,
                message="Default cache configuration is missing",
                passed=False,
            )
        else:
            return ValidationResult(
                name="config.CACHES",
                severity=ValidationSeverity.INFO,
                message="Cache configuration is present",
                passed=True,
            )
            
    def validate_middleware(self) -> ValidationResult:
        """
        Validate middleware configuration.
        
        Returns:
            ValidationResult
        """
        middleware = getattr(settings, "MIDDLEWARE", [])
        required_middleware = [
            "django.middleware.security.SecurityMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "matchhire_backend.core.security_headers.SecurityHeadersMiddleware",
        ]
        
        missing = [mw for mw in required_middleware if mw not in middleware]
        
        if missing:
            return ValidationResult(
                name="config.MIDDLEWARE",
                severity=ValidationSeverity.WARNING,
                message=f"Missing recommended middleware: {', '.join(missing)}",
                passed=False,
                metadata={"missing": missing},
            )
        else:
            return ValidationResult(
                name="config.MIDDLEWARE",
                severity=ValidationSeverity.INFO,
                message="All required middleware is configured",
                passed=True,
            )
            
    def run_all_validations(self) -> Dict[str, Any]:
        """
        Run all configuration validations.
        
        Returns:
            Dictionary with validation summary
        """
        self.results = []
        
        self.results.append(self.validate_installed_apps())
        self.results.append(self.validate_database_config())
        self.results.append(self.validate_cache_config())
        self.results.append(self.validate_middleware())
        
        errors = [r for r in self.results if r.severity == ValidationSeverity.ERROR]
        warnings = [r for r in self.results if r.severity == ValidationSeverity.WARNING]
        
        return {
            "passed": len(errors) == 0,
            "total_checks": len(self.results),
            "errors": len(errors),
            "warnings": len(warnings),
            "results": [
                {
                    "name": r.name,
                    "severity": r.severity.value,
                    "message": r.message,
                    "passed": r.passed,
                    "metadata": r.metadata,
                }
                for r in self.results
            ],
        }


class StartupDiagnostics:
    """
    Startup diagnostics utility.
    
    Runs diagnostic checks at application startup.
    """
    
    def __init__(self):
        self.env_validator = EnvironmentValidator()
        self.config_validator = ConfigurationValidator()
        
    def run_diagnostics(self) -> Dict[str, Any]:
        """
        Run all startup diagnostics.
        
        Returns:
            Dictionary with diagnostic results
        """
        logger.info("Running startup diagnostics...")
        
        env_results = self.env_validator.run_all_validations()
        config_results = self.config_validator.run_all_validations()
        
        # System diagnostics
        import platform
        import psutil
        
        system_info = {
            "python_version": sys.version,
            "platform": platform.platform(),
            "cpu_count": psutil.cpu_count(),
            "memory_gb": psutil.virtual_memory().total / 1024 / 1024 / 1024,
        }
        
        overall_passed = env_results["passed"] and config_results["passed"]
        
        if not overall_passed:
            logger.error("Startup diagnostics failed")
        else:
            logger.info("Startup diagnostics passed")
            
        return {
            "passed": overall_passed,
            "environment": env_results,
            "configuration": config_results,
            "system": system_info,
            "timestamp": datetime.utcnow().isoformat(),
        }


def validate_startup() -> bool:
    """
    Validate startup and exit if critical errors are found.
    
    Returns:
        True if validation passed
    """
    diagnostics = StartupDiagnostics()
    results = diagnostics.run_diagnostics()
    
    if not results["passed"]:
        logger.critical("Startup validation failed. Please fix the errors above.")
        if not config("DEBUG", default=False, cast=bool):
            sys.exit(1)
            
    return results["passed"]
