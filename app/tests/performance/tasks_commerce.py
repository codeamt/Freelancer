from locust import task

class CommerceTasks:
    def __init__(self, client):
        self.client = client

    @task
    def list_products(self):
        self.client.get("/commerce/products")

    @task
    def simulate_checkout(self):
        self.client.post("/commerce/checkout", json={"product_id": 1, "quantity": 1})


