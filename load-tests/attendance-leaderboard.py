import os
import random
from locust import HttpUser, task, between, events
import json
import time


class BotUser(HttpUser):
    wait_time = between(1, 5)

    current_order = "last_updated"

    def on_start(self):
        self.api_key = os.getenv("SWECC_API_KEY")
        if not self.api_key:
            raise ValueError("SWECC_API_KEY environment variable not set")

        self.headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json",
        }

    def get_ordering_option(self, past_value):
        return "recent" if past_value == "attendance" else "attendance"

    @task
    def send_message(self):

        start_time = time.time()

        self.current_order = self.get_ordering_option(self.current_order)

        with self.client.get(
            f"/leaderboard/attendance/?order_by={self.current_order}",
            headers=self.headers,
            catch_response=True,
        ) as response:
            duration = time.time() - start_time

            if response.status_code == 200:
                response.success()
                events.request.fire(
                    request_type="POST",
                    name="message_success",
                    response_time=duration * 1000,
                    response_length=len(response.text),
                    context={"current_order": self.current_order},
                )
            else:
                response.failure(f"Unexpected status code: {response.status_code}")
                print(
                    f"Error sending message - Status: {response.status_code}, "
                    f"Current Order: {self.current_order}, "
                    f"Response: {response.text}"
                )


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("Starting load test...")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("Load test completed.")
