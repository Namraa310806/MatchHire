# Deployment Checklist

## Pre-Deployment

### Code Review
- [ ] All code reviewed and approved
- [ ] No TODO or FIXME comments in production code
- [ ] Security review completed
- [ ] Performance review completed
- [ ] Documentation updated

### Testing
- [ ] Unit tests passing (100% coverage target)
- [ ] Integration tests passing
- [ ] End-to-end tests passing
- [ ] Load tests completed and passed
- [ ] Security tests passed
- [ ] Manual QA completed

### Configuration
- [ ] Environment variables configured
- [ ] Secrets rotated if needed
- [ ] Feature flags configured
- [ ] Database migrations prepared
- [ ] Cache invalidation plan ready

### Backup
- [ ] Database backup created
- [ ] Elasticsearch snapshot created
- [ ] Configuration backup created
- [ ] Rollback plan documented

## Deployment

### Database
- [ ] Run migrations in staging
- [ ] Verify migration results
- [ ] Run migrations in production
- [ ] Verify production migration
- [ ] Update application schema

### Application
- [ ] Build new Docker image
- [ ] Push to registry
- [ ] Update deployment configuration
- [ ] Deploy to canary (10% traffic)
- [ ] Monitor canary for 15 minutes
- [ ] Deploy to remaining instances

### Cache
- [ ] Warm up critical cache keys
- [ ] Verify cache connectivity
- [ ] Monitor cache hit rate

### Monitoring
- [ ] Verify monitoring dashboards
- [ ] Check alerting configuration
- [ ] Enable enhanced monitoring during deployment
- [ ] Set up deployment-specific alerts

## Post-Deployment

### Verification
- [ ] Health checks passing
- [ ] Smoke tests passing
- [ ] Key user journeys tested
- [ ] Error rates within normal range
- [ ] Performance metrics within SLA

### Monitoring
- [ ] Monitor error rates for 1 hour
- [ ] Monitor response times for 1 hour
- [ ] Monitor database performance
- [ ] Monitor cache performance
- [ ] Check for memory leaks

### Documentation
- [ ] Update deployment log
- [ ] Document any issues
- [ ] Update runbooks if needed
- [ ] Communicate to stakeholders

### Cleanup
- [ ] Remove old Docker images
- [ ] Clean up temporary files
- [ ] Disable enhanced monitoring
- [ ] Archive deployment artifacts

## Rollback Triggers

Rollback immediately if:
- Error rate > 5%
- Response time > 2s
- Health checks failing
- Database errors increasing
- Memory usage > 90%
- Any critical functionality broken

## Rollback Procedure

1. Stop new deployment
2. Revert to previous Docker image
3. Run rollback migrations if needed
4. Restore cache from backup if needed
5. Verify health checks
6. Monitor for 30 minutes
7. Document rollback reason
