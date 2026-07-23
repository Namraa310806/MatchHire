# Monitoring Guide

## Overview

This guide explains how to monitor the MatchHire platform using the admin console's observability features.

## System Dashboard

### Key Metrics

The System Dashboard provides an at-a-glance view of platform health:

#### Platform KPIs

- **Total Users**: Registered user count
- **Active Jobs**: Currently active job listings
- **Applications**: Total applications submitted
- **Companies**: Registered companies
- **Active Users**: Users active in last 30 days
- **Pending Jobs**: Jobs awaiting approval
- **Interviews**: Scheduled interviews
- **Matches**: Candidate-job matches

#### System Health

Real-time health checks for all system components:
- Database connectivity
- Cache status
- External API integrations
- Background job queues
- File storage

Each check shows:
- Status (healthy, degraded, unhealthy)
- Response time
- Status message

#### Search Platform Metrics

- **Provider**: Search technology (PostgreSQL, Elasticsearch, OpenSearch)
- **Index Status**: Current index health
- **Document Count**: Total indexed documents
- **Query Latency**: p50, p95, p99 response times
- **Cache Hit Ratio**: Percentage of cached queries
- **Total Queries**: Query volume
- **Search Failures**: Failed query count

#### Recommendation Engine Metrics

- **Total Requests**: Recommendation requests made
- **Acceptance Rate**: Percentage of accepted recommendations
- **Avg Confidence**: Average match confidence score
- **Latency**: p50, p95 response times
- **Feedback Count**: Total user feedback
- **Positive/Negative Feedback**: Feedback breakdown

#### System Metrics

- **API Latency**: p50, p95, p99 response times
- **Request Volume**: Total API requests
- **Error Rate**: Percentage of failed requests
- **Cache Hit Ratio**: Cache effectiveness

## Search Platform Monitoring

### Detailed Search Metrics

Navigate to **Search** for detailed search platform monitoring:

#### Provider Information

- Search provider type
- Index status and health
- Document count and growth

#### Performance Metrics

- Query latency percentiles (p50, p95, p99)
- Index latency (time to index new documents)
- Cache hit ratio
- Search failure rate

#### Usage Metrics

- Total query volume
- Top queries by frequency
- Average query latency
- Query patterns and trends

### Search Health Indicators

#### Healthy Indicators

- Query latency < 100ms (p50)
- Cache hit ratio > 80%
- Search failures < 1%
- Index status: healthy

#### Degraded Indicators

- Query latency 100-500ms (p50)
- Cache hit ratio 50-80%
- Search failures 1-5%
- Index status: degraded

#### Unhealthy Indicators

- Query latency > 500ms (p50)
- Cache hit ratio < 50%
- Search failures > 5%
- Index status: unhealthy

### Troubleshooting Search Issues

#### High Query Latency

1. Check index size and document count
2. Review query complexity
3. Verify cache configuration
4. Check server resources

#### Low Cache Hit Ratio

1. Review query patterns
2. Check cache TTL settings
3. Analyze query diversity
4. Consider cache warming

#### High Search Failures

1. Check search provider logs
2. Verify index health
3. Review query syntax
4. Check network connectivity

## Recommendation Engine Monitoring

### Detailed Recommendation Metrics

Navigate to **Recommendations** for detailed monitoring:

#### Overview Metrics

- Total recommendation requests
- Acceptance rate
- Average confidence score

#### Performance Metrics

- Recommendation latency (p50, p95)
- Throughput (requests/second)
- Model inference time

#### Feedback Metrics

- Total feedback count
- Positive feedback percentage
- Negative feedback percentage
- Feedback trends over time

### Recommendation Health Indicators

#### Healthy Indicators

- Acceptance rate > 60%
- Avg confidence > 70%
- Latency < 200ms (p50)
- Positive feedback > 80%

#### Degraded Indicators

- Acceptance rate 40-60%
- Avg confidence 50-70%
- Latency 200-500ms (p50)
- Positive feedback 60-80%

#### Unhealthy Indicators

- Acceptance rate < 40%
- Avg confidence < 50%
- Latency > 500ms (p50)
- Positive feedback < 60%

### Troubleshooting Recommendation Issues

#### Low Acceptance Rate

1. Review recommendation algorithm
2. Analyze user feedback patterns
3. Check match scoring logic
4. Consider model retraining

#### Low Confidence Scores

1. Review data quality
2. Check feature engineering
3. Analyze training data
4. Consider model tuning

#### High Latency

1. Check model complexity
2. Review infrastructure resources
3. Optimize inference pipeline
4. Consider model caching

## Observability Monitoring

### Detailed System Metrics

Navigate to **Observability** for comprehensive system monitoring:

#### API Performance

- API latency percentiles (p50, p95, p99)
- Request volume over time
- Error rate by endpoint
- Response time distribution

#### Cache Performance

- Cache hit ratio
- Cache size
- Eviction rate
- Cache effectiveness by endpoint

#### Queue Status

- Queue size for each queue
- Processing jobs count
- Failed jobs count
- Queue age distribution

#### Background Jobs

- Job status (running, idle, failed)
- Last run time
- Next scheduled run
- Job duration

#### Service Health

- Service status (healthy, degraded, unhealthy)
- Uptime percentage
- Last check timestamp
- Response times

### System Health Indicators

#### Healthy Indicators

- API latency < 100ms (p50)
- Error rate < 1%
- Cache hit ratio > 80%
- All services healthy
- No failed jobs

#### Degraded Indicators

- API latency 100-300ms (p50)
- Error rate 1-5%
- Cache hit ratio 60-80%
- Some services degraded
- Minimal job failures

#### Unhealthy Indicators

- API latency > 300ms (p50)
- Error rate > 5%
- Cache hit ratio < 60%
- Services unhealthy
- Multiple job failures

### Troubleshooting System Issues

#### High API Latency

1. Check database query performance
2. Review external API calls
3. Analyze slow endpoints
4. Check server resources

#### High Error Rate

1. Review error logs
2. Check database connectivity
3. Verify external integrations
4. Analyze error patterns

#### Low Cache Hit Ratio

1. Review cache strategy
2. Check cache configuration
3. Analyze access patterns
4. Consider cache warming

#### Queue Backlog

1. Check worker availability
2. Review job processing time
3. Analyze job failure patterns
4. Scale workers if needed

#### Background Job Failures

1. Review job logs
2. Check error messages
3. Verify job dependencies
4. Restart failed jobs

## Security Monitoring

### Security Event Monitoring

Navigate to **Security** to monitor security events:

#### Event Types

- **Login Success**: Successful user logins
- **Login Failure**: Failed login attempts
- **Account Locked**: Account lockouts
- **Permission Changed**: Permission modifications
- **Role Changed**: Role modifications

#### Severity Levels

- **Low**: Normal security events
- **Medium**: Potentially suspicious activity
- **High**: Clear security concerns
- **Critical**: Immediate action required

### Login Activity Monitoring

#### Metrics Tracked

- Total login count per user
- Failed login attempts
- Last login timestamp
- Current session IP address
- Last failed login timestamp

#### Security Indicators

#### Normal Activity

- Failed attempts < 5 per user
- Consistent login patterns
- Known IP addresses
- Regular login intervals

#### Suspicious Activity

- Failed attempts > 10 per user
- Unusual login patterns
- Unknown IP addresses
- Rapid successive attempts

#### Critical Activity

- Failed attempts > 20 per user
- Multiple account lockouts
- Geographic anomalies
- Brute force patterns

### Security Incident Response

#### Immediate Actions

1. Lock affected accounts
2. Review audit logs
3. Check for data breaches
4. Notify security team

#### Investigation Steps

1. Review security events timeline
2. Analyze login patterns
3. Check IP geolocation
4. Review user activity

#### Recovery Steps

1. Reset compromised credentials
2. Enable additional authentication
3. Monitor for continued activity
4. Document the incident

## Alerting and Notifications

### Recommended Alert Thresholds

#### Critical Alerts

- API latency > 500ms (p50)
- Error rate > 5%
- Search failures > 5%
- System status: unhealthy
- Security events: critical

#### Warning Alerts

- API latency > 300ms (p50)
- Error rate > 2%
- Search failures > 2%
- System status: degraded
- Security events: high

#### Info Alerts

- API latency > 200ms (p50)
- Error rate > 1%
- Cache hit ratio < 70%
- Queue backlog > 100
- Job failures > 5%

### Monitoring Schedule

#### Continuous Monitoring

- System health status
- API error rate
- Security events (critical)

#### Hourly Monitoring

- API latency
- Request volume
- Cache performance
- Queue status

#### Daily Monitoring

- Search platform metrics
- Recommendation metrics
- Background job status
- Login activity

#### Weekly Monitoring

- Platform KPIs trends
- User growth metrics
- Job posting trends
- Application volume

## Performance Optimization

### Search Optimization

1. **Index Optimization**
   - Regular index maintenance
   - Remove stale documents
   - Optimize index mappings

2. **Query Optimization**
   - Review slow queries
   - Optimize query syntax
   - Use appropriate filters

3. **Cache Optimization**
   - Increase cache size
   - Adjust TTL settings
   - Implement query caching

### Recommendation Optimization

1. **Model Optimization**
   - Regular model retraining
   - Feature engineering
   - Hyperparameter tuning

2. **Infrastructure Optimization**
   - Scale compute resources
   - Optimize inference pipeline
   - Implement model caching

### System Optimization

1. **API Optimization**
   - Implement response caching
   - Optimize database queries
   - Use connection pooling

2. **Infrastructure Optimization**
   - Scale horizontally
   - Load balancing
   - CDN implementation

## Reporting

### Daily Reports

- System health summary
- Critical security events
- API performance summary
- Error rate summary

### Weekly Reports

- Platform KPIs trends
- User growth metrics
- Job posting statistics
- Application volume trends

### Monthly Reports

- Comprehensive performance review
- Security incident summary
- Capacity planning analysis
- Optimization recommendations

## Best Practices

### Monitoring

1. Set up appropriate alert thresholds
2. Review metrics regularly
3. Investigate anomalies promptly
4. Maintain monitoring documentation

### Incident Response

1. Have clear escalation procedures
2. Document all incidents
3. Conduct post-incident reviews
4. Implement preventive measures

### Performance

1. Establish performance baselines
2. Monitor trends over time
3. Proactively optimize
4. Plan for capacity growth

### Security

1. Monitor security events continuously
2. Respond to incidents quickly
3. Maintain security documentation
4. Regular security audits
