# Security Monitoring Guide

## Overview

This guide covers security monitoring practices for the MatchHire backend production deployment.

## Security Events

### Logged Security Events

The MatchHire backend logs the following security events via the SecurityAuditService:

**Authentication Events:**
- Failed login attempts
- Successful logins
- Logout events
- Token refresh events
- Registration attempts

**Authorization Events:**
- Permission denied errors
- Unauthorized access attempts
- Admin access events

**Rate Limiting Events:**
- Rate limit exceeded (user-based)
- Rate limit exceeded (IP-based)
- Throttle violations

**File Upload Events:**
- Invalid file type attempts
- File size violations
- Malicious file signature detection

**API Security Events:**
- Invalid API key usage (if implemented)
- Suspicious request patterns
- Abnormal request volumes

### Event Log Format

All security events follow this structured format:

```
EVENT_TYPE | timestamp | user_id (if available) | email_identifier | ip_address | additional_context
```

**Examples:**
```
FAILED_LOGIN | 2026-01-15T10:30:00Z | null | user@example.com | 192.168.1.100 | reason=invalid_credentials
PERMISSION_DENIED | 2026-01-15T10:31:00Z | 123a456b-789c-0def-1234-56789abcdef0 | null | 192.168.1.100 | resource=jobs, action=create
IP_RATE_LIMIT_EXCEEDED | 2026-01-15T10:32:00Z | null | null | 192.168.1.100 | scope=ip_login, rate=5/hour
```

## Monitoring Tools

### Sentry Integration

**Current Setup:**
- Sentry DSN configured via `SENTRY_DSN` environment variable
- PII filtering enabled
- Error tracking for application errors
- Performance monitoring

**Security Event Tracking:**
```python
# Security events are logged to application logs
# Sentry captures these as error events with appropriate tags
import logging

logger = logging.getLogger('matchhire.security')
logger.warning(
    f"FAILED_LOGIN | email={email} | ip={ip_address} | reason={reason}"
)
```

**Sentry Alerts Configuration:**

**Critical Alerts (Immediate):**
- 10+ failed login attempts from single IP in 5 minutes
- 50+ permission denied errors in 1 hour
- 100+ rate limit violations in 1 hour
- Database connection failures
- Redis connection failures

**Warning Alerts (Hourly):**
- 5+ failed login attempts from single IP in 1 hour
- 20+ permission denied errors in 1 hour
- High error rate (>5% of requests)

**Info Alerts (Daily):**
- Daily security event summary
- Unusual traffic patterns
- New user registrations spike

### Prometheus Metrics

**Security Metrics:**

```python
# Custom security metrics
from prometheus_client import Counter, Histogram

# Security event counters
failed_login_attempts = Counter(
    'matchhire_failed_login_attempts_total',
    'Total failed login attempts',
    ['reason']
)

permission_denied_errors = Counter(
    'matchhire_permission_denied_total',
    'Total permission denied errors',
    ['resource', 'action']
)

rate_limit_violations = Counter(
    'matchhire_rate_limit_violations_total',
    'Total rate limit violations',
    ['scope', 'type']
)

# Security event histogram
security_event_duration = Histogram(
    'matchhire_security_event_duration_seconds',
    'Time spent processing security events',
    ['event_type']
)
```

**Grafana Dashboard Queries:**

```promql
# Failed login attempts rate
rate(matchhire_failed_login_attempts_total[5m])

# Permission denied errors by resource
sum(rate(matchhire_permission_denied_total[1h])) by (resource)

# Rate limit violations
sum(rate(matchhire_rate_limit_violations_total[1h])) by (scope)

# Top IPs by failed logins
topk(10, sum(rate(matchhire_failed_login_attempts_total[5m])) by (ip))
```

## Alerting Rules

### Prometheus Alert Rules

```yaml
groups:
  - name: security_alerts
    rules:
      - alert: HighFailedLoginRate
        expr: rate(matchhire_failed_login_attempts_total[5m]) > 10
        for: 5m
        labels:
          severity: critical
          team: security
        annotations:
          summary: High rate of failed login attempts
          description: "Failed login rate: {{ $value }} attempts/second"

      - alert: HighPermissionDeniedRate
        expr: rate(matchhire_permission_denied_total[1h]) > 50
        for: 10m
        labels:
          severity: warning
          team: security
        annotations:
          summary: High rate of permission denied errors
          description: "Permission denied rate: {{ $value }} errors/hour"

      - alert: HighRateLimitViolations
        expr: rate(matchhire_rate_limit_violations_total[1h]) > 100
        for: 10m
        labels:
          severity: warning
          team: security
        annotations:
          summary: High rate of rate limit violations
          description: "Rate limit violation rate: {{ $value }} violations/hour"
```

### Sentry Alert Rules

**Critical:**
- Alert on: `FAILED_LOGIN` event count > 10 in 5 minutes
- Alert on: `PERMISSION_DENIED` event count > 50 in 1 hour
- Alert on: `IP_RATE_LIMIT_EXCEEDED` event count > 100 in 1 hour

**Warning:**
- Alert on: `FAILED_LOGIN` event count > 5 in 1 hour
- Alert on: `PERMISSION_DENIED` event count > 20 in 1 hour
- Alert on: Error rate > 5% of total requests

## Log Analysis

### Log Aggregation

**Current Setup:**
- Structured JSON logging in production
- Logs stored in Docker containers (json-file driver)
- Log rotation: 10MB max size, 3 files retained

**Recommended Enhancement:**
- Centralized log aggregation (ELK Stack, Loki, CloudWatch)
- Long-term log retention (30-90 days)
- Log analysis and search capabilities

### Log Search Queries

**Failed Login Analysis:**
```bash
# Find IPs with multiple failed logins
grep "FAILED_LOGIN" /var/log/matchhire/app.log | jq -r '.ip' | sort | uniq -c | sort -rn | head -20

# Find accounts with failed login attempts
grep "FAILED_LOGIN" /var/log/matchhire/app.log | jq -r '.email' | sort | uniq -c | sort -rn | head -20
```

**Permission Denied Analysis:**
```bash
# Find most common permission denied resources
grep "PERMISSION_DENIED" /var/log/matchhire/app.log | jq -r '.resource' | sort | uniq -c | sort -rn

# Find users with permission denied errors
grep "PERMISSION_DENIED" /var/log/matchhire/app.log | jq -r '.user_id' | sort | uniq -c | sort -rn
```

**Rate Limit Analysis:**
```bash
# Find IPs exceeding rate limits
grep "RATE_LIMIT_EXCEEDED" /var/log/matchhire/app.log | jq -r '.ip' | sort | uniq -c | sort -rn

# Find most common rate limit scopes
grep "RATE_LIMIT_EXCEEDED" /var/log/matchhire/app.log | jq -r '.scope' | sort | uniq -c | sort -rn
```

## Incident Response

### Severity Levels

**P1 - Critical:**
- Active attack in progress
- Data breach confirmed
- System compromise suspected
- Response time: < 15 minutes

**P2 - High:**
- Suspicious activity pattern detected
- Multiple failed login attempts from single IP
- Unusual data access patterns
- Response time: < 1 hour

**P3 - Medium:**
- Elevated error rates
- Single security event
- Configuration issue
- Response time: < 4 hours

**P4 - Low:**
- Informational security event
- Routine monitoring alert
- Documentation update needed
- Response time: < 24 hours

### Response Procedures

**P1 - Critical Incident:**
1. Immediate team notification
2. Activate incident response team
3. Isolate affected systems if needed
4. Preserve evidence
5. Begin forensic analysis
6. Communicate with stakeholders
7. Implement containment measures
8. Document all actions

**P2 - High Priority:**
1. Alert on-call engineer
2. Investigate the event
3. Determine scope and impact
4. Implement mitigation if needed
5. Document findings
6. Update monitoring rules

**P3 - Medium Priority:**
1. Create ticket in issue tracker
2. Investigate during business hours
3. Determine if action required
4. Implement fix if needed
5. Document resolution

**P4 - Low Priority:**
1. Log event for review
2. Include in weekly security review
3. Update documentation if needed

## Security Dashboard

### Recommended Dashboard Components

**Overview Panel:**
- Total security events (24h)
- Failed login attempts (24h)
- Permission denied errors (24h)
- Rate limit violations (24h)
- Current threat level

**Authentication Panel:**
- Failed login rate chart
- Top IPs by failed logins
- Successful vs failed login ratio
- Geographic distribution (if available)

**Authorization Panel:**
- Permission denied errors by resource
- Permission denied errors by user
- Authorization failure rate
- Most common denied actions

**Rate Limiting Panel:**
- Rate limit violations by scope
- Top IPs by violations
- Violation rate over time
- Throttle effectiveness

**File Upload Panel:**
- Upload attempts by type
- Rejected uploads by reason
- Upload success rate
- Malicious file detection

### Grafana Dashboard Example

```json
{
  "dashboard": {
    "title": "MatchHire Security Monitoring",
    "panels": [
      {
        "title": "Failed Login Rate",
        "targets": [
          {
            "expr": "rate(matchhire_failed_login_attempts_total[5m])"
          }
        ]
      },
      {
        "title": "Permission Denied Errors",
        "targets": [
          {
            "expr": "sum(rate(matchhire_permission_denied_total[1h])) by (resource)"
          }
        ]
      },
      {
        "title": "Rate Limit Violations",
        "targets": [
          {
            "expr": "sum(rate(matchhire_rate_limit_violations_total[1h])) by (scope)"
          }
        ]
      }
    ]
  }
}
```

## Automated Threat Detection

### Anomaly Detection Rules

**Brute Force Attack Detection:**
```python
# Detect 10+ failed logins from single IP in 5 minutes
def detect_brute_force(ip_address, time_window=300):
    recent_failures = SecurityEvent.objects.filter(
        event_type='FAILED_LOGIN',
        ip_address=ip_address,
        timestamp__gte=timezone.now() - timedelta(seconds=time_window)
    ).count()
    return recent_failures >= 10
```

**Credential Stuffing Detection:**
```python
# Detect failed logins for multiple accounts from single IP
def detect_credential_stuffing(ip_address, time_window=300):
    recent_failures = SecurityEvent.objects.filter(
        event_type='FAILED_LOGIN',
        ip_address=ip_address,
        timestamp__gte=timezone.now() - timedelta(seconds=time_window)
    ).values('email').distinct().count()
    return recent_failures >= 5
```

**Abnormal Access Pattern Detection:**
```python
# Detect unusual access patterns (e.g., accessing many different resources)
def detect_abnormal_access(user_id, time_window=3600):
    recent_access = SecurityEvent.objects.filter(
        event_type__in=['PERMISSION_DENIED', 'API_ACCESS'],
        user_id=user_id,
        timestamp__gte=timezone.now() - timedelta(seconds=time_window)
    ).values('resource').distinct().count()
    return recent_access >= 100
```

## Compliance Monitoring

### GDPR Compliance

**Data Access Logging:**
- Log all PII access events
- Track data export requests
- Monitor data deletion requests
- Audit admin access to user data

**Data Breach Detection:**
- Alert on unusual data export volumes
- Monitor bulk data access
- Track unauthorized data access attempts

### SOC 2 Compliance

**Security Event Logging:**
- Maintain immutable audit logs
- Log all security-relevant events
- Retain logs for minimum 90 days
- Implement log tampering detection

**Access Control Monitoring:**
- Monitor privilege escalation
- Track admin access
- Log permission changes
- Alert on unauthorized access attempts

## Security Reporting

### Daily Security Report

**Contents:**
- Total security events
- Failed login attempts
- Permission denied errors
- Rate limit violations
- New user registrations
- Suspicious activity summary

**Delivery:**
- Email to security team
- Posted to internal Slack channel
- Stored in security dashboard

### Weekly Security Review

**Contents:**
- Security event trends
- New threats identified
- Incidents resolved
- False positive analysis
- Monitoring rule updates
- Recommended improvements

**Delivery:**
- Security team meeting
- Executive summary
- Action items tracking

### Monthly Security Report

**Contents:**
- Security posture assessment
- Incident summary
- Threat landscape analysis
- Compliance status
- Metrics and KPIs
- Improvement roadmap

**Delivery:**
- Executive presentation
- Board report (if required)
- Public summary (if applicable)

## References

- [OWASP Security Logging](https://cheatsheetseries.owasp.org/cheatsheets/Security_Logging_Cheat_Sheet.html)
- [NIST Incident Response Guide](https://csrc.nist.gov/publications/detail/sp-800-61-rev-2/final)
- [Sentry Security Monitoring](https://docs.sentry.io/product/security/)
- [Prometheus Security Monitoring](https://prometheus.io/docs/practices/security/)
