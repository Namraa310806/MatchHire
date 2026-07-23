# Admin Console Architecture

## System Overview

The Admin Console is a React-based single-page application that provides comprehensive platform administration capabilities. It follows a feature-based architecture with clear separation of concerns.

## Technology Stack

### Frontend Framework
- **React 18+**: UI framework with hooks
- **TypeScript**: Type safety and developer experience
- **Vite**: Build tool and dev server

### State Management
- **TanStack Query**: Server state management, caching, and synchronization
- **React Context**: Local component state

### UI Components
- **shadcn/ui**: Component library built on Radix UI
- **Tailwind CSS**: Utility-first CSS framework
- **Lucide React**: Icon library

### Data Layer
- **Axios**: HTTP client with interceptors
- **TanStack Query**: Data fetching and caching

## Architecture Layers

### 1. Presentation Layer (Pages)

**Location**: `features/admin/pages/`

Each page is a self-contained component that:
- Manages its own local state
- Uses custom hooks for data fetching
- Composes UI components
- Handles user interactions

**Example**:
```typescript
export default function UserManagement() {
  const [search, setSearch] = useState('');
  const { data, isLoading } = useAdminUsers({ search });
  // UI rendering
}
```

### 2. Data Layer (Hooks)

**Location**: `features/admin/hooks/`

Custom hooks encapsulate:
- API calls via TanStack Query
- Caching strategies
- Error handling
- Loading states

**Example**:
```typescript
export function useAdminUsers(params: UserListParams = {}) {
  return useQuery({
    queryKey: ['admin', 'users', params],
    queryFn: () => adminApi.getUsers(params),
  });
}
```

### 3. Service Layer (Services)

**Location**: `features/admin/services/`

Service functions handle:
- HTTP requests
- Request/response transformation
- Error handling
- API endpoint configuration

**Example**:
```typescript
export const adminApi = {
  getUsers: async (params: UserListParams): Promise<PaginatedResponse<AdminUser>> => {
    const { data } = await api.get<PaginatedResponse<AdminUser>>('/users/', { params });
    return data;
  },
};
```

### 4. Type Layer (Types)

**Location**: `features/admin/types/`

TypeScript definitions ensure:
- Type safety across layers
- IDE autocomplete
- Compile-time error detection
- Self-documenting code

**Example**:
```typescript
export interface AdminUser {
  id: string;
  email: string;
  full_name: string | null;
  role: 'candidate' | 'recruiter' | 'admin';
  is_active: boolean;
  date_joined: string;
}
```

## Data Flow

### Read Flow

1. User interacts with page (e.g., clicks "Users" tab)
2. Page component calls custom hook (e.g., `useAdminUsers()`)
3. Hook executes TanStack Query
4. TanStack Query calls service function
5. Service makes HTTP request to backend
6. Response is cached by TanStack Query
7. Component receives data and renders

### Write Flow

1. User performs action (e.g., suspends user)
2. Page component calls mutation hook
3. Hook executes service function
4. Service makes HTTP request to backend
5. On success, TanStack Query invalidates relevant cache
6. Components automatically re-fetch and update

## Caching Strategy

### Query Caching

TanStack Query provides intelligent caching:
- **Default TTL**: 5 minutes for most queries
- **Dashboard TTL**: 30 seconds with auto-refresh
- **Health TTL**: 10 seconds with auto-refresh
- **Metrics TTL**: 30-60 seconds with auto-refresh

### Cache Keys

Cache keys follow a hierarchical pattern:
```typescript
['admin', 'users', { search: 'john', role: 'candidate' }]
['admin', 'dashboard']
['health', 'status']
```

### Cache Invalidation

Mutations automatically invalidate related caches:
```typescript
onSuccess: () => {
  queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
}
```

## Error Handling

### API Errors

Service layer handles HTTP errors:
- 401/403: Redirect to login
- 404: Show not found state
- 500: Show error message
- Network: Show offline message

### Validation Errors

Backend validation errors are displayed:
- Form-level errors
- Field-level errors
- Action-specific errors

## Performance Optimization

### Code Splitting

Pages are code-split by route:
```typescript
const SystemDashboard = lazy(() => import('@/features/admin/pages/SystemDashboard'));
```

### Lazy Loading

Components are lazy-loaded when needed:
- Heavy charts
- Complex tables
- Dialog components

### Memoization

Expensive computations are memoized:
- `useMemo` for derived data
- `useCallback` for event handlers
- React.memo for component re-renders

## Security Architecture

### Authentication

- JWT tokens stored securely
- Automatic token refresh
- Token expiration handling
- Logout on token invalidation

### Authorization

- Role-based access control
- Permission checks on backend
- Admin-only endpoints
- Throttled admin requests

### Data Protection

- No sensitive data in localStorage
- Secure HTTP only cookies
- CSRF protection
- XSS prevention

## Scalability Considerations

### Horizontal Scaling

- Stateless design
- Shared cache (if needed)
- CDN for static assets
- Load balancer ready

### Vertical Scaling

- Efficient rendering
- Minimal bundle size
- Optimized images
- Lazy loading

## Monitoring Integration

### Frontend Monitoring

Ready for integration with:
- Error tracking (Sentry)
- Performance monitoring (Web Vitals)
- User analytics
- A/B testing

### Backend Monitoring

Backend provides:
- Health endpoints
- Metrics endpoints
- Log aggregation
- Alerting

## Future Architecture Enhancements

### Real-Time Updates

WebSocket integration for:
- Live dashboard updates
- Real-time notifications
- Collaborative features

### Offline Support

Service Worker for:
- Offline page access
- Background sync
- Cache-first strategy

### Advanced Features

- Command palette
- Keyboard shortcuts
- Customizable dashboards
- Export functionality
