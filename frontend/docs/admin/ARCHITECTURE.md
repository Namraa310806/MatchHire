# Admin Console Architecture

## Overview

The MatchHire Admin Console is a production-grade administration and operations interface built with React, TypeScript, and TanStack Query. It provides comprehensive platform management capabilities including user management, content moderation, system monitoring, and observability.

## Technology Stack

- **Frontend Framework**: React 18 with TypeScript
- **Routing**: React Router v6
- **State Management**: TanStack Query (React Query) for server state
- **UI Components**: shadcn/ui with Tailwind CSS
- **Icons**: Lucide React
- **HTTP Client**: Axios

## Directory Structure

```
src/features/admin/
├── components/          # Shared admin components
│   ├── AdminLayout.tsx     # Main admin layout with sidebar
│   ├── AdminSidebar.tsx    # Navigation sidebar
│   ├── AdminDataTable.tsx  # Reusable data table component
│   ├── AdminStatusBadge.tsx # Status badge component
│   ├── AdminActionDialog.tsx # Action confirmation dialog
│   └── AdminFilterBar.tsx  # Search and filter bar
├── hooks/              # Custom React Query hooks
│   ├── useAdminDashboard.ts
│   ├── useAdminUsers.ts
│   ├── useAdminCompanies.ts
│   ├── useAdminJobs.ts
│   ├── useAdminResumes.ts
│   ├── useAdminApplications.ts
│   ├── useHealth.ts
│   ├── useObservability.ts
│   ├── useFeatureFlags.ts
│   ├── useAuditLogs.ts
│   └── useSecurity.ts
├── pages/              # Admin page components
│   ├── SystemDashboard.tsx
│   ├── UserManagement.tsx
│   ├── CompanyManagement.tsx
│   ├── JobAdministration.tsx
│   ├── ApplicationAdministration.tsx
│   ├── ResumeAdministration.tsx
│   ├── SearchMonitoring.tsx
│   ├── RecommendationMonitoring.tsx
│   ├── Observability.tsx
│   ├── FeatureFlags.tsx
│   ├── AuditLogs.tsx
│   ├── SecurityCenter.tsx
│   └── SystemConfiguration.tsx
├── services/           # API service layer
│   └── adminService.ts
├── types/              # TypeScript type definitions
│   └── index.ts
└── utils/              # Utility functions
```

## Core Components

### AdminLayout

The main layout component that wraps all admin pages. It provides:
- Collapsible sidebar navigation
- Responsive design
- Consistent page structure

### AdminSidebar

Navigation sidebar with:
- 13 admin sections
- Collapsible interface
- Active route highlighting
- Icon-based navigation

### AdminDataTable

Reusable data table component with:
- Pagination support
- Loading states
- Empty state handling
- Custom row rendering

### AdminStatusBadge

Standardized status badges for:
- User status (active, suspended)
- Job status (draft, active, closed, archived)
- Company status (pending, approved, rejected, suspended)
- Health status (healthy, degraded, unhealthy)

### AdminActionDialog

Reusable confirmation dialog for:
- User actions (suspend, activate, change role)
- Company actions (approve, reject, suspend)
- Job actions (approve, close, archive)
- Resume actions (suspend, activate)

### AdminFilterBar

Search and filter component with:
- Text search
- Dropdown filters
- Clear filters functionality

## Data Layer

### API Services

All API calls are centralized in `adminService.ts`:

```typescript
// Dashboard and metrics
adminApi.getDashboardStats()
healthApi.getHealthStatus()
searchMetricsApi.getSearchMetrics()
recommendationMetricsApi.getRecommendationMetrics()
systemMetricsApi.getSystemMetrics()

// CRUD operations
adminApi.getUsers()
adminApi.updateUser()
adminApi.getCompanies()
adminApi.updateCompany()
adminApi.getJobs()
adminApi.updateJob()
adminApi.getResumes()
adminApi.updateResume()
adminApi.getApplications()

// Observability and security
featureFlagsApi.getFeatureFlags()
auditLogsApi.getAuditLogs()
securityApi.getSecurityEvents()
securityApi.getLoginActivity()
systemConfigApi.getSystemConfig()
```

### React Query Hooks

Custom hooks provide typed, cached data access:

```typescript
// Auto-refreshing hooks
useAdminDashboard()      // 30s refresh
useHealthStatus()        // 30s refresh
useSystemMetrics()       // 30s refresh
useSearchMetrics()       // 60s refresh
useRecommendationMetrics() // 60s refresh

// Manual refresh hooks
useAdminUsers(params)
useAdminCompanies(params)
useAdminJobs(params)
useAdminResumes(params)
useAdminApplications(params)
```

## Type System

Comprehensive TypeScript types defined in `types/index.ts`:

- **Admin Types**: Dashboard stats, users, companies, jobs, resumes, applications
- **Health Types**: Health status, health checks
- **Metrics Types**: Search metrics, recommendation metrics, system metrics
- **Observability Types**: Queue status, job status, service health
- **Security Types**: Security events, login activity
- **Configuration Types**: System config, feature flags, audit logs

## Routing

Admin routes are protected by `AdminRoute` component:

```typescript
<Route element={<AdminRoute />}>
  <Route element={<AdminLayout />}>
    <Route path="admin/dashboard" element={<SystemDashboard />} />
    <Route path="admin/users" element={<UserManagement />} />
    <!-- ... other admin routes -->
  </Route>
</Route>
```

## Design Patterns

### 1. Feature-Based Organization

Admin functionality is organized by feature rather than by file type, following the feature-sliced design pattern.

### 2. Separation of Concerns

- **Components**: UI rendering and user interaction
- **Hooks**: Data fetching and state management
- **Services**: API communication
- **Types**: Type definitions

### 3. Reusable Components

Shared components reduce code duplication and ensure consistency across admin pages.

### 4. Auto-Refresh

Critical metrics auto-refresh at appropriate intervals to provide real-time visibility.

### 5. Loading States

All pages include loading skeletons for better perceived performance.

### 6. Error Handling

Graceful degradation when backend endpoints are unavailable.

## Backend Integration

The admin console integrates with existing backend APIs:

- **Admin APIs**: `/api/admin/*` for CRUD operations
- **Health APIs**: `/api/health/`, `/api/ready/`, `/api/live/`
- **Mock APIs**: Some endpoints return mock data when backend support is unavailable

## Performance Considerations

1. **Query Caching**: TanStack Query caches responses to reduce API calls
2. **Selective Refresh**: Only critical metrics auto-refresh
3. **Pagination**: Large datasets use pagination
4. **Lazy Loading**: Components load data only when needed
5. **Code Splitting**: Admin pages can be code-split for better initial load

## Security

- All admin routes require admin role authentication
- Sensitive actions require confirmation dialogs
- Audit trails track all administrative actions
- Security events are monitored and displayed

## Accessibility

- Semantic HTML elements
- Keyboard navigation support
- Screen reader friendly
- High contrast ratios in dark mode
- Focus management in dialogs

## Future Enhancements

1. **Real-time Updates**: WebSocket integration for live metrics
2. **Advanced Analytics**: Charts and graphs for data visualization
3. **Bulk Operations**: Enhanced bulk action capabilities
4. **Export Functionality**: CSV/Excel export for reports
5. **Custom Dashboards**: User-configurable dashboard layouts
