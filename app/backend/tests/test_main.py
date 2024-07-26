from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
from pathlib import Path
parent_dir = Path(__file__).parents[1]
sys.path.append(str(parent_dir))

from main import app, get_db
from auth.auth import get_current_user
from database import Base
from typing import Annotated

# Set up a test database
TEST_DATABASE_URL = "postgresql://postgres:yaman@localhost:5432/test"
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency function for testing
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

#create all the tables
Base.metadata.create_all(bind=engine)

# Create a test client
client = TestClient(app)

admin_id = 1
employee_id = 0
manager_id = 5
project_id = 0
request_id = 0
request_id2 = 0
skill_id = 0

def get_emp():
    return {"username": "username", "id": employee_id, "role": "employee"}

def get_manager():
    return {"username": "username", "id": manager_id, "role": "manager"}

def get_admin():
    return {"username": "username", "id": admin_id, "role": "admin"}

def logout():
    response = client.post("/auth/logout")
    
    # Check if the logout was successful (status code 200)
    assert response.status_code == 200
    
    # Check the response message
    logout_message = response.json()
    assert logout_message["message"] == "logout successful"

def test_login_admin():
    formData = {
        "username": "1",  
        "password": "r123"
    }
    response = client.post("/auth/token", data=formData)  
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "token_type" in response.json()
    assert "role" in response.json()

def test_get_users():    
    response = client.get("/user/")
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_get_single_user_data():
    # Assuming user_id 1 exists in the database for testing purposes
    user_id = 1
    response = client.get(f"/user/{user_id}")
    
    assert response.status_code == 200
    
    emp_data = response.json()
    assert isinstance(emp_data, dict)  # Since the response is a single dictionary
        
    assert "id" in emp_data
    assert "name" in emp_data
    assert "email" in emp_data
    assert "role" in emp_data
    assert "manager_id" in emp_data
    assert "manager_name" in emp_data
    
    projects = emp_data.get("projects")  # get projects value from emp_data, if it exists
    assert projects is None or isinstance(projects, list)
    
    skills = emp_data.get("skills")  # get skills value from emp_data, if it exists
    assert skills is None or isinstance(skills, list)

def test_create_emp():
    # Assuming a logged-in user with admin privileges
    user_data = {
        "id": 12,
        "name": "jane Doe",
        "email": "jane1.doe@example.com",
        "password": "password123",
        "role": "manager"
    }
    
    response = client.post("/user/", json=user_data)
    
    assert response.status_code == 200
    
    emp_data = response.json()
    assert isinstance(emp_data, dict)  # Since the response is expected to be a single dictionary
    global employee_id
    employee_id = emp_data['id']
    
    assert "id" in emp_data
    assert "name" in emp_data
    assert "email" in emp_data
    assert "role" in emp_data
    assert "manager_id" in emp_data

def test_update_emp():
    
    update_data = {
        "user_id": employee_id,
        "name": "Jane Smith",
        "email": "jane.smith@example.com",
        "password": "newpassword123",
        "role": "employee"
    }
    
    update_response = client.put("/user/update", json=update_data)
    
    assert update_response.status_code == 200
    
    updated_emp_data = update_response.json()
    assert isinstance(updated_emp_data, dict)
    
    #Verify the updated user details
    assert updated_emp_data["id"] == employee_id
    assert updated_emp_data["name"] == "Jane Smith"
    assert updated_emp_data["email"] == "jane.smith@example.com"
    assert updated_emp_data["role"] == "employee"

def test_create_project():
    project_data = {
        "id": 5,
        "name": "New Project",
        "manager_id": manager_id
    }
    
    project_response = client.post("/project/", json=project_data)
    
    assert project_response.status_code == 200
    
    project_data_response = project_response.json()
    assert isinstance(project_data_response, dict)
    global project_id
    project_id = project_data_response["id"]
    
    # Verify the created project details
    assert "id" in project_data_response
    assert project_data_response["name"] == "New Project"
    assert project_data_response["manager_id"] == manager_id

def test_get_projects():
    get_project_response = client.get("/project/")
    assert get_project_response.status_code == 200
    
    project_list = get_project_response.json()
    assert isinstance(project_list, list)
    
    # Verify the project is in the list
    for proj in project_list:
        assert "id" in proj
        assert "name" in proj
        assert "manager_id" in proj

def test_assign_manager():
    assign_manager_data = {
        'user_id' : employee_id,
        'mid' : manager_id
    }
    assign_response = client.put("/user/manager/assign", json=assign_manager_data)
    assert assign_response.status_code == 200
    
    assigned_user_data = assign_response.json()
    assert isinstance(assigned_user_data, dict)
    
    # Verify the manager assignment
    assert assigned_user_data['id'] == employee_id
    assert assigned_user_data['manager_id'] == manager_id

def test_assign_project():
    assign_project_data = {
        'user_id': employee_id,
        'project_id': project_id
    }
    
    assign_project_response = client.put("/user/project/assign", json=assign_project_data)
    assert assign_project_response.status_code == 200
    
    assigned_project_data = assign_project_response.json()
    assert isinstance(assigned_project_data, dict)
    
    # Verify the project assignment
    assert assigned_project_data['id'] == employee_id
    assert assigned_project_data['project_id'] == project_id

def test_unassign_project():
    # Assuming the employee has already been assigned a project
    unassign_project_data = {
        'user_id': employee_id
    }

    unassign_project_response = client.put("/user/project/unassign", json=unassign_project_data)
    assert unassign_project_response.status_code == 200

    unassigned_project_data = unassign_project_response.json()
    assert isinstance(unassigned_project_data, dict)

    # Verify the project unassignment
    assert unassigned_project_data['id'] == employee_id
    assert unassigned_project_data['project_id'] is None

def test_unassign_manager():
    unassign_manager_data = {
        'user_id': employee_id
    }
    
    unassign_manager_response = client.put("/user/manager/unassign", json=unassign_manager_data)
    assert unassign_manager_response.status_code == 200
    
    unassigned_manager_data = unassign_manager_response.json()
    assert isinstance(unassigned_manager_data, dict)
    
    # Verify the project unassignment
    assert unassigned_manager_data['id'] == employee_id
    assert unassigned_manager_data['manager_id'] is None
    logout()

############################################################################################################################################

def test_login_employee():
    formData = {
        "username": employee_id,  
        "password": "newpassword123"
    }
    response = client.post("/auth/token", data=formData)  
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "token_type" in response.json()
    assert "role" in response.json()        

def test_create_skill():
     # Assuming the user is an employee

    skill_data = {"name": "Python", "emp_id": employee_id}
    response = client.post("/skill/", json=skill_data)
    
    # Check if the skill was created successfully (status code 200)
    assert response.status_code == 200
    
    # Verify the skill data returned in the response
    created_skill = response.json()
    assert created_skill["name"] == "Python"
    assert created_skill["emp_id"] == employee_id
    delete_id = created_skill["id"]
    delete_response = client.delete(f"/skill/{delete_id}")
    
    # Check if the skill was deleted successfully (status code 200)
    assert delete_response.status_code == 200
    
    # Verify the delete message
    assert delete_response.json()["message"] == "Skill Deleted"
    logout()

##############################################################################################################################################

def test_login_manager():
    formData = {
        "username": manager_id,  
        "password": "password123"
    }
    response = client.post("/auth/token", data=formData)  
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "token_type" in response.json()
    assert "role" in response.json()    

def test_get_unassigned_emp_data():
    
    skill_name = {"skill_name": "Python"}  # Assuming the skill name you want to test
     # Assuming the user is an employee

    response = client.post(f"/user/skill/unassigned", json=skill_name)
    
    assert response.status_code == 200
    
    emp_data = response.json()
    assert isinstance(emp_data, list)  # Since the response is expected to be a list of dictionaries
    
    # Check if each employee dictionary has the required keys
    for emp in emp_data:
        assert "id" in emp
        assert "name" in emp
        assert "email" in emp
        assert "role" in emp
        assert "manager_id" in emp

def test_create_request():
    # Call the create_request endpoint with authenticated user data
      # Assuming the user is a manager
    request_data = {"id": 5, "name": "New Request", "description": "Description of the request", "manager_id": manager_id}
    response = client.post("/request/", json=request_data)
    
    # Check if the request was created successfully (status code 200)
    assert response.status_code == 200
    
    # Verify the request data returned in the response
    created_request = response.json()
    global request_id
    request_id = created_request["id"]
    assert created_request["name"] == "New Request"
    assert created_request["description"] == "Description of the request"
    assert created_request["manager_id"] == manager_id

    request_data2 = {"name": "New Request", "description": "Description of the request", "manager_id": manager_id}
    response = client.post("/request/", json=request_data2)
    
    # Check if the request was created successfully (status code 200)
    assert response.status_code == 200
    
    # Verify the request data returned in the response
    created_request = response.json()
    global request_id2
    request_id2 = created_request["id"]
    assert created_request["name"] == "New Request"
    assert created_request["description"] == "Description of the request"
    assert created_request["manager_id"] == manager_id


def test_get_request_data():
    
    response = client.get("/request/")
    
    # Check if the request data was retrieved successfully (status code 200)
    assert response.status_code == 200
    
    # Verify the response content
    request_data = response.json()
    assert isinstance(request_data, list)
    for request in request_data:
        assert "id" in request
        assert "name" in request
        assert "description" in request
        assert "manager_id" in request
        assert "status" in request

def test_create_skill_manager():
     # Assuming the user is an employee

    skill_data = {"id": 4, "name": "Python", "emp_id": manager_id}
    response = client.post("/skill/", json=skill_data)
    
    # Check if the skill was created successfully (status code 200)
    assert response.status_code == 200
    
    # Verify the skill data returned in the response
    created_skill = response.json()
    global skill_id
    skill_id = created_skill["id"]
    assert created_skill["name"] == "Python"
    assert created_skill["emp_id"] == manager_id

def test_get_skill_data():
    
    response = client.get("/skill/")
    
    # Check if the skill data was retrieved successfully (status code 200)
    assert response.status_code == 200
    
    # Verify the response content
    skill_data = response.json()
    assert isinstance(skill_data, list)
    for skill in skill_data:
        assert "id" in skill
        assert "name" in skill
        assert "emp_id" in skill

def test_get_single_skill_data():
    
    # Define a sample skill name
    skill_name = "Python"
    
    # Call the get_single_skill_data endpoint with authenticated user data
    response = client.get(f"/skill/skill={skill_name}")
    
    # Check if the skill data was retrieved successfully (status code 200)
    assert response.status_code == 200
    
    # Verify the response content
    skill_data = response.json()
    assert isinstance(skill_data, list)
    assert len(skill_data) > 0  # Ensure at least one skill record is returned
    for skill in skill_data:
        assert "id" in skill
        assert "name" in skill
        assert "emp_id" in skill

def test_get_single_skill_data():
    
    # Call the get_single_skill_data endpoint with authenticated user data
    response = client.get(f"/skill/unique")
    
    # Check if the skill data was retrieved successfully (status code 200)
    assert response.status_code == 200
    
    # Verify the response content
    skill_data = response.json()
    assert isinstance(skill_data, list)
    assert len(skill_data) > 0  # Ensure at least one skill record is returned
    for skill in skill_data:
        assert "id" in skill
        assert "name" in skill
        assert "emp_id" in skill

def test_delete_skill():
    delete_response = client.delete(f"/skill/{skill_id}")
    
    # Check if the skill was deleted successfully (status code 200)
    assert delete_response.status_code == 200
    
    # Verify the delete message
    assert delete_response.json()["message"] == "Skill Deleted"
    logout()    

##############################################################################################################################################

def test_login_admin2():
    formData = {
        "username": admin_id,  
        "password": "r123"
    }
    response = client.post("/auth/token", data=formData)  
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "token_type" in response.json()
    assert "role" in response.json()    


def test_approve_request():    
    # Create a request to approve
    # Assuming request_id is available
    create_response = client.put(f"/request/accept/{request_id}")
    
    # Check if the request was approved successfully (status code 200)
    assert create_response.status_code == 200
    
    # Verify the status of the request
    approved_request = create_response.json()
    assert approved_request["status"] == "Accepted"

# Similarly, you can write a test function for rejecting a request
def test_reject_request():
    # Create a request to reject
    # Assuming request_id is available
    create_response = client.put(f"/request/reject/{request_id2}")
    
    # Check if the request was rejected successfully (status code 200)
    assert create_response.status_code == 200
    
    # Verify the status of the request
    rejected_request = create_response.json()
    assert rejected_request["status"] == "Rejected"

# Assuming the client object and necessary dependencies are correctly set up

def test_delete_request():
    # Create a request to delete
    # Assuming request_id is available
    create_response = client.delete(f"/request/{request_id}")
    
    # Check if the request was deleted successfully (status code 200)
    assert create_response.status_code == 200
    
    # Verify the delete message
    assert create_response.json()["message"] == "Request Deleted"

    create_response = client.delete(f"/request/{request_id2}")
    
    # Check if the request was deleted successfully (status code 200)
    assert create_response.status_code == 200
    
    # Verify the delete message
    assert create_response.json()["message"] == "Request Deleted"


def test_delete_project():
    # Create a project to delete
    # Assuming project_id is available
    delete_response = client.delete(f"/project/{project_id}")
    
    # Check if the project was deleted successfully (status code 200)
    assert delete_response.status_code == 200
    
    # Verify the delete message
    assert delete_response.json()["message"] == "Project Deleted"

def test_delete_user():  
    delete_response = client.delete(f"/user/{employee_id}")
    
    # Check if the user was deleted successfully (status code 200)
    assert delete_response.status_code == 200
    
    # Verify the delete message
    assert delete_response.json()["message"] == "User Deleted"

def test_logout():
    response = client.post("/auth/logout")
    
    # Check if the logout was successful (status code 200)
    assert response.status_code == 200
    
    # Check the response message
    logout_message = response.json()
    assert logout_message["message"] == "logout successful"


   





