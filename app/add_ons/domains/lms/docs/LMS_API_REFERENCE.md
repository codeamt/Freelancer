# LMS API Reference

Complete API documentation for the LMS add-on endpoints.

## Base URL

All LMS endpoints are prefixed with `/lms`

```
http://localhost:8002/lms
```

## Authentication

Most endpoints require authentication via session cookies. Ensure users are logged in before accessing protected endpoints.

---

## 📚 Course Endpoints

### List Courses

Get a paginated list of courses with optional filters.

**Endpoint:** `GET /lms/courses`

**Query Parameters:**
- `page` (integer, optional) - Page number (default: 1)
- `page_size` (integer, optional) - Items per page (default: 20)
- `status` (string, optional) - Filter by status: `draft`, `published`, `archived`
- `category` (string, optional) - Filter by category
- `search` (string, optional) - Search in course titles

**Response:**
```json
{
  "courses": [
    {
      "id": 1,
      "title": "Python for Beginners",
      "description": "Learn Python from scratch",
      "thumbnail_url": "https://...",
      "price": 49.99,
      "currency": "USD",
      "difficulty": "beginner",
      "category": "programming",
      "instructor_id": 1
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

**Example:**
```bash
curl http://localhost:8002/lms/courses?category=programming&page=1
```

---

### Get Course Details

Get detailed information about a specific course.

**Endpoint:** `GET /lms/courses/{course_id}`

**Path Parameters:**
- `course_id` (integer, required) - Course ID

**Response:**
```json
{
  "id": 1,
  "title": "Python for Beginners",
  "description": "Learn Python from scratch...",
  "thumbnail_url": "https://...",
  "price": 49.99,
  "currency": "USD",
  "duration_hours": 10.0,
  "difficulty": "beginner",
  "status": "published",
  "category": "programming",
  "tags": ["python", "programming"],
  "requirements": ["Computer with internet"],
  "learning_objectives": ["Learn Python basics", "Write programs"],
  "instructor": {
    "id": 1,
    "email": "instructor@example.com"
  },
  "stats": {
    "lesson_count": 15,
    "enrollment_count": 234,
    "completed_count": 45,
    "completion_rate": 19.23
  },
  "created_at": "2025-11-29T00:00:00",
  "updated_at": "2025-11-29T00:00:00"
}
```

**Example:**
```bash
curl http://localhost:8002/lms/courses/1
```

---

### Create Course

Create a new course (instructor only).

**Endpoint:** `POST /lms/courses`

**Authentication:** Required (instructor)

**Form Data:**
- `title` (string, required) - Course title
- `description` (string, optional) - Course description
- `price` (float, optional) - Course price (default: 0.0)
- `category` (string, optional) - Course category

**Response:** Redirects to course detail page

**Example:**
```bash
curl -X POST http://localhost:8002/lms/courses \
  -H "Cookie: session=..." \
  -F "title=My New Course" \
  -F "description=Learn amazing things" \
  -F "price=29.99" \
  -F "category=programming"
```

---

### Update Course

Update an existing course (instructor only).

**Endpoint:** `PUT /lms/courses/{course_id}`

**Authentication:** Required (course instructor)

**Path Parameters:**
- `course_id` (integer, required) - Course ID

**Form Data:**
- `title` (string, optional) - New title
- `description` (string, optional) - New description
- `price` (float, optional) - New price
- `status` (string, optional) - New status: `draft`, `published`, `archived`

**Response:** Redirects to course detail page

**Example:**
```bash
curl -X PUT http://localhost:8002/lms/courses/1 \
  -H "Cookie: session=..." \
  -F "title=Updated Course Title" \
  -F "price=39.99"
```

---

### Delete Course

Delete a course (instructor only).

**Endpoint:** `DELETE /lms/courses/{course_id}`

**Authentication:** Required (course instructor)

**Path Parameters:**
- `course_id` (integer, required) - Course ID

**Response:**
```json
{
  "message": "Course deleted successfully"
}
```

**Example:**
```bash
curl -X DELETE http://localhost:8002/lms/courses/1 \
  -H "Cookie: session=..."
```

---

### Publish Course

Publish a draft course (instructor only).

**Endpoint:** `POST /lms/courses/{course_id}/publish`

**Authentication:** Required (course instructor)

**Path Parameters:**
- `course_id` (integer, required) - Course ID

**Response:**
```json
{
  "message": "Course published successfully"
}
```

**Example:**
```bash
curl -X POST http://localhost:8002/lms/courses/1/publish \
  -H "Cookie: session=..."
```

---

## 🎓 Enrollment Endpoints

### Enroll in Course

Enroll the current user in a course.

**Endpoint:** `POST /lms/enroll`

**Authentication:** Required

**Form Data:**
- `course_id` (integer, required) - Course ID to enroll in
- `payment_id` (string, optional) - Payment transaction ID

**Response:** Redirects to course page

**Example:**
```bash
curl -X POST http://localhost:8002/lms/enroll \
  -H "Cookie: session=..." \
  -F "course_id=1" \
  -F "payment_id=stripe_123"
```

---

### Get My Courses

Get all courses the current user is enrolled in.

**Endpoint:** `GET /lms/my-courses`

**Authentication:** Required

**Response:**
```json
{
  "enrollments": [
    {
      "id": 1,
      "course_id": 1,
      "course_title": "Python for Beginners",
      "status": "active",
      "enrolled_at": "2025-11-29T00:00:00",
      "progress_percent": 45.5
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:8002/lms/my-courses \
  -H "Cookie: session=..."
```

---

### Get Course Progress

Get detailed progress for a specific course.

**Endpoint:** `GET /lms/courses/{course_id}/progress`

**Authentication:** Required (must be enrolled)

**Path Parameters:**
- `course_id` (integer, required) - Course ID

**Response:**
```json
{
  "course_id": 1,
  "course_title": "Python for Beginners",
  "enrollment_id": 1,
  "progress_percent": 45.5,
  "completed_lessons": [1, 2, 3, 5],
  "total_lessons": 10,
  "time_spent_minutes": 180,
  "last_accessed": "2025-11-29T12:00:00",
  "next_lesson_id": 4
}
```

**Example:**
```bash
curl http://localhost:8002/lms/courses/1/progress \
  -H "Cookie: session=..."
```

---

### Complete Lesson

Mark a lesson as completed.

**Endpoint:** `POST /lms/lessons/{lesson_id}/complete`

**Authentication:** Required (must be enrolled)

**Path Parameters:**
- `lesson_id` (integer, required) - Lesson ID

**Form Data:**
- `enrollment_id` (integer, required) - Enrollment ID
- `time_spent` (integer, optional) - Time spent in minutes (default: 0)

**Response:**
```json
{
  "message": "Lesson completed",
  "progress_percent": 50.0
}
```

**Example:**
```bash
curl -X POST http://localhost:8002/lms/lessons/5/complete \
  -H "Cookie: session=..." \
  -F "enrollment_id=1" \
  -F "time_spent=30"
```

---

## 🔐 Authentication & Authorization

### Required Permissions

| Endpoint | Permission Required |
|----------|-------------------|
| `GET /lms/courses` | None (public) |
| `GET /lms/courses/{id}` | None (public) |
| `POST /lms/courses` | Authenticated user |
| `PUT /lms/courses/{id}` | Course instructor |
| `DELETE /lms/courses/{id}` | Course instructor |
| `POST /lms/courses/{id}/publish` | Course instructor |
| `POST /lms/enroll` | Authenticated user |
| `GET /lms/my-courses` | Authenticated user |
| `GET /lms/courses/{id}/progress` | Enrolled student |
| `POST /lms/lessons/{id}/complete` | Enrolled student |

### Error Responses

**401 Unauthorized**
```json
{
  "detail": "Not authenticated"
}
```

**403 Forbidden**
```json
{
  "detail": "You must be the instructor of this course"
}
```

**404 Not Found**
```json
{
  "detail": "Course not found"
}
```

**500 Internal Server Error**
```json
{
  "detail": "Failed to create course"
}
```

---

## 📊 Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 303 | Redirect (after form submission) |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 500 | Internal Server Error |

---

## 🔄 Rate Limiting

Currently, no rate limiting is implemented. Consider adding rate limiting for production:

```python
# Example rate limiting (to be implemented)
@limiter.limit("100/hour")
async def list_courses():
    ...
```

---

## 📝 Notes

### Pagination

All list endpoints support pagination:
- Default page size: 20
- Maximum page size: 100
- Use `page` and `page_size` query parameters

### Filtering

Course listing supports multiple filters:
- Combine filters with `&`: `?category=programming&difficulty=beginner`
- Search is case-insensitive
- Filters are applied with AND logic

### Data Formats

- **Dates**: ISO 8601 format (`2025-11-29T12:00:00`)
- **Prices**: Float with 2 decimal places
- **IDs**: Integer
- **Enums**: Lowercase strings

---

## 🧪 Testing with cURL

### Create and Publish a Course

```bash
# 1. Create course
curl -X POST http://localhost:8002/lms/courses \
  -H "Cookie: session=YOUR_SESSION" \
  -F "title=Test Course" \
  -F "description=A test course" \
  -F "price=29.99"

# 2. Publish course
curl -X POST http://localhost:8002/lms/courses/1/publish \
  -H "Cookie: session=YOUR_SESSION"

# 3. List courses
curl http://localhost:8002/lms/courses
```

### Enroll and Track Progress

```bash
# 1. Enroll in course
curl -X POST http://localhost:8002/lms/enroll \
  -H "Cookie: session=YOUR_SESSION" \
  -F "course_id=1"

# 2. Check progress
curl http://localhost:8002/lms/courses/1/progress \
  -H "Cookie: session=YOUR_SESSION"

# 3. Complete a lesson
curl -X POST http://localhost:8002/lms/lessons/1/complete \
  -H "Cookie: session=YOUR_SESSION" \
  -F "enrollment_id=1" \
  -F "time_spent=30"
```

---

## 🔮 Future Endpoints (Planned)

### Lessons
- `GET /lms/courses/{id}/lessons` - List course lessons
- `POST /lms/courses/{id}/lessons` - Create lesson
- `PUT /lms/lessons/{id}` - Update lesson
- `DELETE /lms/lessons/{id}` - Delete lesson

### Assessments
- `GET /lms/courses/{id}/assessments` - List assessments
- `POST /lms/courses/{id}/assessments` - Create assessment
- `POST /lms/assessments/{id}/submit` - Submit assessment
- `GET /lms/assessments/{id}/results` - Get results

### Certificates
- `GET /lms/certificates/{id}` - Get certificate
- `GET /lms/certificates/verify/{code}` - Verify certificate

---

**For more information, see the full LMS documentation in `app/add_ons/lms/README.md`**
