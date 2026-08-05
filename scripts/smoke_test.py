#!/usr/bin/env python3
"""End-to-end smoke test for the user-management API.

Waits for the health endpoint, then exercises the full CRUD cycle and the
main error paths against a running instance. Exits non-zero on the first
failed assertion, so CI can gate on it.

Usage:
    python smoke_test.py [--base-url http://localhost:8080] [--timeout 90]
"""

import argparse
import sys
import time
import uuid

import requests

DEFAULT_BASE_URL = "http://localhost:8080"
DEFAULT_TIMEOUT_SECONDS = 90


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def check(condition: bool, message: str) -> None:
    if not condition:
        fail(message)
    print(f"ok: {message}")


def wait_for_health(base_url: str, timeout_seconds: int) -> None:
    """Poll /actuator/health until it reports UP or the timeout expires."""
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            response = requests.get(f"{base_url}/actuator/health", timeout=3)
            if response.status_code == 200 and response.json().get("status") == "UP":
                print(f"ok: health is UP at {base_url}")
                return
        except requests.RequestException:
            pass
        time.sleep(2)
    fail(f"health endpoint not UP within {timeout_seconds}s at {base_url}")


def run_crud_cycle(base_url: str) -> None:
    users_url = f"{base_url}/api/users"
    # Unique email so reruns against the same database never collide
    email = f"smoke-{uuid.uuid4().hex[:12]}@example.com"
    user = {
        "firstName": "Smoke",
        "lastName": "Test",
        "email": email,
        "password": "smoke-test-password",
    }

    # Create
    response = requests.post(users_url, json=user, timeout=5)
    check(response.status_code == 201, f"create returns 201 (got {response.status_code})")
    body = response.json()
    check("passwordHash" not in body and "password" not in body,
          "create response contains no password fields")
    check(response.headers.get("Location", "").endswith(f"/api/users/{body['id']}"),
          "create sets Location header")
    user_id = body["id"]
    user_url = f"{users_url}/{user_id}"

    # Read
    response = requests.get(user_url, timeout=5)
    check(response.status_code == 200, f"read returns 200 (got {response.status_code})")
    check(response.json()["email"] == email, "read returns the created email")

    # Duplicate email is rejected
    response = requests.post(users_url, json=user, timeout=5)
    check(response.status_code == 409, f"duplicate email returns 409 (got {response.status_code})")

    # Validation rejects a short password
    response = requests.post(users_url, json={**user, "password": "short"}, timeout=5)
    check(response.status_code == 400, f"short password returns 400 (got {response.status_code})")

    # Update
    response = requests.put(user_url, json={**user, "firstName": "Updated"}, timeout=5)
    check(response.status_code == 200, f"update returns 200 (got {response.status_code})")
    check(response.json()["firstName"] == "Updated", "update changes the first name")

    # Delete
    response = requests.delete(user_url, timeout=5)
    check(response.status_code == 204, f"delete returns 204 (got {response.status_code})")

    # Deleted user is gone
    response = requests.get(user_url, timeout=5)
    check(response.status_code == 404, f"read after delete returns 404 (got {response.status_code})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS,
                        help="seconds to wait for the health endpoint")
    args = parser.parse_args()

    wait_for_health(args.base_url, args.timeout)
    run_crud_cycle(args.base_url)
    print("SMOKE TEST PASSED")


if __name__ == "__main__":
    main()
