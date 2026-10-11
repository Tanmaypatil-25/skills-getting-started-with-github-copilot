from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(app_module, "activities", deepcopy(app_module.activities))
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_get_activities_returns_activity_data(client):
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert expected_activity in response.json()
    assert "participants" in response.json()[expected_activity]


def test_root_redirects_to_activity_page(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_signup_adds_participant(client):
    # Arrange
    activity = "Basketball Team"
    email = "student@example.com"
    signup_url = f"/activities/{quote(activity, safe='')}/signup"

    # Act
    response = client.post(signup_url, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity}"}
    assert email in app_module.activities[activity]["participants"]


def test_signup_returns_not_found_for_unknown_activity(client):
    # Arrange
    activity = "Unknown Club"
    signup_url = f"/activities/{activity}/signup"

    # Act
    response = client.post(signup_url, params={"email": "student@example.com"})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity = "Basketball Team"
    email = "student@example.com"
    app_module.activities[activity]["participants"].append(email)
    signup_url = f"/activities/{quote(activity, safe='')}/signup"

    # Act
    response = client.post(signup_url, params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert app_module.activities[activity]["participants"].count(email) == 1


def test_unregister_removes_participant(client):
    # Arrange
    activity = "Basketball Team"
    email = "student@example.com"
    app_module.activities[activity]["participants"].append(email)
    signup_url = f"/activities/{quote(activity, safe='')}/signup"

    # Act
    response = client.delete(signup_url, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity}"}
    assert email not in app_module.activities[activity]["participants"]


def test_unregister_returns_not_found_for_unknown_activity(client):
    # Arrange
    activity = "Unknown Club"
    signup_url = f"/activities/{activity}/signup"

    # Act
    response = client.delete(signup_url, params={"email": "student@example.com"})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_returns_not_found_for_unsigned_participant(client):
    # Arrange
    activity = "Basketball Team"
    email = "student@example.com"
    signup_url = f"/activities/{quote(activity, safe='')}/signup"

    # Act
    response = client.delete(signup_url, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"