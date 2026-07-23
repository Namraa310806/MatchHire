# Admin Workflow Guide

## Overview

This guide describes the typical workflows and procedures for using the MatchHire Admin Console.

## User Management Workflow

### Viewing Users

1. Navigate to **Users** from the sidebar
2. Use the search bar to find users by name or email
3. Filter by role (admin, recruiter, candidate)
4. Filter by status (active, suspended)

### Managing Users

#### Suspend User

1. Click the suspend icon (red X) next to the user
2. Provide a reason for suspension
3. Confirm the action
4. User loses access to the platform immediately

#### Activate User

1. Click the activate icon (green check) next to suspended user
2. Provide a reason for activation
3. Confirm the action
4. User regains access to the platform

#### Change User Role

1. Click the role change icon (crown) next to the user
2. Select the new role from the dropdown
3. Provide a reason for the change
4. Confirm the action
5. User permissions are updated immediately

## Company Management Workflow

### Viewing Companies

1. Navigate to **Companies** from the sidebar
2. Use search to find companies by name or website
3. Filter by status (pending, approved, rejected, suspended)
4. View recruiter count and job count for each company

### Company Approval Workflow

#### Approve Company

1. Navigate to **Companies** and filter by "Pending"
2. Review company details (name, website, industry)
3. Click the approve icon (green check)
4. Provide approval reason
5. Confirm the action
6. Company can now post jobs on the platform

#### Reject Company

1. Click the reject icon (red X) next to pending company
2. Provide rejection reason
3. Confirm the action
4. Company cannot operate on the platform

#### Suspend Company

1. Click the suspend icon (ban) next to approved company
4. Provide suspension reason
5. Confirm the action
6. All company jobs are hidden from the platform

## Job Administration Workflow

### Viewing Jobs

1. Navigate to **Jobs** from the sidebar
2. Search by job title or company name
3. Filter by status (draft, active, closed, archived)
4. View application count for each job

### Job Moderation Workflow

#### Approve Job

1. Navigate to **Jobs** and filter by "Draft"
2. Review job details (title, company, recruiter)
3. Click the approve icon (green check)
4. Provide approval reason
5. Confirm the action
6. Job becomes visible to candidates

#### Close Job

1. Click the close icon (X) next to active job
2. Provide closure reason
3. Confirm the action
4. Job no longer accepts new applications

#### Archive Job

1. Click the archive icon (archive) next to active or closed job
2. Provide archival reason
3. Confirm the action
4. Job is hidden from the platform but retained for records

## Application Administration Workflow

### Viewing Applications

1. Navigate to **Applications** from the sidebar
2. Filter by status (submitted, under review, shortlisted, rejected, hired)
3. View candidate, job, company, and recruiter information
4. Track application timeline

### Application Monitoring

- Monitor application volume by status
- Identify bottlenecks in the hiring process
- Track time-to-hire metrics
- Review application quality

## Resume Administration Workflow

### Viewing Resumes

1. Navigate to **Resumes** from the sidebar
2. Filter by parsing status (parsed, not parsed)
3. Filter by structured data status (structured, not structured)
4. View candidate information and file details

### Resume Management

#### Suspend Resume

1. Click the suspend icon (red X) next to resume
2. Provide suspension reason
3. Confirm the action
4. Associated user account is deactivated

#### Activate Resume

1. Click the activate icon (green check) next to suspended resume
2. Provide activation reason
3. Confirm the action
4. Associated user account is reactivated

## System Monitoring Workflow

### Dashboard Monitoring

1. Navigate to **Dashboard** from the sidebar
2. Review platform KPIs (users, jobs, applications, companies)
3. Check system health status
4. Monitor search and recommendation metrics
5. Review system performance metrics

### Health Checks

- Monitor individual component health
- Check response times for each service
- Identify degraded or unhealthy services
- Track uptime and availability

### Search Platform Monitoring

1. Navigate to **Search** from the sidebar
2. Review search provider status
3. Monitor query latency (p50, p95, p99)
4. Check cache hit ratio
5. Review top queries and search failures

### Recommendation Engine Monitoring

1. Navigate to **Recommendations** from the sidebar
2. Monitor total recommendation requests
3. Track acceptance rate
4. Review recommendation confidence scores
5. Analyze feedback (positive/negative)

### Observability Monitoring

1. Navigate to **Observability** from the sidebar
2. Monitor API latency (p50, p95, p99)
3. Track request volume
4. Monitor error rate
5. Review cache performance
6. Check queue status
7. Monitor background jobs
8. Review service health

## Security Workflow

### Security Event Monitoring

1. Navigate to **Security** from the sidebar
2. Review recent security events
3. Filter by severity (low, medium, high, critical)
4. Investigate suspicious activity
5. Take appropriate action

### Login Activity Monitoring

1. Review login activity for all users
2. Monitor failed login attempts
3. Track active sessions
4. Identify unusual login patterns
5. Investigate potential security threats

### Audit Log Review

1. Navigate to **Audit Logs** from the sidebar
2. Filter by action type
3. Filter by actor (user, admin, system)
4. Filter by resource type
5. Review administrative actions
6. Track changes to sensitive data

## Feature Flag Management

### Viewing Feature Flags

1. Navigate to **Feature Flags** from the sidebar
2. View all feature flags across environments
3. Check flag status (enabled/disabled)
4. Review flag descriptions

### Managing Feature Flags

1. Click the toggle icon next to a flag
2. Flag status is updated immediately
3. Changes are logged in audit trail
4. Monitor impact of flag changes

## System Configuration

### Viewing Configuration

1. Navigate to **Settings** from the sidebar
2. Review environment information
3. Check general settings
4. Review email configuration
5. Check storage configuration
6. Review search and recommendation settings
7. Monitor maintenance mode status

### Configuration Notes

- Most configuration is read-only for security
- Changes require backend access
- Configuration changes are logged
- Maintenance mode affects all users

## Best Practices

### User Management

- Always provide clear reasons for administrative actions
- Review user activity before suspending accounts
- Document role changes for audit purposes
- Communicate with users before significant changes

### Company Management

- Verify company information before approval
- Monitor company activity after approval
- Provide constructive feedback for rejections
- Consider company history before suspension

### Job Moderation

- Review job content for compliance
- Ensure job descriptions are appropriate
- Monitor job posting patterns
- Track job performance metrics

### System Monitoring

- Check dashboard regularly
- Set up alerts for critical metrics
- Investigate anomalies promptly
- Document system incidents

### Security

- Review security events daily
- Investigate failed login attempts
- Monitor audit logs regularly
- Report security incidents immediately

### Communication

- Keep audit trail complete
- Provide clear action reasons
- Document unusual events
- Maintain transparency with users

## Troubleshooting

### Common Issues

#### Data Not Loading

1. Check network connectivity
2. Verify backend API status
3. Check browser console for errors
4. Try refreshing the page

#### Actions Not Working

1. Verify user has admin permissions
2. Check if action requires confirmation
3. Review action reason requirements
4. Check for error messages

#### Metrics Not Updating

1. Check auto-refresh interval
2. Verify backend metrics endpoint
3. Check cache settings
4. Manually refresh the page

#### Navigation Issues

1. Verify route configuration
2. Check browser URL
3. Clear browser cache
4. Check for JavaScript errors

## Support

For issues not covered in this guide:

1. Check the [Architecture Documentation](ARCHITECTURE.md)
2. Review the [Monitoring Guide](MONITORING_GUIDE.md)
3. Contact the development team
4. Submit a support ticket with detailed information
