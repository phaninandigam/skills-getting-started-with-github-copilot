"""
Test cases for the FastAPI application endpoints
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

client = TestClient(app)


@pytest.fixture
def clear_activities():
    """Fixture to reset activities to initial state before each test"""
    # Store original state
    original_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    }
    
    # Reset activities before test
    from app import activities
    activities.clear()
    activities.update(original_activities)
    
    yield
    
    # Reset activities after test
    activities.clear()
    activities.update(original_activities)


def test_root_redirect():
    """Test that root path redirects to /static/index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(clear_activities):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    
    data = response.json()
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert "Gym Class" in data
    
    # Verify structure
    activity = data["Chess Club"]
    assert "description" in activity
    assert "schedule" in activity
    assert "max_participants" in activity
    assert "participants" in activity


def test_signup_for_activity_success(clear_activities):
    """Test successfully signing up for an activity"""
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "newstudent@mergington.edu"}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "newstudent@mergington.edu" in data["message"]
    
    # Verify participant was added
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]


def test_signup_for_nonexistent_activity(clear_activities):
    """Test signing up for a non-existent activity"""
    response = client.post(
        "/activities/Nonexistent Activity/signup",
        params={"email": "student@mergington.edu"}
    )
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_signup_duplicate_student(clear_activities):
    """Test that a student cannot sign up twice for the same activity"""
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"}
    )
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"]


def test_unregister_from_activity_success(clear_activities):
    """Test successfully unregistering from an activity"""
    response = client.post(
        "/activities/Chess Club/unregister",
        params={"email": "michael@mergington.edu"}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "michael@mergington.edu" in data["message"]
    
    # Verify participant was removed
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]


def test_unregister_from_nonexistent_activity(clear_activities):
    """Test unregistering from a non-existent activity"""
    response = client.post(
        "/activities/Nonexistent Activity/unregister",
        params={"email": "student@mergington.edu"}
    )
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_unregister_non_registered_student(clear_activities):
    """Test that unregistering a non-registered student returns error"""
    response = client.post(
        "/activities/Chess Club/unregister",
        params={"email": "unregistered@mergington.edu"}
    )
    assert response.status_code == 400
    assert "not registered" in response.json()["detail"]


def test_signup_and_unregister_flow(clear_activities):
    """Test the complete signup and unregister flow"""
    test_email = "testuser@mergington.edu"
    activity = "Programming Class"
    
    # Sign up
    signup_response = client.post(
        f"/activities/{activity}/signup",
        params={"email": test_email}
    )
    assert signup_response.status_code == 200
    
    # Verify participant is in list
    activities_response = client.get("/activities")
    assert test_email in activities_response.json()[activity]["participants"]
    
    # Unregister
    unregister_response = client.post(
        f"/activities/{activity}/unregister",
        params={"email": test_email}
    )
    assert unregister_response.status_code == 200
    
    # Verify participant is removed from list
    activities_response = client.get("/activities")
    assert test_email not in activities_response.json()[activity]["participants"]
