import os
import random
import json
import time
import websocket
from typing import Dict, List
from locust import HttpUser, task, between, events
import requests
from threading import Thread

from commons.bot import BASE_URL_WS, SWECCBot, check_connection, BASE_URL_HTTP


class SWECCLoadTest(HttpUser):
    wait_time = between(1, 5)

    bot: SWECCBot = None
    ws = None
    jwt_token = None

    def on_start(self):
        """Initialize the bot, authenticate, get JWT token, and open WebSocket."""
        bot_id = random.randint(1, 100)
        self.bot = SWECCBot.from_idx(bot_id)

        if not self.bot.ensure_authenticated():
            raise ValueError(f"Failed to authenticate bot {bot_id}")

        self.get_jwt_token()
        self.connect_websocket()

        print(f"Bot {bot_id} initialized, authenticated, and connected to WebSocket")

    def get_jwt_token(self):
        """Get JWT token for WebSocket authentication using the bot's session."""
        try:
            response = self.bot.session.get(f"{BASE_URL_HTTP}/auth/jwt/")

            if response.status_code == 200:
                data = response.json()
                self.jwt_token = data.get("token")
                if not self.jwt_token:
                    raise ValueError("JWT token not found in response")
                print(f"Successfully retrieved JWT token for bot {self.bot.idx}")
            else:
                raise ValueError(
                    f"Failed to get JWT token: {response.status_code} - {response.text}"
                )
        except Exception as e:
            print(f"Error getting JWT token: {e}")
            raise

    def connect_websocket(self):
        """Connect to WebSocket endpoint."""
        if not self.jwt_token:
            raise ValueError("Cannot connect to WebSocket without JWT token")

        services = ["echo"]
        service = random.choice(services)

        ws_url = f"{BASE_URL_WS}/ws/{service}/{self.jwt_token}"
        print(f"Connecting to WebSocket: {ws_url}")
        self.ws = websocket.WebSocketApp(
            ws_url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open,
        )

        thread = Thread(target=self.ws.run_forever)
        thread.daemon = True
        thread.start()
        time.sleep(1)

    def on_message(self, ws, message):
        # do something
        ...

    def on_error(self, ws, error):
        """Handle WebSocket errors."""
        print(f"WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket connection close."""
        print(f"WebSocket closed: {close_status_code} - {close_msg}")
        self.connect_websocket()

    def on_open(self, ws):
        """Handle WebSocket connection open."""
        print("WebSocket connection established")

    def on_stop(self):
        """Clean up WebSocket on test stop."""
        if self.ws:
            self.ws.close()

    @task(3)
    def send_echo_message(self):
        """Send an echo message through WebSocket."""
        if not self.ws:
            return

        try:
            message = {
                "type": "echo",
                "content": f"Hello from bot {self.bot.idx} at {time.time()}",
            }
            self.ws.send(json.dumps(message))
        except Exception as e:
            print(f"Error sending echo message: {e}")
            self.connect_websocket()


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
