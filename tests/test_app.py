from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture(autouse=True)
def restore_activities():
    snapshot = deepcopy(activities)
    yield
    activities.clear()
    activities.update(snapshot)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_get_activities_returns_activity_data(client):
    # Arrange
    expected_participants = ["michael@mergington.edu", "daniel@mergington.edu"]

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    activities_data = response.json()
    assert "Chess Club" in activities_data
    assert activities_data["Chess Club"]["participants"] == expected_participants


def test_signup_adds_participant(client):
    # Arrange
    activity_name = "Art Club"
    email = "alex@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name.replace(' ', '%20')}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities[activity_name]["participants"]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    original_participants = activities[activity_name]["participants"].copy()

    # Act
    response = client.post(
        f"/activities/{activity_name.replace(' ', '%20')}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert activities[activity_name]["participants"] == original_participants


def test_signup_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"
    email = "alex@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name.replace(' ', '%20')}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant_removes_registration(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name.replace(' ', '%20')}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}
    assert email not in activities[activity_name]["participants"]


def test_remove_participant_rejects_unregistered_email(client):
    # Arrange
    activity_name = "Soccer Club"
    email = "alex@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name.replace(' ', '%20')}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_remove_participant_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"
    email = "alex@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name.replace(' ', '%20')}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"