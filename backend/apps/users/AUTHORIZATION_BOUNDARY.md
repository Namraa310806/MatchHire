# MatchHire Authentication & Authorization Boundary

## Phase 3D Final Documentation

This document establishes the authentication and authorization boundary for MatchHire.
It serves as the contract for all future development phases.

---

## Authentication vs Authorization

### Authentication: "Who is this user?"

Authentication establishes identity via:
- Email/password credentials
- JWT access tokens (stored in HttpOnly cookies)
- JWT refresh tokens (stored in HttpOnly cookies with path scoping)

Authentication sets `request.user` in Django views.

### Authorization: "What is this authenticated user allowed to do?"

Authorization determines permissions:
- Is the request authenticated?
- Does the user have permission to perform this operation?
- Does the user own the resource being accessed?

Authentication alone does NOT grant permission to perform arbitrary actions.

---

## REST Framework Default Permission Policy

**Current Configuration:**
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.users.authentication.CookieJWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

**Policy:**
- Default API permission is `IsAuthenticated` (secure default)
- Protected application APIs require authentication by default
- Public endpoints must explicitly opt into `AllowAny`
- Future business APIs will be protected unless explicitly marked public

**Rationale:**
This prevents accidental exposure of future business APIs. Developers must explicitly make an endpoint public.

---

## Endpoint Classification

### PUBLIC ENDPOINTS (AllowAny)

These endpoints are explicitly public and do not require authentication:

1. **GET /api/health/**
   - Purpose: Health check for monitoring
   - Permission: `@permission_classes([AllowAny])`
   - Rationale: Monitoring systems need to check service health without authentication
   - Security: Reports dependency health (database, Redis) but never exposes credentials

2. **POST /api/auth/register/**
   - Purpose: User registration
   - Permission: `permission_classes = []` (equivalent to AllowAny)
   - CSRF: Exempt (no session exists yet)
   - Rationale: New users cannot have authentication credentials

3. **POST /api/auth/login/**
   - Purpose: User login with email/password
   - Permission: `permission_classes = []` (equivalent to AllowAny)
   - CSRF: Exempt (establishes initial authentication)
   - Rationale: Users authenticate with credentials, not session cookies

4. **POST /api/auth/refresh/**
   - Purpose: Refresh JWT access token
   - Permission: `permission_classes = []` (equivalent to AllowAny)
   - CSRF: Exempt (token renewal, not state-changing business operation)
   - Rationale: Token rotation provides replay protection via blacklisting
   - Security: Refresh token is path-scoped to `/api/auth/refresh/`

### PROTECTED ENDPOINTS (IsAuthenticated)

These endpoints require valid JWT authentication:

1. **POST /api/auth/logout/**
   - Purpose: Revoke refresh token and clear cookies
   - Permission: `permission_classes = []` (accepts any request, but validates token)
   - CSRF: Exempt (logout operation that terminates authentication)
   - Security: Revokes refresh token via blacklist, clears HttpOnly cookies

2. **GET /api/auth/me/**
   - Purpose: Retrieve current user's identity
   - Permission: `permission_classes = [IsAuthenticated]`
   - CSRF: Not exempt (future state-changing endpoints must enforce CSRF)
   - Security: Returns only safe user data (id, email)

---

## User Ownership Boundary

### User → UserProfile Relationship

```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
```

### Ownership Principle

**Future APIs MUST derive ownership from `request.user`, not from client-supplied IDs.**

**BAD (Do NOT do this):**
```python
# Allows one candidate to access another candidate's data
GET /api/profile/?user_id=123
def profile_view(request):
    user_id = request.query_params.get('user_id')
    profile = UserProfile.objects.get(user_id=user_id)  # DANGEROUS
```

**GOOD (Do this):**
```python
# Server derives ownership from authenticated identity
GET /api/profile/
def profile_view(request):
    profile = request.user.profile  # SAFE
```

### Rule

For resources with ownership:
- Authorization must be checked server-side
- Object ownership derives from `request.user`
- Do not trust arbitrary client-supplied `user_id` parameters
- Future profile APIs should operate on the authenticated user's own profile

---

## Django User Model Roles

### Built-in Django Roles (Only These Exist)

- **is_active**: Account status (inactive users cannot authenticate)
- **is_staff**: Can access Django admin interface
- **is_superuser**: Full administrative permissions

### No Additional Roles

The current project does NOT have:
- Recruiter
- Employer
- CompanyAdmin
- HiringManager

**Future Rule:** Do not introduce recruiter/employer personas unless the project documentation explicitly changes.

---

## MatchHire Domain Rule

### Job Creation Boundary

**CRITICAL:** MatchHire jobs come from official company sources.

- No normal application user can create arbitrary jobs
- No `POST /api/jobs/` endpoint exists for candidates
- Job ingestion is a platform-controlled process
- Future job ingestion will use the verified-source ingestion pipeline

**Future Rule:** Candidates cannot create jobs. Jobs originate from the platform's verified ingestion pipeline and official company sources.

---

## Django Admin Security

### Current Configuration

- Password field handled by Django's built-in password change mechanism
- Password is not exposed as an editable plaintext field
- Password hash is managed by Django (not directly editable)
- UserProfile is displayed as inline

### Security Review

✅ Password is not editable as plaintext
✅ Password hash is not unnecessarily exposed
✅ Sensitive security fields are not casually editable
✅ UserProfile relationship remains understandable

**No changes needed.**

---

## User Serialization Security

### SafeUserSerializer

```python
class SafeUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email']
        read_only_fields = ['id', 'email']
```

**Exposes only:**
- `id`: User identifier
- `email`: User email

**Never exposes:**
- Password
- Password hash
- last_login (unless genuinely needed)
- Internal permission information
- Authentication secrets

**No changes needed.**

---

## Authentication Error Consistency

### Current Behavior

**Registration:**
- Reports duplicate email (necessary for user feedback)
- Generic validation errors for other issues

**Login:**
- Generic error: "Invalid email or password."
- Does NOT reveal:
  - Whether email exists
  - Whether password is wrong
  - Whether user is inactive

**Rationale:** Prevents account enumeration attacks.

**No changes needed.**

---

## CSRF Boundary

### Current Configuration

- CSRF middleware is globally enabled in settings
- Authentication endpoints are `csrf_exempt` with documented rationale
- Future state-changing authenticated endpoints MUST enforce CSRF protection

### CSRF Exemption Rationale

Authentication endpoints are exempt because:
1. They do not establish authenticated browser sessions
2. They do not operate on existing authenticated state
3. JWT tokens are stored in HttpOnly cookies, not used as CSRF tokens
4. They explicitly validate credentials/tokens

### Future Rule

**Future state-changing cookie-authenticated endpoints must enforce appropriate CSRF protection.**
Do NOT use `csrf_exempt` for business operations.

---

## CORS Boundary

### Current Configuration

```python
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
]
CORS_ALLOW_CREDENTIALS = True
```

**Security Properties:**
✅ Explicit allowed origins (no wildcard)
✅ Credentials allowed (required for HttpOnly cookies)
✅ No arbitrary origin reflection
✅ Development frontend origin supported

**Future Rule:** Keep production configuration environment-driven. Do not broaden CORS for convenience.

---

## Cookie Security

### Access Token Cookie

- HttpOnly: ✅ Yes
- Secure: ✅ Yes in production (DEBUG=False), No in development
- SameSite: ✅ Lax
- Path: ✅ /

### Refresh Token Cookie

- HttpOnly: ✅ Yes
- Secure: ✅ Yes in production (DEBUG=False), No in development
- SameSite: ✅ Lax
- Path: ✅ /api/auth/refresh/ (scoped)

**No changes needed.**

---

## JWT Claims

### Current Payload

JWT contains only identity/security information:
- `user_id`: User identifier
- `exp`: Expiration timestamp
- Standard JWT claims

**JWT does NOT include:**
- Resume data
- Skills
- Keywords
- MatchScores
- Subscriptions
- Profile information
- Job information

**Rationale:** JWT should identify the user, not become a database snapshot.

**No changes needed.**

---

## Password Security

### Current Implementation

✅ Password hashing managed by Django
✅ UserManager used for user creation
✅ Django password validators configured
✅ Raw passwords never persisted
✅ Password confirmation never persisted
✅ Password values not logged
✅ Password hashes not returned through APIs

**No changes needed.**

---

## Future Phase Contract

### RULE 1: Do not create a second User model.
### RULE 2: Do not put professional profile data into User.
### RULE 3: Do not expose passwords or password hashes.
### RULE 4: Do not put profile/resume/matching information into JWT claims.
### RULE 5: Do not store JWTs in localStorage/sessionStorage.
### RULE 6: Do not make protected APIs public by default.
### RULE 7: Public endpoints must explicitly use AllowAny.
### RULE 8: Future state-changing cookie-authenticated endpoints must enforce appropriate CSRF protection.
### RULE 9: Object ownership must derive from authenticated identity rather than trusting arbitrary client user IDs.
### RULE 10: Candidates cannot create arbitrary jobs.
### RULE 11: Jobs originate from the platform's verified ingestion pipeline and official company sources.
### RULE 12: Do not introduce recruiter/employer personas unless the project documentation explicitly changes.

---

## Final Architecture

```
                    REQUEST
                       │
                       ↓
                Django / DRF
                       │
             ┌─────────┴─────────┐
             ↓                   ↓
       Authentication       Permissions
             │                   │
             ↓                   ↓
         request.user       allowed?
             │                   │
             └─────────┬─────────┘
                       ↓
                 API operation
```

**Authentication answers:** "Who are you?"
**Authorization answers:** "Are you allowed to perform this operation?"

These responsibilities remain separate.
