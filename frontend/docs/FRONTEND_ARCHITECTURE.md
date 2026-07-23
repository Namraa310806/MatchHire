# MatchHire Frontend Architecture

## Overview

The MatchHire frontend is built with React 19, TypeScript, and Vite, following a feature-first architecture pattern. This document provides a comprehensive overview of the frontend architecture, including folder structure, component hierarchy, state management, query strategy, authentication flow, and theme system.

## Tech Stack

- **Framework**: React 19
- **Language**: TypeScript
- **Build Tool**: Vite
- **State Management**: TanStack Query (React Query)
- **Routing**: React Router v6
- **Styling**: Tailwind CSS
- **Form Management**: React Hook Form + Zod
- **HTTP Client**: Axios
- **UI Components**: Radix UI primitives
- **Icons**: Lucide React
- **Animations**: Framer Motion
- **Command Palette**: cmdk
- **Date Handling**: date-fns
- **Charts**: Recharts

## Folder Structure

```
src/
├── components/
│   ├── ui/                    # Reusable UI components (Design System)
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   ├── dropdown-menu.tsx
│   │   ├── select.tsx
│   │   ├── avatar.tsx
│   │   ├── badge.tsx
│   │   ├── tooltip.tsx
│   │   ├── popover.tsx
│   │   ├── accordion.tsx
│   │   ├── sheet.tsx
│   │   ├── breadcrumb.tsx
│   │   ├── pagination.tsx
│   │   ├── skeleton.tsx
│   │   ├── spinner.tsx
│   │   ├── empty-state.tsx
│   │   ├── error-state.tsx
│   │   ├── stat-card.tsx
│   │   ├── command.tsx
│   │   ├── calendar.tsx
│   │   ├── file-upload.tsx
│   │   ├── search-box.tsx
│   │   ├── data-table.tsx
│   │   ├── table.tsx
│   │   ├── chart.tsx
│   │   └── ...
│   ├── accessibility/         # Accessibility components
│   │   └── skip-link.tsx
│   ├── loading/               # Loading components
│   │   ├── page-loader.tsx
│   │   ├── section-loader.tsx
│   │   ├── table-loader.tsx
│   │   └── card-loader.tsx
│   ├── error-boundary.tsx    # Global error boundary
│   └── theme-toggle.tsx       # Theme switcher component
├── features/                  # Feature-based modules
│   ├── auth/
│   │   ├── components/        # Auth-specific components
│   │   │   ├── login-form.tsx
│   │   │   └── register-form.tsx
│   │   ├── services/         # Auth API service
│   │   │   └── auth.service.ts
│   │   ├── hooks/            # Auth-specific hooks
│   │   ├── types/            # Auth TypeScript types
│   │   ├── pages/            # Auth pages
│   │   └── utils/            # Auth utilities
│   ├── candidate/            # Candidate feature module
│   ├── recruiter/            # Recruiter feature module
│   ├── jobs/                 # Jobs feature module
│   ├── applications/         # Applications feature module
│   ├── analytics/            # Analytics feature module
│   ├── recommendations/      # Recommendations feature module
│   ├── search/               # Search feature module
│   ├── notifications/        # Notifications feature module
│   ├── resume/               # Resume feature module
│   └── admin/                # Admin feature module
├── layouts/                  # Layout components
│   ├── auth-layout.tsx       # Authentication pages layout
│   ├── public-layout.tsx     # Public pages layout
│   ├── candidate-layout.tsx  # Candidate dashboard layout
│   ├── recruiter-layout.tsx  # Recruiter dashboard layout
│   └── admin-layout.tsx      # Admin dashboard layout
├── pages/                    # Page components
│   └── error-pages/          # Error pages
│       ├── not-found.tsx
│       ├── forbidden.tsx
│       ├── server-error.tsx
│       └── offline.tsx
├── hooks/                    # Custom React hooks
│   ├── use-theme.ts          # Theme management hook
│   ├── use-focus-trap.ts     # Focus trap hook for modals
│   └── use-keyboard-navigation.ts  # Keyboard navigation hook
├── lib/                      # Utility libraries
│   ├── api.ts                # Axios instance and interceptors
│   ├── utils.ts              # General utility functions
│   ├── error-handler.ts      # Error handling utilities
│   └── accessibility.ts      # Accessibility utilities
├── App.tsx                   # Main app component with routing
└── main.tsx                  # Application entry point
```

## Component Hierarchy

### Design System Components

The design system is built on top of Radix UI primitives, providing accessible and customizable components. All UI components follow these principles:

- **Accessibility**: Full ARIA support and keyboard navigation
- **Customizable**: Styled with Tailwind CSS and class-variance-authority
- **Composable**: Components can be combined to build complex UIs
- **Type-safe**: Full TypeScript support

### Layout Components

Layout components provide consistent page structures for different user roles:

- **AuthLayout**: Centered layout for authentication pages
- **PublicLayout**: Header/footer layout for public pages
- **CandidateLayout**: Sidebar + header layout for candidate dashboard
- **RecruiterLayout**: Sidebar + header layout for recruiter dashboard
- **AdminLayout**: Sidebar + header layout for admin dashboard

### Feature Components

Each feature module contains its own components, organized by:
- **Components**: Reusable feature-specific UI components
- **Services**: API service layer for data fetching
- **Hooks**: Custom hooks for feature logic
- **Types**: TypeScript interfaces and types
- **Pages**: Feature-specific page components
- **Utils**: Feature-specific utility functions

## State Management

### TanStack Query (React Query)

TanStack Query is used for server state management, providing:
- **Caching**: Automatic caching and invalidation
- **Background Refetching**: Keep data fresh automatically
- **Optimistic Updates**: Update UI before server confirmation
- **Pagination**: Built-in pagination support
- **Infinite Queries**: Support for infinite scrolling

### Local State

Local component state is managed with React hooks:
- `useState` for simple local state
- `useReducer` for complex local state
- Custom hooks for reusable state logic

### Global State

Global state is minimized and handled through:
- React Context for theme and auth state
- TanStack Query for server state
- URL params for routing state

## Query Strategy

### API Client

The API client (`lib/api.ts`) is configured with:
- **Base URL**: Configurable base URL for API requests
- **Interceptors**: Request/response interceptors for auth and error handling
- **Token Refresh**: Automatic token refresh on 401 errors
- **Error Handling**: Centralized error handling

### Service Layer

Each feature has a dedicated service file that exports functions for API interactions:

```typescript
// Example: auth.service.ts
export const authService = {
  login: async (credentials: LoginCredentials) => { ... },
  register: async (data: RegisterData) => { ... },
  logout: async () => { ... },
  // ...
}
```

### Query Hooks

TanStack Query hooks are used in components to fetch and mutate data:

```typescript
const { data, isLoading, error } = useQuery({
  queryKey: ['jobs', filters],
  queryFn: () => jobService.getJobs(filters),
})

const mutation = useMutation({
  mutationFn: (data: CreateJobData) => jobService.createJob(data),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['jobs'] })
  },
})
```

## Authentication Flow

### Login Flow

1. User enters credentials in `LoginForm`
2. Form is validated with React Hook Form + Zod
3. `authService.login()` is called via API
4. Access token and refresh token are stored
5. User is redirected to appropriate dashboard based on role
6. Auth state is updated in context

### Token Management

- **Access Token**: Stored in memory (or secure cookie)
- **Refresh Token**: Stored in httpOnly cookie
- **Token Refresh**: Automatic refresh via Axios interceptor on 401
- **Token Expiry**: Handled by interceptor with retry logic

### Protected Routes

Protected routes use React Router's `<Outlet>` pattern with route guards:

```typescript
<Route element={<ProtectedRoute />}>
  <Route element={<CandidateRoute />}>
    <Route path="candidate/dashboard" element={<CandidateDashboard />} />
  </Route>
</Route>
```

## Theme System

### Theme Provider

The `ThemeProvider` (`hooks/use-theme.ts`) manages theme state:
- **Themes**: light, dark, system
- **Persistence**: Theme preference stored in localStorage
- **System Detection**: Automatically detects system preference
- **CSS Classes**: Applies `light` or `dark` class to document root

### Theme Toggle

The `ThemeToggle` component allows users to switch themes:
- Button with icon indicating current theme
- Cycles through light → dark → system
- Persists preference to localStorage

### Tailwind Configuration

Tailwind is configured to use CSS variables for theme colors:
- `--background`: Main background color
- `--foreground`: Main text color
- `--primary`: Primary brand color
- `--secondary`: Secondary brand color
- And more semantic color tokens

## Error Handling

### Global Error Boundary

The `ErrorBoundary` component catches React errors:
- Displays user-friendly error message
- Provides retry functionality
- Logs errors to console
- Can be customized with fallback UI

### API Error Handler

The `handleApiError` function (`lib/error-handler.ts`) handles API errors:
- **401**: Redirect to login
- **403**: Show access denied message
- **404**: Show not found message
- **500**: Show server error message
- **Others**: Show generic error message

### Error Pages

Dedicated error pages for different scenarios:
- **NotFoundPage**: 404 errors
- **ForbiddenPage**: 403 errors
- **ServerErrorPage**: 500 errors
- **OfflinePage**: Network errors

### Retry Logic

The `createRetryHandler` utility provides retry functionality:
- Configurable max retries
- Exponential backoff delay
- Automatic retry on failure

## Loading States

### Loading Components

Dedicated loading components for different contexts:
- **PageLoader**: Full page loading skeleton
- **SectionLoader**: Section-level loading skeleton
- **TableLoader**: Table loading skeleton
- **CardLoader**: Card grid loading skeleton
- **Spinner**: Simple spinner for inline loading

### TanStack Query Loading

TanStack Query provides built-in loading states:
- `isLoading`: Initial loading state
- `isFetching`: Background refetching state
- `isPending`: Mutation pending state

## Accessibility

### ARIA Attributes

All interactive components include proper ARIA attributes:
- `role`: Identifies element purpose
- `aria-label`: Provides accessible label
- `aria-describedby`: Associates with description
- `aria-invalid`: Indicates validation errors
- `aria-live**: Announces dynamic changes

### Keyboard Navigation

Custom hooks for keyboard navigation:
- **useKeyboardNavigation**: Handles arrow keys, Enter, Escape
- **useFocusTrap**: Traps focus in modals
- **Skip Links**: Allows skipping to main content

### Focus Management

Utilities for focus management:
- **setFocus**: Sets focus and scrolls into view
- **getFocusableElements**: Finds all focusable elements
- **trapFocus**: Traps focus within container
- **announceToScreenReader**: Announces to screen readers

## Responsive Design

### Breakpoints

Tailwind breakpoints are used for responsive design:
- `sm`: 640px
- `md`: 768px
- `lg`: 1024px
- `xl`: 1280px
- `2xl`: 1536px

### Mobile-First

All components follow mobile-first approach:
- Base styles for mobile
- `md:` and up for tablet/desktop
- Responsive navigation with mobile drawer

### Layouts

Each layout is fully responsive:
- **Desktop**: Sidebar navigation
- **Mobile**: Drawer navigation with hamburger menu
- **Tablet**: Adaptive layout based on screen size

## Performance Optimization

### Code Splitting

Code splitting is implemented via React Router:
- Lazy loading of route components
- Separate chunks per feature module
- Reduced initial bundle size

### Image Optimization

Images should be optimized:
- WebP format when possible
- Lazy loading with `loading="lazy"`
- Responsive images with `srcset`

### Bundle Analysis

Bundle size is monitored with:
- Vite bundle analyzer
- Tree-shaking for unused code
- Minification in production

## Testing Strategy

### Unit Tests

Unit tests should cover:
- Custom hooks
- Utility functions
- Pure components
- Service functions

### Integration Tests

Integration tests should cover:
- Component interactions
- Form submissions
- API calls
- Routing

### E2E Tests

E2E tests should cover:
- Critical user flows
- Authentication
- Navigation
- Form submissions

## Development Guidelines

### Component Guidelines

- **Single Responsibility**: Each component does one thing well
- **Composition**: Prefer composition over inheritance
- **Props Interface**: Define clear prop interfaces
- **Default Props**: Provide sensible defaults
- **Type Safety**: Use TypeScript for all props

### Code Style

- **ESLint**: Follow ESLint rules
- **Prettier**: Use Prettier for formatting
- **Naming**: Use descriptive names
- **Comments**: Comment complex logic only
- **File Names**: Use kebab-case for files

### Git Workflow

- **Branch Strategy**: Feature branches from main
- **Commit Messages**: Conventional commits
- **PR Reviews**: Required for all changes
- **CI/CD**: Automated tests and linting

## Deployment

### Build Process

Production build process:
1. `npm run build` - Creates optimized production build
2. `npm run preview` - Preview production build locally
3. Deploy to hosting platform

### Environment Variables

Required environment variables:
- `VITE_API_URL`: API base URL
- `VITE_APP_NAME`: Application name

### Hosting

The application can be deployed to:
- Vercel
- Netlify
- AWS S3 + CloudFront
- Any static hosting provider

## Future Enhancements

### Planned Improvements

- **PWA Support**: Add service worker for offline support
- **Internationalization**: Add i18n support
- **Analytics**: Integrate analytics tracking
- **Performance Monitoring**: Add performance monitoring
- **E2E Testing**: Add comprehensive E2E tests
- **Storybook**: Add Storybook for component documentation

---

This architecture document serves as a guide for developers working on the MatchHire frontend. It should be updated as the architecture evolves.
