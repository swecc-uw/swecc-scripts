import os
import requests
import dataclasses
import json
from typing import Optional, Dict, Any

HOST = "localhost"
HTTP = "http"
WS = "ws"
BASE_URL_HTTP = "http://localhost"
BASE_URL_WS = "ws://localhost"


@dataclasses.dataclass
class SWECCBot:
    idx: int
    first_name: str
    last_name: str
    username: str
    email: str
    password: str
    discord_username: str
    session: Optional[requests.Session] = None
    is_authenticated: bool = False

    @staticmethod
    def from_idx(i: int):
        """Create a bot with default values based on index."""
        first_name = f"Bot{i}First"
        last_name = "BotLast"
        username = f"bot{i}username"
        email = f"bot{i}@bot.com"
        password = "bot"
        discord_username = f"bot{i}discord"
        return SWECCBot(
            idx=i,
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            password=password,
            discord_username=discord_username,
            session=requests.Session(),
        )

    @staticmethod
    def from_dict(d: Dict[str, Any]):
        """Create a bot from a dictionary."""
        bot = SWECCBot(
            idx=d["idx"],
            first_name=d["first_name"],
            last_name=d["last_name"],
            username=d["username"],
            email=d["email"],
            password=d["password"],
            discord_username=d["discord_username"],
            session=requests.Session(),
            is_authenticated=d.get("is_authenticated", False),
        )
        return bot

    def to_dict(self) -> Dict[str, Any]:
        """Convert bot to dictionary, excluding session object."""
        data = dataclasses.asdict(self)
        data.pop("session", None)
        return data

    def get_csrf_token(self) -> Optional[str]:
        """Retrieve CSRF token from the server."""
        try:
            response = self.session.get(f"{BASE_URL_HTTP}/auth/csrf/")
            if response.status_code == 200:
                return self.session.cookies.get("csrftoken")
            print(f"Failed to retrieve CSRF token: {response.status_code}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error while retrieving CSRF token: {e}")
            return None

    def register(self) -> bool:
        """Register the bot on the server."""
        csrf_token = self.get_csrf_token()
        if not csrf_token:
            print(f"Could not retrieve CSRF token for bot {self.idx}")
            return False

        headers = {"X-CSRFToken": csrf_token}

        response = self.session.post(
            f"{BASE_URL_HTTP}/auth/register/", json=self.to_dict(), headers=headers
        )

        if response.status_code == 201:
            print(f"Bot {self.idx} registered successfully")
            return True
        else:
            print(
                f"Bot {self.idx} registration failed: {response.status_code} - {response.text}"
            )

            return False

    def login(self) -> bool:
        """Log in the bot to the server using session-based authentication."""
        csrf_token = self.get_csrf_token()
        if not csrf_token:
            print(f"Could not retrieve CSRF token for bot {self.idx}")
            return False

        headers = {"X-CSRFToken": csrf_token, "Content-Type": "application/json"}

        login_data = {"username": self.username, "password": self.password}

        response = self.session.post(
            f"{BASE_URL_HTTP}/auth/login/", data=json.dumps(login_data), headers=headers
        )

        if response.status_code == 200:
            try:
                print(f"Bot {self.idx} logged in successfully")
                return True
            except Exception as e:
                print(f"Bot {self.idx} login succeeded but encountered an error: {e}")
                return False
        else:
            print(
                f"Bot {self.idx} login failed: {response.status_code} - {response.text}"
            )
            return False

    def verify(self) -> bool:
        """Verify the bot using API key authentication."""
        api_key = os.getenv("SWECC_API_KEY")
        if not api_key:
            print(f"SWECC_API_KEY environment variable not set for bot {self.idx}")
            return False

        headers = {
            "Authorization": f"Api-Key {api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "discord_id": self.idx,
            "discord_username": self.discord_username,
            "username": self.username,
        }

        response = requests.put(
            f"{BASE_URL_HTTP}/members/verify-discord/", headers=headers, json=data
        )

        if response.status_code == 200:
            print(f"Bot {self.idx} verified successfully")
            return True
        else:
            print(
                f"Bot {self.idx} verification failed: {response.status_code} - {response.text}"
            )
            return False

    def ensure_authenticated(self) -> bool:
        """Ensure the bot is registered, verified and logged in."""

        if self.is_authenticated:
            return True

        if self.login():
            self.is_authenticated = True

            self.verify()
            return True

        self.register()
        if self.login():
            self.is_authenticated = True

            self.verify()
            return True

        return False

    def request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make an authenticated request to the server."""
        if not self.ensure_authenticated():
            raise ValueError(f"Bot {self.idx} is not authenticated")

        url = f"{BASE_URL_HTTP}{endpoint}"
        return self.session.request(method, url, **kwargs)


def check_connection() -> bool:
    """Check connection to the server."""
    try:
        response = requests.get(f"{BASE_URL_HTTP}/health")
        if response.status_code == 200:
            print("Connected to the server")
            return True
        else:
            print(
                f"Server is up but returned unexpected status: {response.status_code}"
            )
            return False
    except requests.exceptions.ConnectionError:
        print("Could not connect to the server")
        return False
