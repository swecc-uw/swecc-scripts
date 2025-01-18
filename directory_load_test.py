import os
import random
from locust import HttpUser, task, between, events
import json
import time


class BotUser(HttpUser):
    wait_time = between(1, 5)

    queries = ["advay", "asdfa", "test", "asdfwe"]
    current_query_index = 0
    current_query_progress = 0

    def on_start(self):
        self.api_key = os.getenv("SWECC_API_KEY")
        if not self.api_key:
            raise ValueError("SWECC_API_KEY environment variable not set")

        self.headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json",
        }

    def keystroke(self):
        return random.randrange(
            self.current_query_progress, len(self.queries[self.current_query_index])
        )

    @task
    def send_message(self):

        start_time = time.time()

        new_index = self.keystroke()
        query = self.queries[self.current_query_index][:new_index]
        self.current_query_progress = new_index

        if self.current_query_progress >= len(self.queries[self.current_query_index]):
            self.current_query_index = (self.current_query_index + 1) % self.queries

        with self.client.get(
            f"/directory/search/?q={query}", headers=self.headers, catch_response=True
        ) as response:
            duration = time.time() - start_time

            if response.status_code == 200:
                response.success()
                events.request.fire(
                    request_type="POST",
                    name="message_success",
                    response_time=duration * 1000,
                    response_length=len(response.text),
                    context={"query": query},
                )
            else:
                response.failure(f"Unexpected status code: {response.status_code}")
                print(
                    f"Error sending message - Status: {response.status_code}, "
                    f"Query: {query}, "
                    f"Response: {response.text}"
                )


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("Starting load test...")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("Load test completed.")
