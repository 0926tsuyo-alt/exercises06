"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

import json
import secrets
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# Authentication setup
security = HTTPBasic()

def load_users():
    with current_dir.joinpath("users.json").open("r", encoding="utf-8") as file:
        return json.load(file)

users = load_users()


def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    user_email = credentials.username
    user_password = credentials.password

    if user_email not in users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    user_record = users[user_email]
    if not secrets.compare_digest(user_record["password"], user_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    return {"email": user_email, **user_record}


def require_role(user, allowed_roles):
    if user["role"] not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied for this role",
        )


@app.get("/dashboard")
def dashboard(user: dict = Depends(get_current_user)):
    if user["role"] == "student":
        enrolled = [
            {
                "activity_name": name,
                "schedule": details["schedule"],
                "participants": details["participants"],
            }
            for name, details in activities.items()
            if user["email"] in details["participants"]
        ]

        available = [
            {
                "activity_name": name,
                "description": details["description"],
                "schedule": details["schedule"],
                "spots_left": details["max_participants"] - len(details["participants"]),
            }
            for name, details in activities.items()
            if user["email"] not in details["participants"]
        ]

        return {
            "role": "student",
            "name": user["name"],
            "enrolled_activities": enrolled,
            "available_activities": available,
        }

    if user["role"] == "teacher":
        return {
            "role": "teacher",
            "name": user["name"],
            "activities": [
                {
                    "activity_name": name,
                    "description": details["description"],
                    "schedule": details["schedule"],
                    "max_participants": details["max_participants"],
                    "current_participants": len(details["participants"]),
                    "participants": details["participants"],
                }
                for name, details in activities.items()
            ],
        }

    if user["role"] == "hod":
        activity_summary = [
            {
                "activity_name": name,
                "schedule": details["schedule"],
                "participants": details["participants"],
                "max_participants": details["max_participants"],
            }
            for name, details in activities.items()
        ]
        return {
            "role": "hod",
            "name": user["name"],
            "total_activities": len(activities),
            "total_students_signed_up": sum(
                len(details["participants"]) for details in activities.values()
            ),
            "activity_summary": activity_summary,
        }

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Unknown role",
    )


@app.get("/dashboard/student")
def student_dashboard(user: dict = Depends(get_current_user)):
    require_role(user, ["student"])
    return dashboard(user)


@app.get("/dashboard/teacher")
def teacher_dashboard(user: dict = Depends(get_current_user)):
    require_role(user, ["teacher"])
    return dashboard(user)


@app.get("/dashboard/hod")
def hod_dashboard(user: dict = Depends(get_current_user)):
    require_role(user, ["hod"])
    return dashboard(user)

# In-memory activity database
activities = {
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
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
