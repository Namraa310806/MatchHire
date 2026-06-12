"""
MatchHire RBAC Documentation

This module documents the centralized Role-Based Access Control (RBAC) system
for the MatchHire application. All authorization logic is implemented in
apps/users/permissions.py and should be reused across all modules.

AVAILABLE PERMISSIONS
====================

Base Permissions:
-----------------

1. IsCandidate
   - Purpose: Restrict access to candidates only
   - Allows: role == CANDIDATE
   - Denies: All other roles and anonymous users
   - Use Case: Candidate-specific endpoints (resume upload, profile management)

2. IsRecruiter
   - Purpose: Restrict access to recruiters only
   - Allows: role == RECRUITER
   - Denies: All other roles and anonymous users
   - Use Case: Recruiter-specific endpoints (job posting, candidate search)

3. IsVerifiedUser
   - Purpose: Restrict access to verified users only
   - Allows: user.is_verified == True
   - Denies: Unverified users and anonymous users
   - Use Case: Sensitive operations requiring verification

4. IsProfileOwner
   - Purpose: Object-level permission for profile ownership
   - Allows: obj.user == request.user
   - Denies: Non-owners
   - Use Case: Profile update/delete operations
   - Note: This is an object-level permission (has_object_permission)

5. ReadOnly
   - Purpose: Allow read-only access
   - Allows: GET, HEAD, OPTIONS
   - Denies: POST, PUT, PATCH, DELETE
   - Use Case: Public read endpoints with no write access

Composite Permissions:
---------------------

6. CandidateAndVerified
   - Purpose: Restrict access to verified candidates only
   - Allows: role == CANDIDATE AND is_verified == True
   - Denies: All other combinations
   - Use Case: High-value candidate operations (e.g., applying to jobs)

7. RecruiterAndVerified
   - Purpose: Restrict access to verified recruiters only
   - Allows: role == RECRUITER AND is_verified == True
   - Denies: All other combinations
   - Use Case: High-value recruiter operations (e.g., contacting candidates)

USAGE EXAMPLES
==============

Basic Role Restriction:
-----------------------

from rest_framework import viewsets
from apps.users.permissions import IsCandidate

class CandidateResumeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsCandidate]
    # Only candidates can access this endpoint

Composite Permission:
---------------------

from apps.users.permissions import CandidateAndVerified

class JobApplicationViewSet(viewsets.ModelViewSet):
    permission_classes = [CandidateAndVerified]
    # Only verified candidates can apply to jobs

Object-Level Permission:
------------------------

from apps.users.permissions import IsProfileOwner

class ProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsProfileOwner]
    # Users can only access their own profiles

Read-Only Access:
-----------------

from apps.users.permissions import ReadOnly

class PublicJobListView(generics.ListAPIView):
    permission_classes = [ReadOnly]
    # Anyone can read, but no one can write

Multiple Permissions (AND Logic):
---------------------------------

from apps.users.permissions import IsRecruiter, IsVerifiedUser

class RecruiterDashboardView(generics.RetrieveAPIView):
    permission_classes = [IsRecruiter, IsVerifiedUser]
    # Equivalent to RecruiterAndVerified

INTENDED USE CASES BY MODULE
============================

Resume Module:
- IsCandidate: For resume upload/management
- IsProfileOwner: For resume ownership verification

Jobs Module:
- IsRecruiter: For job posting/management
- ReadOnly: For public job listings
- IsProfileOwner: For job ownership verification

Matching Module:
- CandidateAndVerified: For accessing match results
- RecruiterAndVerified: For accessing candidate matches

Recruiter Tools:
- IsRecruiter: For recruiter-specific tools
- RecruiterAndVerified: For advanced recruiter features

Application Module:
- CandidateAndVerified: For submitting applications
- IsRecruiter: For reviewing applications

Notifications Module:
- IsProfileOwner: For accessing own notifications

SECURITY PRINCIPLES
==================

1. Centralization: All authorization logic lives in permissions.py
2. No Role Checks in Views: Views should only declare permission_classes
3. Composability: Permissions can be combined using AND logic
4. Object-Level Security: Use has_object_permission for ownership checks
5. Reusability: Permissions are designed for reuse across modules

ERROR RESPONSES
==============

- 401 Unauthorized: User is not authenticated
- 403 Forbidden: User is authenticated but lacks permission

These follow DRF standards and are automatically handled by the
permission classes.

TESTING
=======

Test endpoints are available at:
- /api/rbac/candidate-only/
- /api/rbac/recruiter-only/
- /api/rbac/verified-only/

These endpoints exist solely for validation and should not be used
in production.

For comprehensive test coverage, see apps/users/tests.py.
"""
