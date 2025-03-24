import os
import random
from locust import HttpUser, task, between, events
import json
import time
from typing import Dict, List
import requests

from commons.bot import SWECCBot, check_connection, BASE_URL_HTTP


class SWECCLoadTest(HttpUser):
    wait_time = between(1, 5)
    bot: SWECCBot = None

    def on_start(self):
        """Initialize the bot and ensure it's authenticated."""

        bot_id = random.randint(1, 100)
        self.bot = SWECCBot.from_idx(bot_id)

        if not self.bot.ensure_authenticated():
            raise ValueError(f"Failed to authenticate bot {bot_id}")

        self.client.headers.update({"Content-Type": "application/json"})

        csrf_token = self.bot.get_csrf_token()
        if csrf_token:
            self.client.headers.update({"X-CSRFToken": csrf_token})

        print(f"Bot {bot_id} initialized and authenticated")

    @task(3)
    def view_directory(self):
        """Simulate viewing the directory."""
        with self.client.get(
            "/directory/", name="View Directory", catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to view directory: {response.status_code}")

    @task(5)
    def search_directory(self):
        """Simulate searching the directory."""

        queries = ["bot", "test", "user", "admin", "elimelt"]
        query = random.choice(queries)

        with self.client.get(
            f"/directory/search/?q={query}",
            name=f"Search Directory ({query})",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to search directory: {response.status_code}")

    @task(2)
    def view_attendance_leaderboard(self):
        """Simulate viewing the attendance leaderboard."""
        order_options = ["attendance", "recent"]
        order_by = random.choice(order_options)

        with self.client.get(
            f"/leaderboard/attendance/?order_by={order_by}",
            name=f"View Attendance Leaderboard ({order_by})",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to view leaderboard: {response.status_code}")

    @task(1)
    def view_profile(self):
        """Simulate viewing a user profile."""

        user_ids = list(range(1, 10))
        user_id = random.choice(user_ids)

        with self.client.get(
            f"/directory/{user_id}/",
            name=f"View User Profile ({user_id})",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to view profile: {response.status_code}")

    @task(1)
    def simulate_message(self):
        """Simulate sending a message (for engagement tracking)."""

        channel_id = random.randint(1, 10)

        data = {
            "channel_id": channel_id,
            "discord_id": self.bot.idx,
        }

        with self.client.post(
            "/engagement/message/", json=data, name="Send Message", catch_response=True
        ) as response:
            if response.status_code == 202:
                response.success()
            else:
                response.failure(f"Failed to send message: {response.status_code}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Check connection to the server before starting the test."""
    if not check_connection():
        environment.runner.quit()
        return
    print("Starting load test...")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("Load test completed.")
