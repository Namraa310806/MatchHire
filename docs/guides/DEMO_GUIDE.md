# MatchHire Demo Guide

This guide provides step-by-step instructions for setting up and running comprehensive demos of MatchHire for candidates, recruiters, and administrators.

## Table of Contents

1. [Quick Start Demo](#quick-start-demo)
2. [Candidate Demo](#candidate-demo)
3. [Recruiter Demo](#recruiter-demo)
4. [Admin Demo](#admin-demo)
5. [Demo Data Setup](#demo-data-setup)
6. [Demo Scenarios](#demo-scenarios)
7. [Troubleshooting](#troubleshooting)

## Quick Start Demo

### Prerequisites

- Docker Desktop installed
- Git installed
- 8GB RAM minimum
- 20GB disk space

### Setup

```bash
# Clone the repository
git clone https://github.com/your-org/matchhire.git
cd matchhire

# Start the application
make docker-up

# Run migrations
make migrate

# Populate demo data
docker compose exec web python manage.py populate_demo_data --companies 50 --jobs 200 --candidates 500 --applications 2000

# Create demo users
docker compose exec web python manage.py create_demo_users
```

### Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api/v1/
- **Admin Panel**: http://localhost:8000/admin/
- **Swagger UI**: http://localhost:8000/api/v1/schema/swagger-ui/

## Candidate Demo

### Demo Credentials

```
Email: candidate_demo@example.com
Password: demo123456
```

### Demo Workflow

#### 1. Registration and Profile Setup

1. Navigate to http://localhost:3000
2. Click "Sign Up" in the top right
3. Fill in registration details:
   - Email: candidate_demo@example.com
   - Password: demo123456
   - First Name: John
   - Last Name: Doe
4. Complete profile setup:
   - Add headline: "Senior Software Engineer"
   - Add summary: "Experienced full-stack developer with 5+ years in Python and React"
   - Set location: "San Francisco, CA"
   - Add skills: Python, React, Django, PostgreSQL

#### 2. Upload Resume

1. Go to Profile → Resume
2. Click "Upload Resume"
3. Select a sample resume (PDF format)
4. Wait for parsing to complete
5. Review extracted skills and experience
6. Save profile

#### 3. Search Jobs

1. Navigate to Jobs → Search
2. Try different search queries:
   - "software engineer"
   - "python developer"
   - "react developer"
   - "full stack"
3. Use filters:
   - Location: Remote
   - Job Type: Full-time
   - Experience Level: Senior
   - Salary Range: $100,000 - $150,000
4. Save search for later

#### 4. View Recommendations

1. Navigate to Jobs → Recommendations
2. Browse AI-recommended jobs based on profile
3. View match scores and reasons
4. Click on jobs to view details
5. Apply to recommended jobs

#### 5. Apply to Jobs

1. Select a job from search or recommendations
2. Click "Apply Now"
3. Write a personalized cover letter
4. Submit application
5. View application status in Applications tab

#### 6. Track Applications

1. Navigate to Applications
2. View all submitted applications
3. Track status: Pending → Reviewed → Interviewing → Offer
4. View interview schedules
5. Update application notes

#### 7. Receive Notifications

1. Navigate to Notifications
2. View application status updates
3. View interview invitations
4. View job recommendations
5. Mark notifications as read

## Recruiter Demo

### Demo Credentials

```
Email: recruiter_demo@techcorp.com
Password: demo123456
```

### Demo Workflow

#### 1. Registration and Company Setup

1. Navigate to http://localhost:3000
2. Click "Sign Up" → "Recruiter"
3. Fill in registration details:
   - Email: recruiter_demo@techcorp.com
   - Password: demo123456
   - Company Name: TechCorp Inc.
   - Industry: Technology
4. Complete company profile:
   - Add description
   - Add website
   - Add location
   - Set company size

#### 2. Post Jobs

1. Navigate to Jobs → Post Job
2. Fill in job details:
   - Title: Senior Software Engineer
   - Description: Detailed job description
   - Requirements: Skills and experience needed
   - Responsibilities: Day-to-day tasks
   - Benefits: Perks and benefits
   - Location: Remote
   - Job Type: Full-time
   - Experience Level: Senior
   - Salary Range: $120,000 - $180,000
3. Add required skills:
   - Python
   - Django
   - React
   - PostgreSQL
4. Set expiry date
5. Publish job

#### 3. Search Candidates

1. Navigate to Candidates → Search
2. Try different search queries:
   - "python developer"
   - "full stack engineer"
   - "react developer"
3. Use filters:
   - Location: Remote
   - Experience Level: Senior
   - Skills: Python, Django
   - Expected Salary Range
4. View candidate profiles
5. Save candidates to shortlist

#### 4. View Recommendations

1. Navigate to Candidates → Recommendations
2. Browse AI-recommended candidates
3. View match scores and reasons
4. Compare candidates
5. Save to shortlist

#### 5. Manage Applications

1. Navigate to Applications
2. View all received applications
3. Review candidate profiles
4. Update application status:
   - Pending → Reviewed → Shortlisted → Interviewing → Offered → Hired
5. Add notes to applications
6. Filter by status, job, or date

#### 6. Schedule Interviews

1. Select a shortlisted application
2. Click "Schedule Interview"
3. Choose interview type:
   - Phone Screen
   - Video Interview
   - On-site Interview
   - Technical Assessment
4. Set date and time
5. Add interview details
6. Send invitation to candidate
7. Track interview status

#### 7. View Analytics

1. Navigate to Analytics
2. View hiring metrics:
   - Total applications received
   - Applications by job
   - Applications by status
   - Time to hire
   - Source of applications
3. View candidate engagement:
   - Profile views
   - Job views
   - Application rates
4. Export reports

## Admin Demo

### Demo Credentials

```
Email: admin@matchhire.com
Password: admin123456
```

### Demo Workflow

#### 1. Platform Overview

1. Navigate to http://localhost:8000/admin/
2. Login with admin credentials
3. View platform statistics:
   - Total users
   - Active jobs
   - Total applications
   - System health

#### 2. User Management

1. Navigate to Users → All Users
2. View all registered users
3. Filter by role (candidate, recruiter, admin)
4. View user profiles
5. Suspend or ban users if needed
6. Reset user passwords
7. View user activity logs

#### 3. Job Management

1. Navigate to Jobs → All Jobs
2. View all posted jobs
3. Filter by company, status, location
4. Review job content
5. Approve or reject jobs
6. Feature premium jobs
7. View job analytics

#### 4. Application Monitoring

1. Navigate to Applications → All Applications
2. View application statistics
3. Monitor application flow
4. Identify bottlenecks
5. View application trends
6. Export application data

#### 5. Search Monitoring

1. Navigate to Monitoring → Search
2. View search analytics:
   - Popular search terms
   - Search volume trends
   - Zero-result searches
3. Monitor Elasticsearch health
4. View search performance metrics
5. Identify search issues

#### 6. Recommendation Monitoring

1. Navigate to Monitoring → Recommendations
2. View recommendation statistics:
   - Total recommendations generated
   - Recommendation click-through rate
   - Application rate from recommendations
3. Monitor recommendation quality
4. View matching algorithm performance
5. A/B test different algorithms

#### 7. System Health

1. Navigate to System → Health
2. View system metrics:
   - CPU usage
   - Memory usage
   - Disk usage
   - Network traffic
3. View database health:
   - Connection pool status
   - Query performance
   - Slow queries
4. View Redis health:
   - Memory usage
   - Connection count
   - Cache hit rate
5. View Celery status:
   - Worker health
   - Queue backlog
   - Task execution time

#### 8. Audit Logs

1. Navigate to System → Audit Logs
2. View all system events:
   - User actions
   - Job postings
   - Applications
   - System changes
3. Filter by date, user, action type
4. Export audit logs
5. Investigate security events

#### 9. Feature Flags

1. Navigate to System → Feature Flags
2. View all feature flags
3. Enable/disable features:
   - Advanced search
   - AI recommendations
   - Video interviews
   - Resume parsing
4. Set rollout percentages
5. Monitor feature usage

## Demo Data Setup

### Populate Demo Data

```bash
# Full demo dataset
docker compose exec web python manage.py populate_demo_data \
  --companies 50 \
  --jobs 200 \
  --candidates 500 \
  --applications 2000

# Smaller dataset for quick testing
docker compose exec web python manage.py populate_demo_data \
  --companies 10 \
  --jobs 20 \
  --candidates 50 \
  --applications 100

# Clear existing demo data and repopulate
docker compose exec web python manage.py populate_demo_data \
  --clear \
  --companies 50 \
  --jobs 200 \
  --candidates 500 \
  --applications 2000
```

### Create Demo Users

```bash
docker compose exec web python manage.py create_demo_users
```

This creates:
- 1 admin user
- 5 recruiter users
- 10 candidate users

### Elasticsearch Indexing

```bash
# Index all jobs
docker compose exec web python manage.py search_index --model jobs.Job --action index

# Index all candidates
docker compose exec web python manage.py search_index --model users.CandidateProfile --action index

# Rebuild all indexes
docker compose exec web python manage.py search_index --action rebuild
```

## Demo Scenarios

### Scenario 1: End-to-End Hiring Process

**Objective**: Demonstrate complete hiring workflow from job posting to offer acceptance.

**Steps**:
1. Recruiter posts a job
2. Candidate searches and finds the job
3. Candidate applies with resume
4. Recruiter reviews application
5. Recruiter schedules interview
6. Candidate attends interview
7. Recruiter extends offer
8. Candidate accepts offer

**Duration**: 10-15 minutes

### Scenario 2: AI-Powered Matching

**Objective**: Demonstrate AI recommendation system.

**Steps**:
1. Candidate completes profile with skills
2. System generates job recommendations
3. Candidate views match scores and reasons
4. Recruiter posts job with requirements
5. System generates candidate recommendations
6. Recruiter views match scores and reasons

**Duration**: 5-10 minutes

### Scenario 3: Advanced Search

**Objective**: Demonstrate Elasticsearch-powered search capabilities.

**Steps**:
1. Candidate performs semantic search
2. Use filters and facets
3. Save search queries
4. Recruiter searches for candidates
5. Use boolean operators
6. Export search results

**Duration**: 5-8 minutes

### Scenario 4: Analytics Dashboard

**Objective**: Demonstrate hiring analytics and insights.

**Steps**:
1. Recruiter views application funnel
2. Analyze time-to-hire metrics
3. View candidate engagement data
4. Export reports
5. Admin views platform-wide analytics
6. Monitor system health

**Duration**: 8-12 minutes

## Troubleshooting

### Demo Data Not Loading

**Problem**: Demo data command fails or data doesn't appear.

**Solution**:
```bash
# Check if Faker is installed
docker compose exec web pip list | grep Faker

# Install Faker if missing
docker compose exec web pip install faker

# Run migrations first
docker compose exec web python manage.py migrate

# Try populating data again
docker compose exec web python manage.py populate_demo_data --clear
```

### Search Not Working

**Problem**: Search returns no results or errors.

**Solution**:
```bash
# Check Elasticsearch status
docker compose exec web curl -X GET "localhost:9200/_cluster/health"

# Rebuild search indexes
docker compose exec web python manage.py search_index --action rebuild

# Check search configuration
docker compose exec web python manage.py check
```

### Images Not Uploading

**Problem**: Resume or profile image uploads fail.

**Solution**:
```bash
# Check media directory permissions
docker compose exec web ls -la /app/backend/media

# Fix permissions
docker compose exec web chmod -R 755 /app/backend/media

# Restart containers
docker compose restart
```

### Performance Issues

**Problem**: Demo runs slowly or times out.

**Solution**:
```bash
# Check container resources
docker stats

# Increase Docker memory allocation in Docker Desktop settings
# Recommended: 8GB RAM, 4 CPUs

# Clear Redis cache
docker compose exec redis redis-cli FLUSHALL

# Restart services
docker compose restart web celery_worker celery_beat
```

### Frontend Not Loading

**Problem**: Frontend shows blank page or errors.

**Solution**:
```bash
# Check frontend build
cd frontend
npm run build

# Restart frontend container
docker compose restart frontend

# Check browser console for errors
# Open Developer Tools (F12) and check Console tab
```

## Tips for Successful Demos

### Preparation

1. **Test the demo beforehand**: Run through all scenarios at least once
2. **Have backup data**: Keep a snapshot of working demo data
3. **Check system health**: Verify all services are running before starting
4. **Clear browser cache**: Use incognito mode for clean demo
5. **Have backup credentials**: Keep a list of all demo user credentials

### During Demo

1. **Start with overview**: Briefly explain the platform before diving in
2. **Focus on value**: Highlight features that solve real problems
3. **Keep it interactive**: Ask questions and engage the audience
4. **Handle errors gracefully**: Have backup plans if something fails
5. **Time management**: Keep each scenario within time limits

### After Demo

1. **Collect feedback**: Ask for questions and suggestions
2. **Document issues**: Note any problems encountered
3. **Follow up**: Send additional resources if requested
4. **Clean up**: Reset demo data for next session

## Additional Resources

- [Developer Guide](../development/developer-guide.md)
- [API Documentation](../api/)
- [Deployment Guide](../deployment/)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
