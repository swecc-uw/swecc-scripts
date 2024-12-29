import os
import random
from locust import HttpUser, task, between, events
import json
import time

class BotUser(HttpUser):
    wait_time = between(1, 5)

    channel_ids = list(range(1, 11))
    user_ids = list(range(1, 11))

    def on_start(self):
        self.api_key = os.getenv('SWECC_API_KEY')
        if not self.api_key:
            raise ValueError("SWECC_API_KEY environment variable not set")

        self.headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json",
        }

    @task
    def send_message(self):
        channel_id = random.choice(self.channel_ids)
        user_id = random.choice(self.user_ids)

        data = {
            "channel_id": channel_id,
            "discord_id": user_id,
        }

        start_time = time.time()

        with self.client.post(
            "/engagement/message/",
            json=data,
            headers=self.headers,
            catch_response=True
        ) as response:
            duration = time.time() - start_time

            if response.status_code == 202:
                response.success()
                events.request.fire(
                    request_type="POST",
                    name="message_success",
                    response_time=duration * 1000,
                    response_length=len(response.text),
                    context={
                        "channel_id": channel_id,
                        "user_id": user_id
                    }
                )
            elif response.status_code == 404:
                response.failure(f"User not found: {user_id}")
            else:
                response.failure(f"Unexpected status code: {response.status_code}")

            if response.status_code != 202:
                print(f"Error sending message - Status: {response.status_code}, "
                      f"Channel: {channel_id}, User: {user_id}, "
                      f"Response: {response.text}")

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("Starting load test...")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("Load test completed.")