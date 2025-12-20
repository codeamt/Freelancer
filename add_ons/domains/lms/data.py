"""
LMS Domain - Sample Data

Shared course data that can be used by examples and demos.
In production, this would be fetched from database.
"""

# Sample courses for demos and examples
SAMPLE_COURSES = [
    {
        "id": 1,
        "title": "Platform Orientation - Free Course",
        "description": "Get started with our learning platform - completely free!",
        "instructor": "Platform Team",
        "price": 0.00,
        "duration": "2 hours",
        "level": "Beginner",
        "students": 1250,
        "rating": 4.8,
        "image": "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "category": "Getting Started",
        "features": ["10 video lessons", "Platform tour", "Quick start guide", "Lifetime access"],
        "long_description": "Welcome to our platform! This free orientation course will help you get started. Learn how to navigate the platform, access courses, track your progress, and make the most of your learning journey."
    },
    {
        "id": 2,
        "title": "Python Programming Fundamentals",
        "description": "Master Python from basics to advanced concepts",
        "instructor": "Dr. Sarah Chen",
        "price": 49.99,
        "duration": "12 hours",
        "level": "Beginner",
        "students": 3420,
        "rating": 4.9,
        "image": "https://images.unsplash.com/photo-1526379095098-d400fd0bf935?q=80&w=1332&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "category": "Programming",
        "features": ["42 video lessons", "Coding exercises", "Certificate", "Lifetime access"],
        "long_description": "Learn Python programming from scratch. Cover variables, data types, control flow, functions, OOP, file handling, and more. Perfect for beginners!"
    },
    {
        "id": 3,
        "title": "Web Development Bootcamp",
        "description": "Build modern web applications with HTML, CSS, JavaScript",
        "instructor": "Mike Johnson",
        "price": 79.99,
        "duration": "20 hours",
        "level": "Intermediate",
        "students": 2890,
        "rating": 4.7,
        "image": "https://images.unsplash.com/photo-1498050108023-c5249f4df085?q=80&w=1172&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "category": "Web Development",
        "features": ["65 video lessons", "10 projects", "Certificate", "Lifetime access"],
        "long_description": "Complete web development bootcamp covering HTML5, CSS3, JavaScript, React, Node.js, and deployment. Build real-world projects!"
    },
    {
        "id": 4,
        "title": "Data Science with Python",
        "description": "Learn data analysis, visualization, and machine learning",
        "instructor": "Dr. Emily Rodriguez",
        "price": 99.99,
        "duration": "25 hours",
        "level": "Advanced",
        "students": 1560,
        "rating": 4.9,
        "image": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "category": "Data Science",
        "features": ["80 video lessons", "Real datasets", "Certificate", "Lifetime access"],
        "long_description": "Master data science with Python. Learn pandas, NumPy, matplotlib, scikit-learn, and build ML models. Includes real-world projects!"
    },
    {
        "id": 5,
        "title": "Mobile App Development",
        "description": "Build iOS and Android apps with React Native",
        "instructor": "Alex Kim",
        "price": 89.99,
        "duration": "18 hours",
        "level": "Intermediate",
        "students": 2100,
        "rating": 4.8,
        "image": "https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "category": "Mobile Development",
        "features": ["55 video lessons", "5 apps", "Certificate", "Lifetime access"],
        "long_description": "Build cross-platform mobile apps for iOS and Android using React Native and modern development tools."
    },
    {
        "id": 6,
        "title": "UI/UX Design Masterclass",
        "description": "Design beautiful and user-friendly interfaces",
        "instructor": "Jessica Martinez",
        "price": 69.99,
        "duration": "15 hours",
        "level": "Beginner",
        "students": 1890,
        "rating": 4.7,
        "image": "https://images.unsplash.com/photo-1561070791-2526d30994b5?q=80&w=1064&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "category": "Design",
        "features": ["45 video lessons", "Design projects", "Certificate", "Lifetime access"],
        "long_description": "Master UI/UX design principles, Figma, user research, wireframing, prototyping, and design systems."
    }
]


def get_course_by_id(course_id: int):
    """Get course by ID"""
    return next((c for c in SAMPLE_COURSES if c["id"] == course_id), None)


def get_courses_by_category(category: str):
    """Get courses by category"""
    return [c for c in SAMPLE_COURSES if c["category"] == category]


def get_free_courses():
    """Get all free courses"""
    return [c for c in SAMPLE_COURSES if c["price"] == 0.00]


def get_all_categories():
    """Get all unique categories"""
    return list(set(c["category"] for c in SAMPLE_COURSES))
