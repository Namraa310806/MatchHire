# Admin Console Operations Guide

## Getting Started

### Prerequisites

- Admin role in MatchHire
- Valid JWT token
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Stable internet connection

### Access

Navigate to `/admin` in your MatchHire instance. You'll be redirected to login if not authenticated.

## Dashboard Navigation

### Main Navigation

The admin console uses a tab-based navigation:

- **Dashboard**: System health and platform KPIs
- **Users**: User management and moderation
- **Jobs**: Job administration and moderation
- **Applications**: Application monitoring
- **Resumes**: Resume administration
- **Search**: Search platform monitoring
- **Recommendations**: Recommendation engine monitoring
- **Config**: System configuration (read-only)

### Keyboard Navigation

- Use Tab to navigate between tabs
- Use Enter to select a tab
- Use Escape to close dialogs

## System Dashboard

### Overview

The system dashboard provides an at-a-glance view of platform health and performance.

### Key Metrics

**Platform KPIs**:
- Total Users: Registered user count
- Active Jobs: Currently active job listings
- Applications: Total applications submitted
- Companies: Registered companies

**Secondary KPIs**:
- Active Users: Users active in last 30 days
- Pending Jobs: Jobs awaiting approval
- Interviews: Scheduled interviews
- Matches: Candidate-job matches

### Health Status

Real-time health checks for:
- Database connectivity
- Cache status
- Disk space
- Memory usage
- CPU usage
- Elasticsearch (if configured)

**Status Indicators**:
- 🟢 Healthy: All systems operational
- 🟡 Degraded: Some issues detected
- 🔴 Unhealthy: Critical issues

### Search Platform

Monitor search provider performance:
- Provider type (PostgreSQL, Elasticsearch)
- Index status
- Document count
- Query latency (p50, p95, p99)
- Cache hit ratio
- Total queries
- Search failures

### Recommendation Engine

Track recommendation performance:
- Total requests
- Acceptance rate
- Average confidence
- Latency metrics
- Feedback analysis

### System Metrics

Overall system observability:
- API latency (p50, p95, p99)
- Request volume
- Error rate
- Cache hit ratio

## User Management

### Viewing Users

1. Navigate to **Users** tab
2. Use search to find users by name or email
3. Filter by role (Admin, Recruiter, Candidate)
4. Filter by status (Active, Suspended)
5. View user details in the table

### User Actions

**Suspend User**:
1. Click the suspend icon (❌) next to user
2. Provide a reason for suspension
3. Confirm action

**Activate User**:
1. Click the activate icon (✓) next to suspended user
2. Provide a reason for activation
3. Confirm action

**Change Role**:
1. Click the role icon (👑) next to user
2. Select new role (Candidate, Recruiter, Admin)
3. Provide a reason for change
4. Confirm action

### Best Practices

- Always provide clear reasons for administrative actions
- Review user activity before suspending
- Use role changes judiciously
- Document reasons for audit trail

## Job Administration

### Viewing Jobs

1. Navigate to **Jobs** tab
2. Use search to find jobs by title or company
3. Filter by status (Draft, Active, Closed, Archived)
4. View job details in the table

### Job Actions

**Approve Job**:
1. Click the approve icon (✓) next to draft job
2. Provide a reason for approval
3. Confirm action

**Close Job**:
1. Click the close icon (❌) next to active job
2. Provide a reason for closure
3. Confirm action

**Archive Job**:
1. Click the archive icon (📦) next to job
2. Provide a reason for archival
3. Confirm action

### Best Practices

- Review job content before approval
- Close jobs that are no longer relevant
- Archive old jobs to keep platform clean
- Communicate job status changes to recruiters

## Application Administration

### Viewing Applications

1. Navigate to **Applications** tab
2. Filter by status (Submitted, Under Review, Shortlisted, Rejected, Hired)
3. View application details in the table

### Application Details

Each application shows:
- Candidate name and email
- Job title and company
- Recruiter email
- Application status
- Application date

### Best Practices

- Monitor application volumes
- Track rejection rates
- Identify hiring bottlenecks
- Review recruiter activity

## Resume Administration

### Viewing Resumes

1. Navigate to **Resumes** tab
2. Filter by parsing status (Parsed, Not Parsed)
3. Filter by structured data status (Structured, Not Structured)
4. View resume details in the table

### Resume Actions

**Suspend Resume**:
1. Click the suspend icon (❌) next to resume
2. This deactivates the associated user account
3. Provide a reason
4. Confirm action

**Activate Resume**:
1. Click the activate icon (✓) next to suspended resume
2. This reactivates the associated user account
3. Provide a reason
4. Confirm action

### Best Practices

- Monitor parsing success rates
- Identify parsing failures
- Review structured data quality
- Handle resume suspensions carefully

## Search Monitoring

### Overview

Monitor search platform performance and identify issues.

### Key Metrics

**Provider Information**:
- Provider type
- Index status
- Document count

**Performance**:
- Query latency (p50, p95, p99)
- Index latency (p50)
- Cache hit ratio

**Usage**:
- Total queries
- Search failures
- Top queries

### Troubleshooting

**High Latency**:
- Check index status
- Review query complexity
- Verify cache configuration

**High Failures**:
- Check provider connectivity
- Review error logs
- Verify index health

**Low Cache Hit Ratio**:
- Review cache configuration
- Check query patterns
- Consider cache warming

## Recommendation Monitoring

### Overview

Track recommendation engine performance and user acceptance.

### Key Metrics

**Overview**:
- Total requests
- Acceptance rate
- Average confidence

**Performance**:
- Latency (p50, p95)

**Feedback**:
- Total feedback
- Positive feedback
- Negative feedback

### Troubleshooting

**Low Acceptance Rate**:
- Review confidence thresholds
- Check recommendation quality
- Analyze user feedback

**High Latency**:
- Check model performance
- Review caching strategy
- Optimize computation

## System Configuration

### Overview

View system configuration (read-only).

### Configuration Sections

**Environment**:
- Environment name
- Version
- Deploy time
- Git commit

**General Settings**:
- Site name
- Site URL
- Support email
- Upload limits
- Allowed file types

**Email Configuration**:
- Provider
- SMTP settings
- TLS configuration

**Storage Configuration**:
- Provider type
- Bucket settings
- CDN configuration

**Search Configuration**:
- Provider
- Index settings
- Fuzziness

**Recommendation Configuration**:
- Enabled status
- Strategy
- Thresholds

**Analytics Configuration**:
- Enabled status
- Provider
- Tracking ID

**Maintenance Mode**:
- Status
- Message
- Scheduled maintenance

### Best Practices

- Review configuration regularly
- Monitor maintenance mode status
- Keep configuration documented
- Plan maintenance windows

## Troubleshooting

### Common Issues

**Dashboard Not Loading**:
- Check internet connection
- Verify JWT token validity
- Clear browser cache
- Check backend health

**Data Not Refreshing**:
- Click Refresh button
- Check auto-refresh settings
- Verify backend connectivity
- Review browser console for errors

**Actions Failing**:
- Verify admin permissions
- Check reason field is filled
- Review error messages
- Check backend logs

### Error Messages

**403 Forbidden**: Insufficient permissions
**404 Not Found**: Resource not available
**500 Server Error**: Backend issue
**Network Error**: Connectivity problem

## Security Best Practices

### Access Control

- Never share admin credentials
- Use strong passwords
- Enable 2FA if available
- Log out after sessions

### Data Protection

- Don't download sensitive data
- Use secure connections (HTTPS)
- Report security issues
- Follow data retention policies

### Audit Trail

- All actions are logged
- Reasons are required for actions
- Logs include timestamp and actor
- Review audit logs regularly

## Performance Tips

### Dashboard Performance

- Use filters to reduce data
- Close unused tabs
- Limit concurrent operations
- Use modern browsers

### Browser Recommendations

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### Network Requirements

- Stable internet connection
- Minimum 1 Mbps download
- Low latency (<100ms)

## Support

### Getting Help

- Check documentation
- Review error messages
- Contact support team
- Check backend logs

### Reporting Issues

Include:
- Browser and version
- Steps to reproduce
- Error messages
- Screenshots if applicable

## Training Resources

### Documentation

- Admin Console README
- Architecture documentation
- API documentation
- Backend documentation

### Best Practices

- Review this guide regularly
- Follow security guidelines
- Attend training sessions
- Share knowledge with team
