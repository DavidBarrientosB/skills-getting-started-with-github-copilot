"""
Tests for the High School Management System API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the activities database before each test"""
    # Store original state
    original_activities = {}
    for key, value in activities.items():
        original_activities[key] = {
            "description": value["description"],
            "schedule": value["schedule"],
            "max_participants": value["max_participants"],
            "participants": value["participants"].copy()
        }

    yield

    # Reset to original state
    activities.clear()
    activities.update(original_activities)


class TestActivitiesAPI:
    """Test cases for the activities API"""

    def test_get_activities(self, client):
        """Test getting all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()

        # Check that we have activities
        assert len(data) > 0

        # Check structure of first activity
        first_activity = next(iter(data.values()))
        assert "description" in first_activity
        assert "schedule" in first_activity
        assert "max_participants" in first_activity
        assert "participants" in first_activity
        assert isinstance(first_activity["participants"], list)

    def test_get_root_redirects_to_static(self, client):
        """Test that root path redirects to static index"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307  # Temporary redirect
        assert "/static/index.html" in response.headers["location"]

    def test_signup_successful(self, client):
        """Test successful signup for an activity"""
        activity_name = "Chess Club"
        email = "test@mergington.edu"

        # Get initial participant count
        initial_count = len(activities[activity_name]["participants"])

        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]

        # Check that participant was added
        assert len(activities[activity_name]["participants"]) == initial_count + 1
        assert email in activities[activity_name]["participants"]

    def test_signup_activity_not_found(self, client):
        """Test signup for non-existent activity"""
        response = client.post("/activities/NonExistent/signup?email=test@mergington.edu")
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_already_signed_up(self, client):
        """Test signup when student is already signed up"""
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already in participants

        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_unregister_successful(self, client):
        """Test successful unregister from an activity"""
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already in participants

        # Get initial participant count
        initial_count = len(activities[activity_name]["participants"])

        response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]

        # Check that participant was removed
        assert len(activities[activity_name]["participants"]) == initial_count - 1
        assert email not in activities[activity_name]["participants"]

    def test_unregister_activity_not_found(self, client):
        """Test unregister from non-existent activity"""
        response = client.delete("/activities/NonExistent/unregister?email=test@mergington.edu")
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_not_signed_up(self, client):
        """Test unregister when student is not signed up"""
        activity_name = "Chess Club"
        email = "notsignedup@mergington.edu"

        response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_signup_multiple_activities(self, client):
        """Test that a student can sign up for multiple activities"""
        email = "multiactivity@mergington.edu"

        # Sign up for two different activities
        response1 = client.post("/activities/Chess%20Club/signup?email=" + email)
        assert response1.status_code == 200

        response2 = client.post("/activities/Programming%20Class/signup?email=" + email)
        assert response2.status_code == 200

        # Check both activities have the student
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Programming Class"]["participants"]

    def test_unregister_then_signup_again(self, client):
        """Test unregistering and then signing up again"""
        activity_name = "Chess Club"
        email = "reusable@mergington.edu"

        # First sign up
        client.post(f"/activities/{activity_name}/signup?email={email}")
        assert email in activities[activity_name]["participants"]

        # Then unregister
        client.delete(f"/activities/{activity_name}/unregister?email={email}")
        assert email not in activities[activity_name]["participants"]

        # Sign up again
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response.status_code == 200
        assert email in activities[activity_name]["participants"]