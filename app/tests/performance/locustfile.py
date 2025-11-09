from locust import HttpUser, between, task
from .tasks_auth import AuthTasks
from .tasks_commerce import CommerceTasks
from .tasks_lms import LMSTasks
from .tasks_social import SocialTasks

class FastAppUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.auth = AuthTasks(self.client)
        self.lms = LMSTasks(self.client)
        self.commerce = CommerceTasks(self.client)
        self.social = SocialTasks(self.client)
        self.auth.login()

    @task(2)
    def view_courses(self):
        self.lms.list_courses()

    @task(3)
    def browse_products(self):
        self.commerce.list_products()

    @task(1)
    def create_post(self):
        self.social.create_post()

    @task(1)
    def like_post(self):
        self.social.like_post()