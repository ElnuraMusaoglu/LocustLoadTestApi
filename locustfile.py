# https://jsonplaceholder.typicode.com/

from locust import HttpUser, task, between, SequentialTaskSet
import random
import string


def random_string(length=10):
    """Generate a random string of given length"""
    return ''.join(random.choices(string.ascii_letters, k=length))


class BrowsePosts(SequentialTaskSet):
    """
    Task set: Simulates a user browsing posts and comments
    Runs tasks in sequence for more realistic user journeys.
    """

    @task
    def get_all_posts(self):
        with self.client.get("/posts", catch_response=True) as response:
            if response.status_code != 200:
                response.failure("Failed to fetch posts")
            else:
                # store a post id for later use
                posts = response.json()
                if posts:
                    self.post_id = random.choice(posts)["id"]
                else:
                    self.post_id = 1

    @task
    def get_single_post(self):
        self.client.get(f"/posts/{self.post_id}")

    @task
    def get_comments_for_post(self):
        self.client.get(f"/posts/{self.post_id}/comments")


class CreateData(SequentialTaskSet):
    """
    Task set: Simulates users creating content (posts, comments)
    """

    @task
    def create_post(self):
        payload = {
            "title": random_string(12),
            "body": random_string(50),
            "userId": random.randint(1, 10)
        }
        with self.client.post("/posts", json=payload, catch_response=True) as response:
            if response.status_code == 201:
                self.post_id = response.json().get("id", 101)  # fake API always returns 101
            else:
                response.failure("Failed to create post")

    @task
    def create_comment(self):
        payload = {
            "name": random_string(8),
            "email": f"{random_string(5)}@example.com",
            "body": random_string(30),
            "postId": getattr(self, "post_id", 1)
        }
        self.client.post("/comments", json=payload)


class FakeApiUser(HttpUser):
    """
    Represents a user in the load test.
    - Some users mostly browse
    - Some users create data
    """

    wait_time = between(1, 3)  # think time between requests
    host = "https://jsonplaceholder.typicode.com"

    tasks = {
        BrowsePosts: 3,   # 75% of users are browsers
        CreateData: 1     # 25% of users create posts/comments
    }
