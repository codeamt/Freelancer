from locust import task

class SocialTasks:
    def __init__(self, client):
        self.client = client

    @task
    def create_post(self):
        self.client.post("/social/posts", json={"author_id": 1, "content": "Load test post"})

    @task
    def like_post(self):
        self.client.post("/social/like", json={"user_id": 1, "post_id": 1})

