# Dependency Security Guide

## Overview

This guide covers dependency security practices for the MatchHire backend.

## Current Dependencies

### Core Framework
- Django 5.1.7
- djangorestframework 3.15.2
- djangorestframework-simplejwt 5.5.0
- django-cors-headers 4.7.0
- drf-spectacular 0.29.0

### Database
- psycopg2-binary 2.9.10

### Task Queue & Cache
- celery 5.4.0
- redis 5.2.1

### Document Processing
- PyMuPDF 1.25.2
- PyPDF2 3.0.1
- python-docx 1.1.2

### Machine Learning
- scikit-learn 1.6.1
- torch 2.5.1+cpu
- sentence-transformers 3.4.1
- numpy 1.26.4
- pandas 2.2.2

### Web Scraping
- scrapy 2.12.0
- playwright 1.50.0

### Authentication & Security
- PyJWT 2.9.0

### Configuration
- python-decouple 3.8

### Production Server
- gunicorn 23.0.0

### Observability
- prometheus-client 0.21.0
- sentry-sdk 2.19.2

## Security Tools

### pip-audit

**Purpose:** Audit Python dependencies for known vulnerabilities

**Installation:**
```bash
pip install pip-audit
```

**Usage:**
```bash
# Audit requirements.txt
pip-audit --requirement requirements.txt

# Audit installed packages
pip-audit

# Generate JSON output for CI/CD
pip-audit --format json --output audit-report.json
```

**CI/CD Integration:**
```yaml
# .github/workflows/security.yml
- name: Run pip-audit
  run: |
    pip install pip-audit
    pip-audit --requirement requirements.txt
```

### Safety

**Purpose:** Check installed dependencies for known security vulnerabilities

**Installation:**
```bash
pip install safety
```

**Usage:**
```bash
# Check requirements.txt
safety check --file requirements.txt

# Check installed packages
safety check

# Generate JSON report
safety check --json --output safety-report.json
```

**CI/CD Integration:**
```yaml
# .github/workflows/security.yml
- name: Run safety check
  run: |
    pip install safety
    safety check --file requirements.txt
```

### Dependabot

**Purpose:** Automated dependency updates via GitHub

**Configuration:** `.github/dependabot.yml`
```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/backend"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 10
    reviewers:
      - "your-username"
    labels:
      - "dependencies"
      - "security"
```

**Benefits:**
- Automated dependency updates
- Security vulnerability alerts
- Pull request automation
- Version compatibility checks

## Pre-commit Hooks

### Configuration: `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.6
    hooks:
      - id: bandit
        args: ["-r", "backend/"]
        exclude: ^backend/migrations/

  - repo: https://github.com/PyCQA/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--settings-path=backend/pyproject.toml"]

  - repo: https://github.com/psf/black
    rev: 24.4.2
    hooks:
      - id: black
        args: ["--config=backend/pyproject.toml"]
```

### Installation

```bash
pip install pre-commit
pre-commit install
```

### Usage

```bash
# Run on all files
pre-commit run --all-files

# Run on staged files
pre-commit run
```

## Dependency Update Policy

### Version Pinning

**Current Practice:** All dependencies are pinned to specific versions in `requirements.txt`

**Rationale:**
- Reproducible builds
- Predictable deployments
- Easier rollback

### Update Categories

**Security Updates:**
- Priority: CRITICAL
- Timeline: Within 7 days of CVE disclosure
- Process: Emergency patch release

**Bug Fixes:**
- Priority: HIGH
- Timeline: Next scheduled release
- Process: Standard testing and deployment

**Feature Updates:**
- Priority: MEDIUM
- Timeline: Monthly release cycle
- Process: Full regression testing

**Major Version Updates:**
- Priority: LOW
- Timeline: Quarterly review
- Process: Comprehensive testing and migration plan

### Update Procedure

1. **Monitor:** Subscribe to security advisories for all dependencies
2. **Assess:** Evaluate impact and severity of update
3. **Test:** Update in development environment
4. **Validate:** Run full test suite and security scans
5. **Deploy:** Deploy to staging environment
6. **Verify:** Monitor for issues for 24 hours
7. **Production:** Deploy to production
8. **Document:** Update changelog and documentation

## Vulnerability Response

### Severity Levels

**CRITICAL:**
- Remote code execution
- Authentication bypass
- Data exposure
- Timeline: 24 hours

**HIGH:**
- SQL injection
- XSS vulnerabilities
- Privilege escalation
- Timeline: 72 hours

**MEDIUM:**
- CSRF vulnerabilities
- Information disclosure
- Timeline: 1 week

**LOW:**
- Minor security issues
- Best practice violations
- Timeline: Next release

### Response Process

1. **Identify:** Vulnerability detected via automated scan or disclosure
2. **Assess:** Determine severity and impact
3. **Patch:** Update vulnerable dependency
4. **Test:** Validate fix doesn't break functionality
5. **Deploy:** Deploy to production
6. **Communicate:** Notify stakeholders if required
7. **Document:** Record in security log

## Supply Chain Security

### Package Verification

**Verify package integrity:**
```bash
# Check package hashes
pip hash requirements.txt

# Verify package signatures (if available)
pip install --require-hashes -r requirements.txt
```

### Private Package Index

For enhanced security, consider using a private package index:

- **Artifactory**
- **Nexus**
- **GitHub Packages**
- **AWS CodeArtifact

### Dependency Locking

Consider using dependency locking tools:

- **pip-tools:** `pip-compile` and `pip-sync`
- **Poetry:** Modern Python dependency management
- **PDM:** Modern Python dependency manager

## Monitoring

### Security Advisories

Subscribe to security advisories:
- [Python Security Advisory Database](https://github.com/pypa/advisory-database)
- [GitHub Advisory Database](https://github.com/advisories)
- [NVD](https://nvd.nist.gov/)

### Automated Alerts

Configure automated alerts:
- GitHub Dependabot alerts
- Sentry security alerts
- Custom webhook notifications

## Best Practices

1. **Pin all dependencies:** Never use unpinned versions in production
2. **Regular updates:** Update dependencies monthly at minimum
3. **Security scans:** Run security scans in CI/CD pipeline
4. **Review updates:** Review all dependency updates before deployment
5. **Test thoroughly:** Test all updates in development and staging
6. **Document changes:** Maintain changelog for dependency updates
7. **Monitor advisories:** Subscribe to security advisory feeds
8. **Limit dependencies:** Minimize dependency footprint where possible
9. **Use virtual environments:** Always use virtual environments
10. **Audit regularly:** Perform regular dependency audits

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Security Scan

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  schedule:
    - cron: '0 0 * * 0'  # Weekly

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install pip-audit safety bandit
          pip install -r backend/requirements.txt
      
      - name: Run pip-audit
        run: pip-audit --requirement backend/requirements.txt
      
      - name: Run safety check
        run: safety check --file backend/requirements.txt
      
      - name: Run bandit
        run: bandit -r backend/ -f json -o bandit-report.json || true
      
      - name: Upload reports
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: |
            bandit-report.json
```

## References

- [OWASP Dependency Check](https://owasp.org/www-project-dependency-check/)
- [Python Packaging Authority Security](https://packaging.python.org/guides/security/)
- [pip-audit Documentation](https://pip-audit.readthedocs.io/)
- [Safety Documentation](https://pyup.io/safety/)
- [Dependabot Documentation](https://docs.github.com/en/code-security/dependabot)
