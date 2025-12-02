# LMS Example - Learning Management System

A complete, standalone learning platform example demonstrating auth integration and course management.

## Features

- ✅ **Public Course Catalog** - Anyone can browse courses
- ✅ **Auth-Protected Enrollment** - Must login to enroll
- ✅ **Progress Tracking** - Track learning progress
- ✅ **Instructor Profiles** - View instructor information
- ✅ **Course Ratings** - See student ratings and reviews
- ✅ **Modern UI** - MonsterUI + Tailwind CSS
- ✅ **HTMX Integration** - Dynamic enrollment without page reload
- ✅ **Responsive Design** - Mobile-friendly

## Quick Start

### Mounted in app.py:

```python
from examples.lms import create_lms_app

# Create the LMS app
lms_app = create_lms_app()

# Mount at /lms-example
app.mount("/lms-example", lms_app)
```

### Access:
Visit: **http://localhost:5001/lms-example**

## User Flow

### Without Authentication:
1. Browse course catalog ✓
2. View course details ✓
3. Click "Enroll" → Prompted to sign in
4. Click "Sign In" → Redirected to login
5. After login → Redirected back to LMS

### With Authentication:
1. Browse courses ✓
2. Click "Enroll Now" → Enrolled instantly ✓
3. View "My Courses" → See enrolled courses ✓
4. Track progress ✓
5. Continue learning ✓

## Sample Courses

The example includes 4 sample courses:
- **Introduction to Python** - $49.99 (Beginner, 8 weeks, 42 lessons)
- **Web Development Bootcamp** - $79.99 (Intermediate, 12 weeks, 68 lessons)
- **Data Science Fundamentals** - $99.99 (Intermediate, 10 weeks, 55 lessons)
- **Mobile App Development** - $89.99 (Advanced, 10 weeks, 48 lessons)

## Customization for Clients

### 1. Replace Courses

Edit `COURSES` in `app.py`:

```python
COURSES = [
    {
        "id": 1,
        "title": "Your Course",
        "description": "Course description",
        "instructor": "Instructor Name",
        "duration": "8 weeks",
        "level": "Beginner",
        "price": 49.99,
        "image": "https://your-image-url.com",
        "enrolled": 0,
        "rating": 5.0,
        "lessons": 20
    },
    # Add more courses...
]
```

### 2. Add Real Course Content

```python
@app.get("/course/{course_id}")
async def course_detail(course_id: int):
    course = get_course(course_id)
    lessons = get_course_lessons(course_id)
    
    return Div(
        H1(course["title"]),
        # Course overview
        # Lesson list
        # Progress tracker
        # Discussion forum
    )
```

### 3. Add Video Player

```python
@app.get("/course/{course_id}/lesson/{lesson_id}")
async def lesson_view(course_id: int, lesson_id: int):
    return Div(
        # Video player
        Video(
            src=lesson["video_url"],
            controls=True,
            cls="w-full"
        ),
        # Lesson content
        # Quiz/assessment
        # Next lesson button
    )
```

### 4. Add Progress Tracking

```python
async def update_progress(user_id: str, course_id: int, lesson_id: int):
    await db.update_one("progress", {
        "user_id": user_id,
        "course_id": course_id
    }, {
        "completed_lessons": lesson_id,
        "last_accessed": datetime.utcnow()
    })
```

### 5. Add Instructor Dashboard

```python
@app.get("/instructor/dashboard")
async def instructor_dashboard(request: Request):
    user = await get_current_user(request)
    
    if "instructor" not in user.get("roles", []):
        return RedirectResponse("/")
    
    # Show instructor's courses
    # Student enrollments
    # Revenue analytics
    # Course management tools
```

## Integration with Other Add-ons

### With Auth:
- ✅ User accounts for enrollment
- ✅ Role-based access (student/instructor/admin)
- ✅ Progress tracking per user

### With E-Shop:
- Link courses to shop products
- Purchase courses through shop
- Bundle courses with other products

### With Admin:
- Manage courses
- View enrollments
- Analytics dashboard
- Content moderation

## Tech Stack

- **FastHTML** - Python web framework
- **MonsterUI** - UI components
- **Tailwind CSS** - Styling
- **HTMX** - Dynamic updates
- **UIkit Icons** - Icons

## File Structure

```
examples/lms/
├── __init__.py          # Package init
├── app.py               # Main application
└── README.md            # This file
```

## Features to Add

### Basic:
- [ ] Course detail pages
- [ ] Lesson viewer
- [ ] Quiz/assessment system
- [ ] Certificate generation

### Intermediate:
- [ ] Discussion forums
- [ ] Live chat support
- [ ] Assignment submission
- [ ] Peer reviews

### Advanced:
- [ ] Live video classes
- [ ] AI-powered recommendations
- [ ] Gamification (badges, points)
- [ ] Social learning features

## Client Pricing Example

- **Basic LMS**: $800
  - Course catalog
  - Enrollment system
  - Progress tracking
  
- **+ Content Management**: $400
  - Video hosting
  - Quiz builder
  - Certificate generator
  
- **+ Advanced Features**: $600
  - Discussion forums
  - Live classes
  - Analytics dashboard
  - Mobile app

**Total**: $1,800 for complete learning platform

## Deployment

### Development:
```bash
python app/app.py
# Visit http://localhost:5001/lms-example
```

### Production:
```bash
gunicorn app.app:app --workers 4 --bind 0.0.0.0:8000
```

## Testing Checklist

- [ ] Browse courses without login
- [ ] Try to enroll without login → redirected to login
- [ ] Register new account
- [ ] Login and enroll in course
- [ ] View "My Courses"
- [ ] Check enrollment persists after logout/login
- [ ] Test mobile responsiveness

## Support

This is a template/example. Customize for your client's needs:
- Change branding/colors
- Add client's courses
- Integrate video hosting (Vimeo, YouTube, custom)
- Add payment processing
- Customize learning paths

## License

Part of FastApp - Use freely for client projects

---

**Perfect for**: Online courses, corporate training, educational platforms, skill development
