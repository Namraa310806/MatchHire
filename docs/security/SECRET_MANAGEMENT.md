# Secret Management Guide

## Overview

This guide covers secret management practices for the MatchHire backend production deployment.

## Principles

1. **Never commit secrets to version control**
2. **Use environment variables for all sensitive configuration**
3. **Rotate secrets regularly**
4. **Use strong, randomly generated secrets**
5. **Limit secret access to necessary services only**

## Required Secrets

### Django SECRET_KEY

**Purpose:** Cryptographic signing for sessions, CSRF tokens, password reset tokens

**Generation:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

**Rotation:** Every 90 days

**Storage:** Environment variable `SECRET_KEY`

### Database Credentials

**Purpose:** PostgreSQL database access

**Variables:**
- `DB_NAME`: Database name
- `DB_USER`: Database user
- `DB_PASSWORD`: Database password
- `DB_HOST`: Database host
- `DB_PORT`: Database port

**Generation:**
```bash
# Generate strong password (32 characters)
openssl rand -base64 32
```

**Rotation:** Every 180 days

**Storage:** Environment variables or Docker secrets

### Redis Credentials

**Purpose:** Redis cache and Celery broker

**Variables:**
- `REDIS_URL`: Redis connection URL
- `CELERY_BROKER_URL`: Celery broker URL
- `CELERY_RESULT_BACKEND`: Celery result backend URL

**Rotation:** Every 180 days

**Storage:** Environment variables or Docker secrets

### Sentry DSN

**Purpose:** Error monitoring and performance tracking

**Variable:** `SENTRY_DSN`

**Rotation:** Not required (can be rotated if compromised)

**Storage:** Environment variable

## Docker Secrets Integration

For production deployments using Docker Swarm or Kubernetes, use Docker secrets instead of environment variables.

### Docker Swarm Example

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  web:
    image: matchhire-backend:latest
    secrets:
      - django_secret_key
      - db_password
      - redis_url
    environment:
      SECRET_KEY_FILE: /run/secrets/django_secret_key
      DB_PASSWORD_FILE: /run/secrets/db_password
      REDIS_URL_FILE: /run/secrets/redis_url

secrets:
  django_secret_key:
    external: true
  db_password:
    external: true
  redis_url:
    external: true
```

### Creating Docker Secrets

```bash
# Create secret
echo "your-secret-value" | docker secret create django_secret_key -

# List secrets
docker secret ls

# Remove secret
docker secret rm django_secret_key
```

### Kubernetes Secrets Example

```yaml
# k8s-secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: matchhire-secrets
type: Opaque
stringData:
  SECRET_KEY: "your-secret-key"
  DB_PASSWORD: "your-db-password"
  REDIS_URL: "redis://:password@redis:6379/0"
```

## Secret Rotation Procedures

### Django SECRET_KEY Rotation

1. **Generate new secret key:**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(50))"
   ```

2. **Update environment variable:**
   - Update `.env` file or Docker secret
   - Redeploy application

3. **Verify:** Test authentication and session functionality

4. **Retire old key:** After 7 days, remove old key from backups

### Database Password Rotation

1. **Generate new password:**
   ```bash
   openssl rand -base64 32
   ```

2. **Update database password:**
   ```sql
   ALTER USER matchhire WITH PASSWORD 'new-password';
   ```

3. **Update environment variable:**
   - Update `DB_PASSWORD` in `.env` or Docker secret
   - Redeploy application

4. **Verify:** Test database connectivity

5. **Retire old password:** After 7 days, remove from backups

### Redis Password Rotation

1. **Update Redis configuration:**
   ```bash
   # In redis.conf
   requirepass new-password
   ```

2. **Restart Redis:**
   ```bash
   docker-compose restart redis
   ```

3. **Update environment variable:**
   - Update `REDIS_URL` in `.env` or Docker secret
   - Redeploy application

4. **Verify:** Test Redis connectivity

## Secret Management Services

For enhanced security, consider using a dedicated secret management service:

### AWS Secrets Manager

```python
import boto3
import json

client = boto3.client('secretsmanager')

# Get secret
response = client.get_secret_value(SecretId='matchhire/production')
secret = json.loads(response['SecretString'])

# Use secret
SECRET_KEY = secret['django_secret_key']
```

### HashiCorp Vault

```python
import hvac

client = hvac.Client(url='https://vault.example.com')
client.auth.approle.login(role_id='...', secret_id='...')

# Get secret
secret = client.secrets.kv.v2.read_secret_version(path='matchhire/production')
SECRET_KEY = secret['data']['data']['django_secret_key']
```

## Environment Variable Setup

### Development

```bash
# Copy example file
cp .env.example .env

# Edit with your values
nano .env
```

### Production

```bash
# Set environment variables directly
export SECRET_KEY="your-secret-key"
export DB_PASSWORD="your-db-password"

# Or use .env file
cp .env.example .env.production
nano .env.production
```

## Secret Audit Trail

Maintain a log of secret rotations:

| Date | Secret | Rotated By | Reason |
|------|--------|------------|--------|
| 2026-01-15 | SECRET_KEY | admin | Scheduled rotation |
| 2026-01-15 | DB_PASSWORD | admin | Scheduled rotation |
| 2026-04-15 | SECRET_KEY | admin | Scheduled rotation |

## Security Best Practices

1. **Never log secrets:** Ensure secrets are not logged in application logs
2. **Use read-only secrets:** Where possible, use read-only database credentials
3. **Limit secret scope:** Each service should only have access to secrets it needs
4. **Encrypt secrets at rest:** Use encryption for secrets stored in databases
5. **Monitor secret access:** Log and alert on secret access attempts
6. **Use short-lived secrets:** Where possible, use short-lived tokens (e.g., JWT)
7. **Revoke compromised secrets immediately:** If a secret is leaked, rotate immediately

## Emergency Procedures

### Compromised SECRET_KEY

1. **Immediate:** Generate new SECRET_KEY
2. **Update:** Update environment variable and redeploy
3. **Invalidate:** All user sessions will be invalidated (users must re-login)
4. **Communicate:** Notify users of required re-login
5. **Investigate:** Determine how the secret was compromised

### Compromised Database Password

1. **Immediate:** Generate new database password
2. **Update:** Update database password and environment variable
3. **Redeploy:** Restart application with new credentials
4. **Audit:** Review database access logs
5. **Investigate:** Determine how the password was compromised

## Compliance Considerations

- **SOC 2:** Maintain secret rotation logs and audit trails
- **GDPR:** Ensure secrets are not used to store PII
- **PCI DSS:** If processing payments, follow PCI secret management requirements

## References

- [Django Security Settings](https://docs.djangoproject.com/en/5.1/ref/settings/#security)
- [OWASP Secret Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [Docker Secrets](https://docs.docker.com/engine/swarm/secrets/)
- [Kubernetes Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)
