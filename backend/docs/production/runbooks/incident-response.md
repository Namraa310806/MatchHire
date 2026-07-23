# Incident Response Playbook

## Overview

This playbook provides procedures for responding to production incidents affecting the MatchHire backend.

## Severity Levels

### P0 - Critical
- Complete service outage
- Data loss or corruption
- Security breach
- Impact to all users

### P1 - High
- Major functionality broken
- Significant performance degradation
- Partial service outage

### P2 - Medium
- Minor functionality broken
- Performance issues
- Limited user impact

### P3 - Low
- Cosmetic issues
- Documentation errors
- Very limited impact

## Incident Response Process

### 1. Detection and Identification

**Time: 0-5 minutes**

- Monitor alerts (Sentry, Prometheus, logs)
- Identify affected systems
- Determine severity level
- Declare incident

**Commands:**
```bash
# Check system health
curl http://localhost:8000/health/

# Check error rates
# (via Prometheus/Grafana)

# Check recent logs
docker-compose -f docker-compose.production.yml logs --tail=100 backend
```

### 2. Communication

**Time: 5-10 minutes**

- Notify on-call engineer
- Post to incident channel
- Update status page
- Notify stakeholders if P0/P1

**Template:**
```
🚨 INCIDENT DECLARED

Severity: P0/P1/P2/P3
Service: MatchHire Backend
Impact: [brief description]
Started: [timestamp]
Investigator: [name]
```

### 3. Investigation

**Time: 10-30 minutes**

- Review logs and metrics
- Identify root cause
- Assess impact scope
- Determine workaround if possible

**Investigation Commands:**
```bash
# Check service status
docker-compose -f docker-compose.production.yml ps

# Check resource usage
docker stats

# Check database connections
docker-compose -f docker-compose.production.yml exec postgres psql -U matchhire -d matchhire -c "SELECT count(*) FROM pg_stat_activity;"

# Check Redis
docker-compose -f docker-compose.production.yml exec redis redis-cli info

# Check Elasticsearch
curl http://localhost:9200/_cluster/health
```

### 4. Mitigation

**Time: 30-60 minutes**

- Implement temporary fix
- Restore service if possible
- Apply feature flags to disable affected features
- Scale resources if needed

**Mitigation Actions:**
```bash
# Restart affected service
docker-compose -f docker-compose.production.yml restart backend

# Scale up
docker-compose -f docker-compose.production.yml up -d --scale backend=4

# Disable feature flag
# (via admin API or database)

# Clear cache
docker-compose -f docker-compose.production.yml exec redis redis-cli FLUSHALL
```

### 5. Resolution

**Time: 60-120 minutes**

- Implement permanent fix
- Deploy fix to production
- Verify service recovery
- Monitor for recurrence

### 6. Post-Incident Review

**Time: 1-2 days**

- Document incident timeline
- Identify root cause
- Create action items
- Update runbooks
- Schedule follow-up meeting

## Common Incident Scenarios

### Database Outage

**Symptoms:**
- Database connection errors
- Slow queries
- Timeouts

**Response:**
1. Check database health
2. Check connection pool
3. Restart database if needed
4. Scale database resources
5. Enable read replicas if available

**Commands:**
```bash
# Check database
docker-compose -f docker-compose.production.yml ps postgres
docker-compose -f docker-compose.production.yml logs postgres

# Restart database
docker-compose -f docker-compose.production.yml restart postgres

# Check connections
docker-compose -f docker-compose.production.yml exec postgres psql -U matchhire -d matchhire -c "SELECT * FROM pg_stat_activity;"
```

### Cache Failure

**Symptoms:**
- Cache errors
- Increased database load
- Slower response times

**Response:**
1. Check Redis health
2. Restart Redis if needed
3. Clear corrupted cache
4. Enable cache bypass if needed

**Commands:**
```bash
# Check Redis
docker-compose -f docker-compose.production.yml ps redis
docker-compose -f docker-compose.production.yml logs redis

# Test Redis
docker-compose -f docker-compose.production.yml exec redis redis-cli ping

# Restart Redis
docker-compose -f docker-compose.production.yml restart redis

# Clear cache
docker-compose -f docker-compose.production.yml exec redis redis-cli FLUSHALL
```

### Search Service Failure

**Symptoms:**
- Search errors
- No search results
- Slow search performance

**Response:**
1. Check Elasticsearch health
2. Restart Elasticsearch if needed
3. Enable fallback to database search
4. Reindex if needed

**Commands:**
```bash
# Check Elasticsearch
curl http://localhost:9200/_cluster/health

# Restart Elasticsearch
docker-compose -f docker-compose.production.yml restart elasticsearch

# Enable fallback
# (via feature flag)
```

### High CPU/Memory Usage

**Symptoms:**
- Slow response times
- Timeouts
- System alerts

**Response:**
1. Identify consuming process
2. Check for memory leaks
3. Scale horizontally
4. Restart affected services

**Commands:**
```bash
# Check resource usage
docker stats

# Scale services
docker-compose -f docker-compose.production.yml up -d --scale backend=4 --scale celery-worker=4

# Restart service
docker-compose -f docker-compose.production.yml restart backend
```

### API Rate Limiting Issues

**Symptoms:**
- 429 errors
- Users blocked
- Legitimate traffic rejected

**Response:**
1. Check rate limit configuration
2. Adjust limits if needed
3. Clear rate limit counters
4. Whitelist legitimate users

**Commands:**
```bash
# Check Redis rate limit keys
docker-compose -f docker-compose.production.yml exec redis redis-cli KEYS "ratelimit:*"

# Clear specific user limit
docker-compose -f docker-compose.production.yml exec redis redis-cli DEL "ratelimit:user:<user_id>"
```

## Escalation Matrix

| Severity | Response Time | Escalation |
|----------|---------------|------------|
| P0 | 15 minutes | Executive, CTO |
| P1 | 30 minutes | Engineering Lead |
| P2 | 1 hour | Team Lead |
| P3 | 4 hours | On-call Engineer |

## Communication Channels

- **Incident Channel:** #incidents
- **Status Page:** status.matchhire.com
- **Stakeholder Email:** incidents@matchhire.com

## After-Action Report Template

```markdown
# Incident Report: [Title]

## Summary
[Brief description]

## Timeline
- [Time]: Incident detected
- [Time]: Incident declared
- [Time]: Mitigation implemented
- [Time]: Resolution complete

## Impact
- Users affected: [number]
- Duration: [time]
- Revenue impact: [if applicable]

## Root Cause
[Description of root cause]

## Resolution
[Description of fix]

## Action Items
- [ ] [Action item 1]
- [ ] [Action item 2]

## Lessons Learned
[What went well, what could be improved]
```

## Emergency Contacts

- On-Call Engineer: [contact]
- Engineering Lead: [contact]
- CTO: [contact]
- DevOps: [contact]
