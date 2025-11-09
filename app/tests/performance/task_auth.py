from locust import task

class AuthTasks:
    def __init__(self, client):
        self.client = client
        self.token = None

    def login(self):
        data = {"email": "loadtest@example.com", "password": "loadpass"}
        response = self.client.post("/auth/login", json=data)
        if response.status_code == 200:
            self.token = response.json().get("access_token")

    @task
    def register_user(self):
        data = {"username": "loaduser", "email": "loadtest@example.com", "password": "loadpass"}
        self.client.post("/auth/register", json=data)