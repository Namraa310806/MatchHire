# Security Policy

## Supported Versions

Currently, only the latest version of MatchHire is supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: Yes |

## Reporting a Vulnerability

If you discover a security vulnerability in MatchHire, please report it responsibly.

### How to Report

**Do not** open a public issue for security vulnerabilities.

Instead, send an email to: [security@example.com]

Please include:
- A description of the vulnerability
- Steps to reproduce the vulnerability
- Any potential impact or exploit scenarios
- If applicable, a suggested fix or mitigation

### What to Expect

- You will receive an acknowledgment within 48 hours
- We will provide a timeline for the fix
- We will coordinate with you on the disclosure timeline
- You will be credited in the security advisory (unless you wish to remain anonymous)

### Disclosure Policy

We follow responsible disclosure practices:

1. **Initial Response**: Acknowledge receipt within 48 hours
2. **Investigation**: Validate and assess the vulnerability within 7 days
3. **Remediation**: Develop and test a fix
4. **Coordination**: Agree on disclosure timeline with reporter
5. **Disclosure**: Publish security advisory and fix

We aim to disclose vulnerabilities within 90 days of initial report, depending on severity and complexity.

## Security Best Practices

### For Deployers

- **Keep Dependencies Updated**: Regularly update Django, DRF, and other dependencies
- **Use Strong Secrets**: Generate cryptographically random SECRET_KEY for production
- **Enable HTTPS**: Always use HTTPS in production
- **Configure CORS Properly**: Only allow trusted origins
- **Review Environment Variables**: Ensure no secrets are committed to version control
- **Regular Backups**: Implement automated database backups
- **Monitor Logs**: Set up log monitoring for suspicious activity
- **Rate Limiting**: Configure appropriate rate limits for your usage patterns

### For Developers

- **Input Validation**: Always validate and sanitize user input
- **SQL Injection Prevention**: Use Django ORM, never raw SQL with user input
- **XSS Prevention**: Use Django's template escaping and DRF serializers
- **CSRF Protection**: Ensure CSRF middleware is enabled
- **Authentication**: Use JWT with httpOnly cookies
- **Authorization**: Implement proper permission checks
- **Secrets Management**: Never commit secrets, use environment variables
- **Dependency Scanning**: Regularly scan dependencies for vulnerabilities

## Security Features

MatchHire includes several security features:

### Authentication

- JWT-based authentication with short-lived access tokens (15 minutes)
- Refresh token rotation to prevent token theft replay attacks
- Token blacklisting after rotation
- httpOnly cookies to prevent XSS token theft
- SameSite=Lax to prevent CSRF attacks
- Secure cookie flag in production

### Authorization

- Role-Based Access Control (RBAC)
- Object-level permissions for resource access
- Custom permission classes for fine-grained control

### API Security

- Rate limiting per endpoint
- Request ID tracking for audit trails
- Input validation via serializers
- SQL injection prevention via ORM
- XSS prevention via DRF serializers

### Infrastructure Security

- Nginx reverse proxy for request filtering
- CORS configuration for cross-origin requests
- Environment-based secrets management
- Security audit functions in `matchhire_backend/core/security_audit.py`
- Startup validation checks in `matchhire_backend/core/startup_checks.py`

## Known Security Considerations

### Current Limitations

1. **No IP-Based Rate Limiting**: Rate limiting is per-user, not per-IP
2. **No Request Signing**: API requests are not signed beyond JWT authentication
3. **No Encrypted Fields**: Sensitive data in database is not encrypted at rest
4. **No 2FA**: Two-factor authentication is not implemented

### Future Enhancements

- Add IP-based rate limiting
- Implement request signing for sensitive operations
- Add field-level encryption for sensitive data
- Implement 2FA for admin accounts
- Add security headers (CSP, HSTS, etc.)
- Implement audit logging for admin actions

## Dependency Security

### Regular Updates

We regularly update dependencies to address security vulnerabilities. Key dependencies:

- Django 5.1.7
- Django REST Framework 3.15.2
- djangorestframework-simplejwt 5.5.0
- psycopg2-binary 2.9.10
- Celery 5.4.0
- Redis 5.2.1

### Vulnerability Scanning

We recommend using tools like:
- `pip-audit` for Python dependency scanning
- `safety` for security vulnerability checking
- GitHub Dependabot for automated dependency updates

## Security Audits

### Internal Audits

MatchHire includes internal security audit functions in `matchhire_backend/core/security_audit.py`. These can be run to verify:

- Configuration security
- Secret strength
- TLS/SSL configuration
- Permission configuration

### External Audits

We welcome external security audits. Contact us at [security@example.com] to discuss.

## Incident Response

In the event of a security incident:

1. **Containment**: Immediately isolate affected systems
2. **Investigation**: Determine scope and impact
3. **Communication**: Notify affected users if data was compromised
4. **Remediation**: Apply fixes and patches
5. **Post-Mortem**: Document lessons learned and improve processes

## Contact

For security-related questions or concerns:
- Email: [security@example.com]
- PGP Key: [PGP key here]

## Resources

- [OWASP Django Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Django_Security_Cheat_Sheet.html)
- [Django Security Documentation](https://docs.djangoproject.com/en/stable/topics/security/)
- [Django REST Framework Security](https://www.django-rest-framework.org/api-guide/throttling/)
