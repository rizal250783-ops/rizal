import os
import pytest
import requests
from dotenv import dotenv_values

frontend_env = dotenv_values("/app/frontend/.env")
base_url = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not base_url:
    raise RuntimeError("REACT_APP_BACKEND_URL missing")
BASE_URL = base_url.rstrip("/")
API = f"{BASE_URL}/api"

CREDS = {
    "admin": ("admin@hajimiskin.co.id", "Admin12345"),
    "direktur": ("hendri.kamal@hajimiskin.co.id", "Direktur123"),
    "ao_lending": ("rizky.lending@hajimiskin.co.id", "Password123"),
    "ao_funding": ("budi.funding@hajimiskin.co.id", "Password123"),
    "pic_remedial": ("hendra.remedial@hajimiskin.co.id", "Password123"),
}


def login(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=60)
    return r


def client_for(role):
    email, pw = CREDS[role]
    r = login(email, pw)
    if r.status_code != 200:
        pytest.fail(f"Login failed for {role}: {r.status_code} {r.text[:300]}")
    token = r.json().get("access_token")
    if not token:
        pytest.fail(f"No access_token in login response for {role}")
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}"})
    return s


@pytest.fixture(scope="session")
def admin():
    return client_for("admin")


@pytest.fixture(scope="session")
def direktur():
    return client_for("direktur")


@pytest.fixture(scope="session")
def ao_lending():
    return client_for("ao_lending")


@pytest.fixture(scope="session")
def ao_funding():
    return client_for("ao_funding")


@pytest.fixture(scope="session")
def remedial():
    return client_for("pic_remedial")
