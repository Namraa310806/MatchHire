# Admin Console Documentation

## Overview

The MatchHire Admin Console is a production-grade administration and operations interface that provides comprehensive platform management capabilities. Built with React, TypeScript, and TanStack Query, it integrates with existing backend APIs to expose health monitoring, user management, job moderation, and system configuration.

## Architecture

### Feature Structure

```
frontend/src/features/admin/
├── components/       # Reusable admin components
├── hooks/           # Custom React hooks for data fetching
├── pages/           # Admin page components
├── services/        # API service layer
├── types/           # TypeScript type definitions
└── utils/           # Utility functions
```

### Key Design Principles

- **Enterprise-Grade UI**: Inspired by GitHub Enterprise, Datadog, and AWS Console
- **Real-Time Monitoring**: Auto-refresh capabilities for health and metrics
- **Responsive Design**: Mobile-friendly layouts with dark mode support
- **Accessibility**: WCAG AA compliant with keyboard navigation
- **Type Safety**: Full TypeScript coverage with strict type checking

## Pages

### System Dashboard

**Location**: `features/admin/pages/SystemDashboard.tsx`

**Features**:
- Platform KPIs (users, jobs, applications, companies)
- System health status with real-time checks
- Search platform metrics (provider, index status, latency)
- Recommendation engine metrics (acceptance rate, confidence)
- System metrics (API latency, error rate, cache performance)

**Backend APIs**:
- `GET /api/admin/dashboard/` - Platform statistics
- `GET /api/health/` - System health status
- Mock endpoints for search/recommendation metrics (ready for backend integration)

### User Management

**Location**: `features/admin/pages/UserManagement.tsx`

**Features**:
- View all users with pagination
- Search by name or email
- Filter by role and status
- Suspend/activate users with reason logging
- Change user roles
- Bulk actions support

**Backend APIs**:
- `GET /api/admin/users/` - List users with filters
- `GET /api/admin/users/<id>/` - Get user details
- `PATCH /api/admin/users/<id>/` - Update user (is_active, role)

### Job Administration

**Location**: `features/admin/pages/JobAdministration.tsx`

**Features**:
- View all jobs (draft, active, closed, archived)
- Search by title or company
- Filter by status
- Approve draft jobs
- Close active jobs
- Archive jobs

**Backend APIs**:
- `GET /api/admin/jobs/` - List jobs with filters
- `PATCH /api/admin/jobs/<id>/` - Update job status

### Application Administration

**Location**: `features/admin/pages/ApplicationAdministration.tsx`

**Features**:
- View all applications
- Filter by status
- View candidate, job, and recruiter details
- Read-only inspection (status changes handled by recruiters)

**Backend APIs**:
- `GET /api/admin/applications/` - List applications with filters

### Resume Administration

**Location**: `features/admin/pages/ResumeAdministration.tsx`

**Features**:
- View all resumes
- Filter by parsing status and structured data status
- Suspend/activate resumes (affects user account)
- View file details and parsing status

**Backend APIs**:
- `GET /api/admin/resumes/` - List resumes with filters
- `PATCH /api/admin/resumes/<id>/` - Update resume (activate/deactivate user)

### Search Monitoring

**Location**: `features/admin/pages/SearchMonitoring.tsx`

**Features**:
- Search provider information
- Index status and document count
- Query latency metrics (p50, p95, p99)
- Cache hit ratio
- Top queries analysis
- Search failures tracking

**Note**: Currently uses mock data, ready for backend integration

### Recommendation Monitoring

**Location**: `features/admin/pages/RecommendationMonitoring.tsx`

**Features**:
- Total recommendation requests
- Acceptance rate tracking
- Average confidence score
- Latency metrics (p50, p95)
- Feedback analysis (positive/negative)

**Note**: Currently uses mock data, ready for backend integration

### System Configuration

**Location**: `features/admin/pages/SystemConfiguration.tsx`

**Features**:
- Environment information (name, version, deploy time)
- General settings (site name, upload limits)
- Email configuration (SMTP settings)
- Storage configuration (provider, bucket)
- Search configuration (provider, index settings)
- Recommendation configuration (strategy, thresholds)
- Analytics configuration (provider, tracking)
- Maintenance mode status

**Note**: Read-only view, ready for backend integration

## Services

### Admin Service

**Location**: `features/admin/services/adminService.ts`

**API Functions**:
- `adminApi.getDashboardStats()` - Fetch platform statistics
- `adminApi.getUsers(params)` - List users with filters
- `adminApi.getUser(id)` - Get user details
- `adminApi.updateUser(id, update)` - Update user
- `adminApi.getJobs(params)` - List jobs with filters
- `adminApi.updateJob(id, update)` - Update job status
- `adminApi.getResumes(params)` - List resumes with filters
- `adminApi.updateResume(id, update)` - Update resume
- `adminApi.getApplications(params)` - List applications with filters

**Observability APIs** (mock, ready for backend):
- `healthApi.getHealthStatus()` - System health
- `searchMetricsApi.getSearchMetrics()` - Search metrics
- `recommendationMetricsApi.getRecommendationMetrics()` - Recommendation metrics
- `systemMetricsApi.getSystemMetrics()` - System metrics
- `systemConfigApi.getSystemConfig()` - System configuration

## Hooks

### useAdminDashboard

Fetches dashboard statistics with auto-refresh every 30 seconds.

```typescript
const { data, isLoading } = useAdminDashboard();
```

### useAdminUsers

Fetches users with filtering support.

```typescript
const { data, isLoading, refetch } = useAdminUsers({
  search: 'john',
  role: 'candidate',
  is_active: true
});
```

### useUpdateUser

Mutation for updating user status/role.

```typescript
const updateUser = useUpdateUser();
await updateUser.mutateAsync({ id, update });
```

### useAdminJobs

Fetches jobs with filtering support.

```typescript
const { data, isLoading } = useAdminJobs({
  status: 'active',
  search: 'engineer'
});
```

### useUpdateJob

Mutation for updating job status.

```typescript
const updateJob = useUpdateJob();
await updateJob.mutateAsync({ id, update });
```

### useHealthStatus

Fetches system health with auto-refresh every 30 seconds.

```typescript
const { data, isLoading } = useHealthStatus();
```

### useObservability

Hooks for search, recommendation, and system metrics.

```typescript
const { data: searchMetrics } = useSearchMetrics();
const { data: recommendationMetrics } = useRecommendationMetrics();
const { data: systemMetrics } = useSystemMetrics();
```

## Types

All TypeScript types are defined in `features/admin/types/index.ts`:

- `AdminDashboardStats` - Platform statistics
- `AdminUser` / `AdminUserUpdate` - User management
- `AdminJob` / `AdminJobUpdate` - Job administration
- `AdminResume` / `AdminResumeUpdate` - Resume administration
- `AdminApplication` - Application data
- `PaginatedResponse<T>` - Pagination wrapper
- `HealthStatus` / `HealthCheck` - Health monitoring
- `SearchMetrics` - Search platform metrics
- `RecommendationMetrics` - Recommendation engine metrics
- `SystemMetrics` - System observability metrics
- `SystemConfig` - System configuration

## Backend Integration

### Existing APIs

The following backend APIs are fully integrated:

- **Admin Dashboard**: `/api/admin/dashboard/`
- **User Management**: `/api/admin/users/`
- **Job Administration**: `/api/admin/jobs/`
- **Resume Administration**: `/api/admin/resumes/`
- **Application Administration**: `/api/admin/applications/`
- **Health Checks**: `/api/health/`, `/api/ready/`, `/api/live/`

### Mock APIs (Ready for Integration)

The following features have UI implementations with mock data, ready for backend integration:

- **Search Metrics**: Would integrate with search observability endpoints
- **Recommendation Metrics**: Would integrate with recommendation engine metrics
- **System Metrics**: Would integrate with system observability endpoints
- **Feature Flags**: UI ready for feature flag backend
- **Audit Logs**: UI ready for audit log backend
- **Security Events**: UI ready for security event backend

## Operations UX

### Auto-Refresh

Critical dashboards auto-refresh:
- System Dashboard: 30 seconds
- Health Status: 30 seconds
- Search Metrics: 60 seconds
- Recommendation Metrics: 60 seconds
- System Metrics: 30 seconds

### Loading States

All data fetching includes skeleton loaders for better perceived performance.

### Error Handling

API errors are handled gracefully with user-friendly error messages.

### Responsive Design

All pages are responsive and work on:
- Desktop (1280px+)
- Tablet (768px-1279px)
- Mobile (<768px)

## Security

### Authentication

All admin endpoints require:
- Admin role (`IsAdmin` permission)
- Valid JWT token
- Throttled requests (admin scope)

### Authorization

User actions are logged with:
- Actor information
- Action performed
- Reason for action
- Timestamp

### Audit Trail

All administrative actions are logged via the backend moderation service.

## Future Enhancements

### Company Management

Company management page with:
- View companies
- Approve/reject companies
- Suspend companies
- View company recruiters
- Company statistics

### Feature Flags

Feature flag management with:
- View flags
- Enable/disable flags
- Environment-specific flags
- Audit history

### Audit Logs

Audit log viewer with:
- Filter by action, actor, resource
- Timeline view
- Search functionality
- Export capabilities

### Security Center

Security dashboard with:
- Login activity
- Failed logins
- Locked accounts
- Role assignments
- Security alerts

## Testing

### Unit Tests

Test coverage for:
- Admin service functions
- Custom hooks
- Type validation

### Integration Tests

Test coverage for:
- API integration
- Data flow
- Error handling

### E2E Tests

Test coverage for:
- User workflows
- Admin actions
- Navigation

## Performance

### Optimization

- TanStack Query caching with appropriate TTL
- Pagination for large datasets
- Optimistic updates for mutations
- Skeleton loading states

### Metrics

Target performance:
- Dashboard load: <1s
- Table render: <500ms
- API response: <200ms (p95)

## Accessibility

### WCAG AA Compliance

- Keyboard navigation
- Screen reader support
- Focus management
- Color contrast ratios
- ARIA labels

### Keyboard Shortcuts

Future enhancement:
- Command palette (Cmd+K)
- Quick navigation
- Action shortcuts
