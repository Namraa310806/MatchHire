# MatchHire API Hardening - Security Implementation Report

## Security Architecture Summary

The MatchHire backend has been hardened with production-grade security measures following defense-in-depth principles. The implementation includes:

1. **Rate Limiting & Throttling**: Custom DRF throttle classes with scoped rate limits per endpoint type
2. **File Upload Validation**: Multi-layer validation (MIME type, extension, size, file signature)
3. **Request Validation**: UUID, pagination, ordering, and search parameter validation
4. **Security Headers**: Production-grade HTTP security headers
5. **CORS Configuration**: Whitelist-based CORS with credentials support
6. **Permission System**: Role-based access control with explicit permissions
7. **Serializer Hardening**: Explicit field lists, read-only fields, no mass assignment
8. **Security Audit Logging**: Centralized logging for security events
9. **Password Validation**: Django's built-in password validators
10. **JWT Configuration**: Secure token lifetimes with rotation and blacklisting
11. **API Versioning**: URL-based versioning with backward compatibility
12. **Exception Handling**: Centralized DRF exception handler for consistent error responses

---

## DRF Throttle Configuration

### Custom Throttle Classes

Created in `matchhire_backend/core/throttling.py`:

- **AnonymousRateThrottle**: 100 requests/day for anonymous users
- **AuthenticatedRateThrottle**: 1000 requests/day for authenticated users
- **LoginRateThrottle**: 10 requests/hour for login attempts
- **RegistrationRateThrottle**: 5 requests/hour for registration attempts
- **ResumeUploadRateThrottle**: 30 requests/hour for resume uploads
- **ResumeParsingRateThrottle**: 30 requests/hour for resume parsing
- **StructuredExtractionRateThrottle**: 30 requests/hour for structured extraction
- **JobApplyRateThrottle**: 100 requests/hour for job applications
- **MatchingRateThrottle**: 100 requests/hour for matching operations
- **InterviewScheduleRateThrottle**: 50 requests/hour for interview scheduling
- **NotificationRateThrottle**: 500 requests/hour for notification operations
- **AdminRateThrottle**: 200 requests/hour for admin operations
- **AnalyticsRateThrottle**: 100 requests/hour for analytics operations

### Configuration in settings/base.py

```python
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": (
        "matchhire_backend.core.throttling.AuthenticatedRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anonymous": "100/day",
        "authenticated": "1000/day",
        "login": "10/hour",
        "registration": "5/hour",
        "resume_upload": "30/hour",
        "resume_parsing": "30/hour",
        "structured_extraction": "30/hour",
        "job_apply": "100/hour",
        "matching": "100/hour",
        "interview_schedule": "50/hour",
        "notification": "500/hour",
        "admin": "200/hour",
        "analytics": "100/hour",
    },
}
```

### Throttle Scope Assignment

All endpoints have been assigned appropriate `throttle_scope`:

- **Authentication**: LoginView, CandidateRegistrationView, RecruiterRegistrationView → `login`, `registration`
- **Resumes**: ResumeUploadView → `resume_upload`, ParseResumeView → `resume_parsing`, ExtractResumeVersionView → `structured_extraction`
- **Applications**: JobApplyView → `job_apply`
- **Matching**: CandidateMatchView, JobRecommendationsView, RecruiterCandidatesView → `matching`
- **Interviews**: ApplicationInterviewsListView → `interview_schedule`
- **Notifications**: All notification views → `notification`
- **Admin**: All admin views → `admin`
- **Analytics**: All analytics views → `analytics`
- **General**: All other authenticated endpoints → `authenticated`

---

## File Upload Hardening

### Implementation in apps/resumes/services/validators.py

**Multi-layer validation:**

1. **File Existence Check**: Ensures file is provided
2. **Size Validation**: Maximum 10 MB (10 * 1024 * 1024 bytes)
3. **Dangerous Extension Rejection**: Blocks `.exe`, `.js`, `.dll`, `.bat`, `.zip`, `.sh`, `.cmd`, `.msi`
4. **Allowed Extensions**: `.pdf`, `.docx`, `.txt`
5. **MIME Type Validation**: 
   - `application/pdf`
   - `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
   - `text/plain`
6. **File Signature Verification**:
   - PDF: Must start with `%PDF`
   - DOCX: Must start with `PK` (ZIP archive signature)
   - TXT: Must be valid UTF-8 text

### Validation Logic

```python
def validate_resume_file(file):
    # 1. Check file exists
    # 2. Check file size <= 10MB
    # 3. Reject dangerous extensions
    # 4. Validate allowed extensions
    # 5. Validate MIME type
    # 6. Verify file signature (prevent spoofing)
```

---

## Request Validation

### Implementation in matchhire_backend/core/validators.py

**Validation Functions:**

1. **validate_uuid(value, field_name)**: Validates UUID format
2. **validate_pagination(page, page_size, max_page_size)**: Validates pagination parameters
3. **validate_ordering(ordering, valid_fields)**: Validates ordering against allowed fields
4. **validate_search_length(search, max_length)**: Validates search query length (max 200 chars)
5. **validate_boolean(value, field_name)**: Validates boolean parameters
6. **validate_choice(value, valid_choices, field_name)**: Validates against allowed choices

### Applied to Views

UUID validation applied to all views accepting UUID parameters:
- Resumes: ResumeDetailView, ParseResumeView, ResumeActivateView, etc.
- Jobs: JobDetailView, JobCloseView
- Applications: JobApplyView, ApplicationDetailView, etc.
- Interviews: All interview views
- Admin: All admin detail views

Ordering and search validation applied to:
- ResumeSearchView
- PublicJobListView

---

## Security Headers

### Configuration in settings/prod.py

Production-only security headers:

```python
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
```

**Headers Description:**
- **SECURE_SSL_REDIRECT**: Forces HTTPS in production
- **SESSION_COOKIE_SECURE**: Session cookies only sent over HTTPS
- **CSRF_COOKIE_SECURE**: CSRF cookies only sent over HTTPS
- **SECURE_HSTS_SECONDS**: HSTS with 1 year max-age
- **SECURE_HSTS_INCLUDE_SUBDOMAINS**: HSTS applies to all subdomains
- **SECURE_HSTS_PRELOAD**: HSTS preload eligible
- **X_FRAME_OPTIONS**: Prevents clickjacking (DENY)
- **SECURE_CONTENT_TYPE_NOSNIFF**: Prevents MIME type sniffing
- **SECURE_BROWSER_XSS_FILTER**: Enables XSS filter
- **SECURE_REFERRER_POLICY**: Controls referrer information
- **SECURE_PROXY_SSL_HEADER**: Trusts proxy SSL header

---

## CORS Configuration

### Current Configuration in settings/base.py

```python
CORS_ALLOWED_ORIGINS = get_env(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000,http://localhost:5173",
    cast=Csv(),
)
CORS_ALLOW_CREDENTIALS = True
```

**Security Assessment:**
- ✅ Uses whitelist approach (CORS_ALLOWED_ORIGINS)
- ✅ Does NOT use CORS_ALLOW_ALL_ORIGINS=True
- ✅ Credentials allowed for authenticated requests
- ✅ Default origins are development localhost ports
- ✅ Configurable via environment variable

**Rationale:**
Whitelist-based CORS is more secure than allowing all origins. The configuration allows specific frontend origins (localhost:3000 for React, localhost:5173 for Vite) and supports credentials for cookie-based authentication.

---

## Permission Audit Report

### Permission Classes by Endpoint

**Authentication Endpoints:**
- LoginView: `AllowAny` (correct for public endpoint)
- CandidateRegistrationView: `AllowAny` (correct for public endpoint)
- RecruiterRegistrationView: `AllowAny` (correct for public endpoint)
- RefreshView: `IsAuthenticated`
- LogoutView: `IsAuthenticated`
- CurrentUserView: `IsAuthenticated`

**Resume Endpoints:**
- ResumeUploadView: `IsAuthenticated, IsCandidate`
- ResumeListView: `IsAuthenticated, IsCandidate`
- ResumeDetailView: `IsAuthenticated, IsCandidate`
- ResumeSearchView: `IsAuthenticated, IsRecruiter`
- ParseResumeView: `IsAuthenticated, IsCandidate`
- ExtractResumeVersionView: `IsAuthenticated, IsCandidate`

**Job Endpoints:**
- JobCreateView: `IsAuthenticated, IsRecruiter`
- MyJobsListView: `IsAuthenticated, IsRecruiter`
- JobDetailView: `IsAuthenticated` (with role-based access in view logic)
- JobCloseView: `IsAuthenticated, IsRecruiter, IsJobOwner`
- PublicJobListView: `IsAuthenticated`

**Application Endpoints:**
- JobApplyView: `IsAuthenticated, IsCandidate`
- MyApplicationsListView: `IsAuthenticated, IsCandidate`
- ApplicationDetailView: `IsAuthenticated` (with ownership check)
- JobApplicationsListView: `IsAuthenticated, IsRecruiter`
- ApplicationStatusUpdateView: `IsAuthenticated, IsRecruiter`

**Interview Endpoints:**
- ApplicationInterviewsListView: `IsAuthenticated` (with role-based access)
- InterviewDetailView: `IsAuthenticated` (with ownership check)
- InterviewStatusUpdateView: `IsAuthenticated, IsRecruiter`

**Notification Endpoints:**
- NotificationListView: `IsAuthenticated`
- MarkAsReadView: `IsAuthenticated`
- MarkAllAsReadView: `IsAuthenticated`
- UnreadCountView: `IsAuthenticated`

**Analytics Endpoints:**
- RecruiterDashboardView: `IsAuthenticated, IsRecruiter`
- CandidateDashboardView: `IsAuthenticated, IsCandidate`
- JobAnalyticsView: `IsAuthenticated, IsRecruiter, IsJobOwner`
- TopCandidatesView: `IsAuthenticated, IsRecruiter, IsJobOwner`

**Admin Endpoints:**
- All admin views: `IsAdmin`

**Audit Result:**
- ✅ No accidental `AllowAny` on protected endpoints
- ✅ All endpoints have explicit permission classes
- ✅ Role-based access control properly implemented
- ✅ Ownership checks in view logic where needed
- ✅ Public authentication endpoints correctly use `AllowAny`

---

## Serializer Hardening

### Current State

All serializers already follow security best practices:

1. **Explicit Field Lists**: No use of `__all__`
2. **Read-Only Fields**: Sensitive fields marked as `read_only=True`
3. **No Mass Assignment**: Explicit field definitions prevent mass assignment
4. **Nested Serialization**: Proper handling of nested objects

**Example from ResumeUploadSerializer:**
```python
class ResumeUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    
    def validate_file(self, value):
        validate_resume_file(value)
        return value
```

**Audit Result:**
- ✅ All serializers use explicit field lists
- ✅ No `__all__` usage found
- ✅ Read-only fields properly marked
- ✅ File validation integrated
- ✅ No mass assignment vulnerabilities

---

## Security Audit Logging

### Implementation in matchhire_backend/core/security_audit.py

**SecurityAuditService** provides logging for:

1. **Failed Login Attempts**: `log_failed_login(email, ip_address)`
2. **Permission Denied**: `log_permission_denied(user_id, endpoint, method)`
3. **Invalid Upload**: `log_invalid_upload(user_id, filename, reason)`
4. **Rate Limit Exceeded**: `log_rate_limit_exceeded(user_id, scope, endpoint)`
5. **Invalid Status Transition**: `log_invalid_status_transition(user_id, resource_type, resource_id, from_status, to_status)`
6. **Invalid Moderation**: `log_invalid_moderation_attempt(admin_id, resource_type, resource_id, action)`
7. **Suspicious Activity**: `log_suspicious_activity(user_id, activity_type, details)`

**Integration:**
- Integrated into LoginView for failed login logging
- Uses Python's standard logging infrastructure
- No database model required
- Logs can be configured to file, syslog, or other handlers

---

## Password Validators

### Configuration in settings/base.py

```python
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
```

**Validators:**
1. **UserAttributeSimilarityValidator**: Prevents passwords similar to user attributes (email, name)
2. **MinimumLengthValidator**: Enforces minimum password length (default 8)
3. **CommonPasswordValidator**: Prevents common passwords from breach lists
4. **NumericPasswordValidator**: Prevents purely numeric passwords

**Audit Result:**
- ✅ All recommended Django password validators enabled
- ✅ Covers similarity, length, common passwords, and numeric passwords

---

## JWT Configuration

### Configuration in settings/base.py

```python
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

JWT_ACCESS_COOKIE_NAME = "access_token"
JWT_REFRESH_COOKIE_NAME = "refresh_token"
JWT_COOKIE_SAMESITE = "Lax"
JWT_COOKIE_SECURE = not DEBUG
```

**Security Settings:**
- **Access Token Lifetime**: 15 minutes (short-lived for security)
- **Refresh Token Lifetime**: 7 days (balance between security and UX)
- **Token Rotation**: Enabled (rotates refresh tokens on use)
- **Blacklist After Rotation**: Enabled (old tokens invalidated)
- **Cookie Security**: Secure flag enabled in production
- **SameSite**: Lax (CSRF protection)

**Audit Result:**
- ✅ Short access token lifetime (15 min)
- ✅ Refresh token rotation enabled
- ✅ Blacklist after rotation enabled
- ✅ Secure cookies in production
- ✅ SameSite protection

---

## API Versioning

### Implementation in settings/base.py

```python
REST_FRAMEWORK = {
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.URLPathVersioning",
    "DEFAULT_VERSION": "v1",
    "ALLOWED_VERSIONS": ["v1"],
    "VERSION_PARAM": "version",
}
```

### URL Configuration in urls.py

```python
urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("matchhire_backend.api.urls")),
    path("api/", include("matchhire_backend.api.urls")),  # Backward compatibility
]
```

**Versioning Strategy:**
- **URL Path Versioning**: Version in URL path (e.g., `/api/v1/jobs/`)
- **Current Version**: v1
- **Backward Compatibility**: `/api/` path maintained for existing clients
- **Migration Path**: Clients can migrate from `/api/` to `/api/v1/` at their pace

**Audit Result:**
- ✅ URL-based versioning implemented
- ✅ Backward compatibility maintained
- ✅ Clear migration path for clients

---

## Exception Handler

### Implementation in matchhire_backend/core/exceptions.py

**custom_exception_handler** provides consistent error responses:

**Error Response Format:**
```json
{
    "error": {
        "code": "ERROR_CODE",
        "message": "User-friendly message",
        "details": {...}
    }
}
```

**Error Codes:**
- `VALIDATION_ERROR`: Input validation failed
- `AUTHENTICATION_FAILED`: Authentication failed
- `PERMISSION_DENIED`: Permission denied
- `RATE_LIMIT_EXCEEDED`: Rate limit exceeded
- `NOT_FOUND`: Resource not found
- `INTERNAL_ERROR`: Internal server error

**Features:**
- Consistent error format across all endpoints
- User-friendly error messages
- Detailed error information when available
- Automatic logging of exceptions

---

## Query Optimization Verification

**Query Optimization Status:**
- ✅ No changes to existing query optimization
- ✅ All `select_related` and `prefetch_related` maintained
- ✅ No additional queries introduced by security changes
- ✅ Security validation is in-memory only (no DB queries)

**Examples of Maintained Optimization:**
- JobDetailView: `select_related("recruiter")`
- ApplicationDetailView: `select_related("job", "candidate", "resume_version")`
- InterviewDetailView: `select_related("application", "application__candidate", "application__job")`
- Admin views: Appropriate `select_related` for all queries

---

## Test Coverage

### Security Tests Created

**File: matchhire_backend/core/tests.py**

**Test Classes (45+ tests):**

1. **ValidatorsTest** (11 tests):
   - UUID validation (valid, invalid format)
   - Pagination validation (valid, invalid page, invalid size, size exceeds max)
   - Ordering validation (valid, invalid)
   - Search length validation (valid, exceeds max)
   - Boolean validation (true, false, invalid)
   - Choice validation (valid, invalid)

2. **SecurityAuditServiceTest** (7 tests):
   - Failed login logging
   - Permission denied logging
   - Invalid upload logging
   - Rate limit exceeded logging
   - Invalid status transition logging
   - Invalid moderation attempt logging
   - Suspicious activity logging

3. **ThrottleClassesTest** (12 tests):
   - All throttle classes have correct scope

4. **FileUploadValidationTest** (3 tests):
   - Valid PDF upload
   - Dangerous extension rejection
   - Oversized file rejection

5. **APIVersioningTest** (2 tests):
   - v1 API accessible
   - Backward compatibility

6. **PermissionAuditTest** (4 tests):
   - Login allows anonymous
   - Protected endpoint requires auth
   - Candidate endpoint requires candidate role
   - Recruiter endpoint requires recruiter role

7. **UUIDValidationTest** (2 tests):
   - Invalid UUID returns 400
   - Valid UUID format accepted

8. **SecurityHeadersTest** (1 test):
   - Security headers in production

9. **PasswordValidatorsTest** (1 test):
   - Password validators configured

10. **JWTConfigurationTest** (4 tests):
    - Access token lifetime
    - Refresh token lifetime
    - Rotation enabled
    - Blacklist enabled

11. **CORSConfigurationTest** (2 tests):
    - CORS uses whitelist
    - Credentials allowed

12. **ExceptionHandlerTest** (1 test):
    - Validation error format

13. **ThrottlingIntegrationTest** (2 tests):
    - Login endpoint has throttle scope
    - Registration endpoints have throttle scope

14. **DRFSettingsTest** (3 tests):
    - Throttle classes configured
    - Exception handler configured
    - Versioning configured

**Total Tests: 45+**

---

## Approval Checklist

### Completed Items

- [x] Configure DRF throttling with custom throttle classes
- [x] Assign throttle_scope to all endpoints
- [x] Implement file upload hardening (MIME, extension, size, signature)
- [x] Implement request validation (UUID, pagination, ordering, search)
- [x] Configure security headers in Django settings
- [x] Review and fix CORS configuration
- [x] Audit permissions on all endpoints
- [x] Harden serializers (read-only fields, prevent mass assignment)
- [x] Create SecurityAuditService for logging security events
- [x] Verify password validators configuration
- [x] Review JWT configuration
- [x] Implement API versioning
- [x] Create centralized DRF exception handler
- [x] Write 45+ security tests
- [x] Verify query optimization unchanged
- [x] Generate output documentation

### Pending Items

- [ ] Run makemigrations --check
- [ ] Run migrate
- [ ] Run test
- [ ] Git commit with specified message

---

## Files Created/Modified

### New Files Created

1. `matchhire_backend/core/throttling.py` - Custom DRF throttle classes
2. `matchhire_backend/core/security_audit.py` - Security audit logging service
3. `matchhire_backend/core/exceptions.py` - Centralized exception handler
4. `matchhire_backend/core/validators.py` - Request validation utilities
5. `matchhire_backend/core/tests.py` - Security tests (45+ tests)

### Files Modified

1. `matchhire_backend/settings/base.py`:
   - Added REST_FRAMEWORK throttling configuration
   - Added REST_FRAMEWORK exception handler
   - Added REST_FRAMEWORK versioning configuration
   - Password validators already configured (verified)
   - JWT configuration already secure (verified)
   - CORS already using whitelist (verified)

2. `matchhire_backend/settings/prod.py`:
   - Added SECURE_CONTENT_TYPE_NOSNIFF
   - Added SECURE_BROWSER_XSS_FILTER
   - Added SECURE_REFERRER_POLICY
   - Added SECURE_PROXY_SSL_HEADER

3. `matchhire_backend/urls.py`:
   - Added `/api/v1/` path for versioned API
   - Maintained `/api/` for backward compatibility

4. `apps/resumes/services/validators.py`:
   - Added MIME type validation
   - Added dangerous extension rejection
   - Added TXT file support
   - Enhanced file signature verification

5. `apps/users/auth_views.py`:
   - Added SecurityAuditService import
   - Added failed login logging
   - Added throttle_scope to LoginView
   - Added throttle_scope to registration views

6. `apps/resumes/views.py`:
   - Added validation utilities import
   - Added UUID validation to all UUID-accepting views
   - Added ordering and search validation
   - Added throttle_scope to all views

7. `apps/jobs/views.py`:
   - Added validation utilities import
   - Added UUID validation to all UUID-accepting views
   - Added search length validation
   - Added ordering validation
   - Added throttle_scope to all views

8. `apps/applications/views.py`:
   - Added validation utilities import
   - Added UUID validation to all UUID-accepting views
   - Added throttle_scope to all views

9. `apps/interviews/views.py`:
   - Added validation utilities import
   - Added UUID validation to all UUID-accepting views
   - Added throttle_scope to all views

10. `apps/notifications/views.py`:
    - Added throttle_scope to all views

11. `apps/analytics/views.py`:
    - Added throttle_scope to all views

12. `apps/admin/views.py`:
    - Added throttle_scope to all views

---

## Next Steps

1. **Run makemigrations --check**: Verify no database migrations needed
2. **Run migrate**: Verify migrations apply successfully
3. **Run test**: Execute security tests and verify all pass
4. **Git commit**: Commit with message: `feat(phase-3-task-4.12): implement api hardening and security`

---

## Summary

The MatchHire backend has been successfully hardened with comprehensive security measures:

- **Rate Limiting**: 13 custom throttle classes with scoped limits
- **File Upload**: Multi-layer validation (MIME, extension, size, signature)
- **Request Validation**: UUID, pagination, ordering, search validation
- **Security Headers**: Production-grade HTTP headers
- **CORS**: Whitelist-based configuration
- **Permissions**: Explicit role-based access control
- **Serializers**: Hardened with explicit fields and read-only attributes
- **Audit Logging**: Centralized security event logging
- **Password Validation**: All Django validators enabled
- **JWT**: Secure configuration with rotation and blacklisting
- **API Versioning**: URL-based versioning with backward compatibility
- **Exception Handling**: Consistent error responses
- **Tests**: 45+ comprehensive security tests

All security improvements maintain backward compatibility and do not affect query optimization.
