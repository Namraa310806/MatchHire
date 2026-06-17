# Resume Search API - Example Response

## Endpoint
```
GET /api/resumes/search/
```

## Example Request
```
GET /api/resumes/search/?skill=Python&skill=Django&location=San Francisco&ordering=name
```

## Example Response
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "resume_id": "550e8400-e29b-41d4-a716-446655440000",
      "resume_version_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
      "candidate_name": "Full Stack Developer",
      "location": "San Francisco",
      "skills": [
        "Python",
        "Django",
        "React",
        "AWS"
      ],
      "experience_count": 3,
      "education_count": 2,
      "project_count": 5,
      "certification_count": 2
    },
    {
      "resume_id": "550e8400-e29b-41d4-a716-446655440001",
      "resume_version_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c9",
      "candidate_name": "Python Developer",
      "location": "San Francisco",
      "skills": [
        "Python",
        "Django",
        "PostgreSQL"
      ],
      "experience_count": 2,
      "education_count": 1,
      "project_count": 3,
      "certification_count": 1
    }
  ]
}
```

## Example Request with Pagination
```
GET /api/resumes/search/?skill=Python&page=1&page_size=10
```

## Example Response with Pagination
```json
{
  "count": 45,
  "next": "http://localhost:8000/api/resumes/search/?skill=Python&page=2&page_size=10",
  "previous": null,
  "results": [
    {
      "resume_id": "550e8400-e29b-41d4-a716-446655440000",
      "resume_version_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
      "candidate_name": "Python Developer",
      "location": "San Francisco",
      "skills": ["Python", "Django", "AWS"],
      "experience_count": 3,
      "education_count": 1,
      "project_count": 4,
      "certification_count": 2
    }
    // ... 9 more results
  ]
}
```

## Example Request with Multiple Filters
```
GET /api/resumes/search/?skill=Python&location=Ahmedabad&education=Bachelor
```

## Example Response (Empty)
```
GET /api/resumes/search/?skill=NonExistentSkill
```

```json
{
  "count": 0,
  "next": null,
  "previous": null,
  "results": []
}
```

## Example Error Response (Invalid Ordering)
```
GET /api/resumes/search/?ordering=invalid_field
```

```json
{
  "detail": "Invalid ordering field: invalid_field. Valid fields: name, -name, created_at, -created_at"
}
```

## Example Error Response (Unauthorized - Candidate)
```
GET /api/resumes/search/
```
(As a candidate user)

```json
{
  "detail": "You do not have permission to perform this action."
}
```

## Example Error Response (Unauthorized - Anonymous)
```
GET /api/resumes/search/
```
(As anonymous user)

```json
{
  "detail": "Authentication credentials were not provided."
}
```

## Response Fields Description

| Field | Type | Description |
|-------|------|-------------|
| `resume_id` | UUID | Unique identifier of the resume container |
| `resume_version_id` | UUID | Unique identifier of the resume version |
| `candidate_name` | string | Full name of the candidate |
| `location` | string | Candidate's location |
| `skills` | array[string] | List of candidate's skills |
| `experience_count` | integer | Number of work experience entries |
| `education_count` | integer | Number of education entries |
| `project_count` | integer | Number of project entries |
| `certification_count` | integer | Number of certification entries |
| `count` | integer | Total number of results (pagination) |
| `next` | string/null | URL to next page (pagination) |
| `previous` | string/null | URL to previous page (pagination) |

## Supported Query Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `skill` | string | Filter by skill name (can be multiple) | `?skill=Python&skill=Django` |
| `location` | string | Filter by location | `?location=Ahmedabad` |
| `company` | string | Filter by company name | `?company=Google` |
| `education` | string | Filter by education degree or institution | `?education=Bachelor` |
| `certification` | string | Filter by certification name or issuer | `?certification=AWS` |
| `ordering` | string | Order results (name, -name, created_at, -created_at) | `?ordering=name` |
| `page` | integer | Page number (pagination) | `?page=2` |
| `page_size` | integer | Results per page (default: 20, max: 100) | `?page_size=50` |

## Permission Requirements

- **Authentication**: Required
- **Role**: Recruiter only
- **Candidates**: Blocked (403 Forbidden)
- **Anonymous**: Blocked (401 Unauthorized)
