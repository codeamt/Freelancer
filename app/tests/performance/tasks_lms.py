from locust import task

class LMSTasks:
    def __init__(self, client):
        self.client = client

    @task
    def list_courses(self):
        self.client.get("/lms/courses")

    @task
    def enroll_course(self):
        self.client.post("/lms/enroll", json={"user_id": 1, "course_id": 1})

