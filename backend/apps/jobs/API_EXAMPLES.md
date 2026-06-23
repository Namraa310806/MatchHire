# Job Management API Examples

This document provides example API responses for the Job Management endpoints.

---

## Recruiter Endpoints

### POST /api/jobs/create/ - Create Job

**Request:**
```json
{
  "title": "Senior Software Engineer",
  "company_name": "Tech Corp",
  "location": "San Francisco, CA",
  "employment_type": "full_time",
  "experience_level": "senior",
  "description": "We are looking for a senior software engineer to join our team.",
  "requirements": "5+ years of experience with Python and Django",
  "responsibilities": "Design and implement scalable APIs",
  "salary_min": 120000,
  "salary_max": 180000,
  "currency": "USD",
  "is_remote": true,
  "status": "active"
}
```

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "recruiter_id": "123e4567-e89b-12d3-a456-426614174000",
  "recruiter_email": "recruiter@example.com",
  "title": "Senior Software Engineer",
  "company_name": "Tech Corp",
  "location": "San Francisco, CA",
  "employment_type": "full_time",
  "experience_level": "senior",
  "description": "We are looking for a senior software engineer to join our team.",
  "requirements": "5+ years of experience with Python and Django",
  "responsibilities": "Design and implement scalable APIs",
  "salary_min": "120000.00",
  "salary_max": "180000.00",
  "currency": "USD",
  "is_remote": true,
  "status": "active",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "closed_at": null
}
```

---

### GET /api/jobs/my/ - List Recruiter's Jobs

**Response (200 OK):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "recruiter_id": "123e4567-e89b-12d3-a456-426614174000",
    "recruiter_email": "recruiter@example.com",
    "title": "Senior Software Engineer",
    "company_name": "Tech Corp",
    "location": "San Francisco, CA",
    "employment_type": "full_time",
    "experience_level": "senior",
    "status": "active",
    "is_remote": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "recruiter_id": "123e4567-e89b-12d3-a456-426614174000",
    "recruiter_email": "recruiter@example.com",
    "title": "Junior Developer",
    "company_name": "Tech Corp",
    "location": "Remote",
    "employment_type": "full_time",
    "experience_level": "junior",
    "status": "draft",
    "is_remote": true,
    "created_at": "2024-01-14T09:00:00Z",
    "updated_at": "2024-01-14T09:00:00Z"
  }
]
```

---

### GET /api/jobs/<id>/ - Retrieve Job Detail

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "recruiter_id": "123e4567-e89b-12d3-a456-426614174000",
  "recruiter_email": "recruiter@example.com",
  "title": "Senior Software Engineer",
  "company_name": "Tech Corp",
  "location": "San Francisco, CA",
  "employment_type": "full_time",
  "experience_level": "senior",
  "description": "We are looking for a senior software engineer to join our team.",
  "requirements": "5+ years of experience with Python and Django",
  "responsibilities": "Design and implement scalable APIs",
  "salary_min": "120000.00",
  "salary_max": "180000.00",
  "currency": "USD",
  "is_remote": true,
  "status": "active",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "closed_at": null
}
```

---

### PATCH /api/jobs/<id>/ - Update Job

**Request:**
```json
{
  "title": "Lead Software Engineer",
  "salary_max": 200000
}
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "recruiter_id": "123e4567-e89b-12d3-a456-426614174000",
  "recruiter_email": "recruiter@example.com",
  "title": "Lead Software Engineer",
  "company_name": "Tech Corp",
  "location": "San Francisco, CA",
  "employment_type": "full_time",
  "experience_level": "senior",
  "description": "We are looking for a senior software engineer to join our team.",
  "requirements": "5+ years of experience with Python and Django",
  "responsibilities": "Design and implement scalable APIs",
  "salary_min": "120000.00",
  "salary_max": "200000.00",
  "currency": "USD",
  "is_remote": true,
  "status": "active",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:00:00Z",
  "closed_at": null
}
```

---

### POST /api/jobs/<id>/close/ - Close Job

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "recruiter_id": "123e4567-e89b-12d3-a456-426614174000",
  "recruiter_email": "recruiter@example.com",
  "title": "Senior Software Engineer",
  "company_name": "Tech Corp",
  "location": "San Francisco, CA",
  "employment_type": "full_time",
  "experience_level": "senior",
  "description": "We are looking for a senior software engineer to join our team.",
  "requirements": "5+ years of experience with Python and Django",
  "responsibilities": "Design and implement scalable APIs",
  "salary_min": "120000.00",
  "salary_max": "180000.00",
  "currency": "USD",
  "is_remote": true,
  "status": "closed",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "closed_at": "2024-01-20T15:45:00Z"
}
```

---

## Candidate Endpoints

### GET /api/jobs/ - List Active Jobs

**Response (200 OK):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "recruiter_id": "123e4567-e89b-12d3-a456-426614174000",
    "recruiter_email": "recruiter@example.com",
    "title": "Senior Software Engineer",
    "company_name": "Tech Corp",
    "location": "San Francisco, CA",
    "employment_type": "full_time",
    "experience_level": "senior",
    "status": "active",
    "is_remote": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "recruiter_id": "223e4567-e89b-12d3-a456-426614174001",
    "recruiter_email": "recruiter2@example.com",
    "title": "Product Manager",
    "company_name": "Startup Inc",
    "location": "New York, NY",
    "employment_type": "full_time",
    "experience_level": "mid",
    "status": "active",
    "is_remote": false,
    "created_at": "2024-01-16T14:00:00Z",
    "updated_at": "2024-01-16T14:00:00Z"
  }
]
```

**Note:** Only jobs with `status: "active"` are returned. Draft and closed jobs are hidden from candidates.

---

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Job not found"
}
```

### 400 Bad Request - Validation Error
```json
{
  "title": [
    "Title is required."
  ],
  "salary_min": [
    "salary_min must be less than or equal to salary_max"
  ]
}
```

### 400 Bad Request - Already Closed
```json
{
  "detail": "Job is already closed."
}
```

---

## Enum Values

### Employment Type
- `full_time` - Full Time
- `part_time` - Part Time
- `contract` - Contract
- `internship` - Internship

### Experience Level
- `entry` - Entry Level
- `junior` - Junior
- `mid` - Mid Level
- `senior` - Senior
- `lead` - Lead

### Job Status
- `draft` - Draft (not visible to candidates)
- `active` - Active (visible to candidates)
- `closed` - Closed (not visible to candidates)
