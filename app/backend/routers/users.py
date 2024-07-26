from fastapi import HTTPException, Depends, APIRouter, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
import models
from auth.auth import get_current_user, bcrypt_context
from typing import List, Annotated
from schema import User
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND


router = APIRouter(
    tags= ["user"]
)


db_dependency = Annotated[Session, Depends(get_db)]

current_user_dependency = Annotated[dict, Depends(get_current_user)]
# current_user_dependency = Annotated[str, Depends(get_user)]

templates = Jinja2Templates(directory="..\\frontend\\templates\\employee")

@router.get("/user/")
async def get_user_data(cu : current_user_dependency, db: db_dependency, request: Request):
    if cu is None:
        raise HTTPException(status_code=401, detail='Unauthenticated or unauthorized user')
    if cu["role"] == "admin":
        output = db.query(models.Users).order_by(models.Users.id).all()
    elif cu["role"] == "manager":
        output = db.query(models.Users).filter(models.Users.role != "admin").order_by(models.Users.id).all()
    elif cu["role"] == "employee":
        output = db.query(models.Users).filter(models.Users.role == "employee").order_by(models.Users.id).all()
    if not output:
        raise HTTPException(status_code=404, detail='User table not found')
    else:
        result = []
    for out in output:
        manager = db.query(models.Users).filter(models.Users.id == out.manager_id).first()
        if out.role == "manager":
            project = db.query(models.Projects).filter(models.Projects.manager_id == out.id).all()
            if not project == None:
                project_name = []
                project_id = []
                for p in project:
                    project_name.append(p.name)
                    project_id.append(p.id)
        elif out.role == "employee":
            project = db.query(models.Projects).filter(models.Projects.id == out.project_id).first()
            if not project == None:
                project_name = project.name
                project_id = project.id
        else:
            project_name = None
            project_id = None
        skills = db.query(models.Skills).filter(models.Skills.emp_id == out.id).all()
        emp_skills = []
        manager_name =""
        if not manager == None:
            manager_name = manager.name 
        if skills == None:
            emp_skills = []
        else:
            for skill in skills:
                emp_skills.append(skill.name)
        empdata = {
            "id": out.id,
            "name": out.name,
            "email": out.email,
            "role": out.role,
            "manager_id": out.manager_id,
            "project_id": project_id,
            "manager_name": manager_name,
            "project_name": project_name,
            "skills": emp_skills

        }
        result.append(empdata)

    return result
    # return templates.TemplateResponse("user.html", {"request": request, "emps": output})

@router.get("/user/{user_id}")
async def get_single_user_data(user_id: int, cu : current_user_dependency, db: db_dependency):
    if cu is None:
        raise HTTPException(status_code=401, detail='Unauthenticated user')
    
    if cu["role"] == "admin":
        output = db.query(models.Users).filter(models.Users.id == user_id).first()
    elif cu["role"] == "manager":
        output = db.query(models.Users).filter(models.Users.id == user_id, models.Users.role != "admin").first()
    elif cu["role"] == "employee":
        output = db.query(models.Users).filter(models.Users.id == user_id, models.Users.role == "employee").first()
    
    if not output:
        raise HTTPException(status_code=404, detail='User was not found in the table')
    
    manager = db.query(models.Users).filter(models.Users.id == output.manager_id).first()
    skills = db.query(models.Skills).filter(models.Skills.emp_id == output.id).all()
    if output.role == "manager":
        projects = db.query(models.Projects).filter(models.Projects.manager_id == output.id).all()
        
    elif output.role == "employee":
        projects = [db.query(models.Projects).filter(models.Projects.id == output.project_id).first()]
    else:
            projects = []
    emp_projects = [{"id": project.id, "name": project.name} for project in projects] if projects else []
    emp_skills = [{"id": skill.id, "name": skill.name} for skill in skills] if skills else []
    
    empdata = {
        "id": output.id,
        "name": output.name,
        "email": output.email,
        "role": output.role,
        "manager_id": output.manager_id,
        "manager_name": manager.name if manager else None,
        "projects": emp_projects,
        "skills": emp_skills
    }
    
    return empdata

@router.post("/user/skill/unassigned")
async def get_unassigned_emp_data(skill_name: dict, cu : current_user_dependency, db: db_dependency):
    if cu is None or cu["role"] == "employee":
        raise HTTPException(status_code=401, detail='Unauthenticated or unauthorized user')
    db_emp = db.query(models.Users).filter(models.Users.project_id == None).all()
    db_skill = db.query(models.Skills).filter(models.Skills.name == skill_name['skill_name']).all()
    if not db_emp:
        raise HTTPException(status_code=404, detail='All employees are assigned to a project')
    elif not db_skill:
        raise HTTPException(status_code=404, detail='No employee with this skill')
    output = []
    for emp in db_emp:
        if db.query(models.Skills).filter(models.Skills.emp_id == emp.id, models.Skills.name == skill_name["skill_name"]).first():
            output.append(emp)
    if not output:
        raise HTTPException(status_code=404, detail='No unassigned employee with this skill')
    return output

@router.post("/user/")
async def create_emp(user: User, cu: current_user_dependency, db: db_dependency):
    if cu is None or not cu["role"] == "admin":
        raise HTTPException(status_code=401, detail='Unauthenticated or unauthorized user')
    db_user = models.Users(name=user.name,
                            email=user.email, 
                            password=bcrypt_context.hash(user.password), 
                            role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.put("/user/manager/assign")
async def assign_manager(user: dict, cu : current_user_dependency, db: db_dependency):
    if cu is None or not cu["role"] == "admin":
        raise HTTPException(status_code=401, detail='Unauthenticated or unauthorized user')
    db_user = db.query(models.Users).filter(models.Users.id == user['user_id']).first()
    db_manager = db.query(models.Users).filter(models.Users.id == user['mid']).first()
    if db_manager.role == 'manager' and db_user.role.lower() == "employee" and db_user.manager_id == None:
        db_user.manager_id = user['mid']
    else:
        raise HTTPException(status_code=404, detail='Id does not belong to a valid manager')
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
    

@router.put("/user/project/assign")
async def assign_project(user_id: dict, cu : current_user_dependency, db: db_dependency):
    if cu is None or not cu["role"] == "admin":
        raise HTTPException(status_code=401, detail='Unauthenticated or unauthorized user')
    db_user = db.query(models.Users).filter(models.Users.id == user_id["user_id"]).first()
    db_project = db.query(models.Projects).filter(models.Projects.id == user_id['project_id']).first()
    manager_is_same = db_user.manager_id == db_project.manager_id
    if db_user.project_id == None and db_project and db_user.role.lower() == "employee" and manager_is_same:
        db_user.project_id = user_id['project_id']
    else:
        raise HTTPException(status_code=404, detail='Project is not in project table')
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.put("/user/project/unassign")
async def unassign_project(user_id: dict, cu : current_user_dependency, db: db_dependency):
    if cu is None or not cu["role"] == "admin":
        raise HTTPException(status_code=401, detail='Unauthenticated or unauthorized user')
    db_user = db.query(models.Users).filter(models.Users.id == user_id['user_id']).first()
    if db_user.role.lower() == "employee" and not db_user.project_id == None:
        db_user.project_id = None
    else:
        raise HTTPException(status_code=404, detail='Project cannot be unassigned')
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.put("/user/manager/unassign")
async def unassign_manager(user_id: dict, cu : current_user_dependency, db: db_dependency):
    if cu is None or not cu["role"] == "admin":
        raise HTTPException(status_code=401, detail='Unauthenticated or unauthorized user')
    db_user = db.query(models.Users).filter(models.Users.id == user_id['user_id']).first()
    if db_user.role.lower() == "employee" and not db_user.manager_id == None:
        db_user.manager_id = None
    else:
        raise HTTPException(status_code=404, detail='Manager cannot be unassigned')
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.put("/user/update")
async def update_emp(user: dict, cu : current_user_dependency, db: db_dependency):
    if cu is None or not cu["role"] == "admin":
        raise HTTPException(status_code=401, detail='Unauthenticated or unauthorized user')
    db_user = db.query(models.Users).filter(models.Users.id == user["user_id"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    else:
        if not user["name"] == "":
            db_user.name = user["name"]
        if not user["email"] == "":
            db_user.email = user["email"]
        if not user["password"] == "":
            db_user.password = bcrypt_context.hash(user["password"])
        if not user["role"] == "":
            db_user.role = user["role"]
         
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/user/{user_id}")
async def delete_user(user_id: int, cu : current_user_dependency, db: db_dependency):
    if cu is None or not cu["role"] == "admin":
        raise HTTPException(status_code=401, detail='Unauthenticated or unauthorized user')
    db_user = db.query(models.Users).filter(models.Users.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
    return {"message": "User Deleted"}











@router.get("/addempdata")
async def addempdata(cu: current_user_dependency, request: Request):
    context = {"request": request}
    if cu is None or not cu["role"] == "admin":
        return templates.TemplateResponse("unauthenticated.html", {"request": request}, status_code=HTTP_401_UNAUTHORIZED)
    return templates.TemplateResponse("addempdata.html", context)

@router.get("/userdelete")
async def userdelete(cu: current_user_dependency, request: Request):
    context = {"request": request}
    if cu is None or not cu["role"] == "admin":
        return templates.TemplateResponse("unauthenticated.html", {"request": request}, status_code=HTTP_401_UNAUTHORIZED)
    return templates.TemplateResponse("userdelete.html", context)

@router.get("/updateempdata")
async def updateempdata(cu: current_user_dependency, request: Request):
    context = {"request": request}
    if cu is None or not cu["role"] == "admin":
        return templates.TemplateResponse("unauthenticated.html", {"request": request}, status_code=HTTP_401_UNAUTHORIZED)
    return templates.TemplateResponse("updateempdata.html", context)

@router.get("/viewemp")
async def viewemp(cu: current_user_dependency, request: Request):
    context = {"request": request}
    if cu is None:
        return templates.TemplateResponse("unauthenticated.html", {"request": request}, status_code=HTTP_401_UNAUTHORIZED)
    return templates.TemplateResponse("viewemp.html", context)

@router.get("/viewsingleemp")
async def viewsingleemp(cu: current_user_dependency, request: Request):
    context = {"request": request}
    if cu is None:
        return templates.TemplateResponse("unauthenticated.html", {"request": request}, status_code=HTTP_401_UNAUTHORIZED)
    return templates.TemplateResponse("viewsingleemp.html", context)

@router.get("/viewunassigned")
async def viewunassigned(cu: current_user_dependency, request: Request):
    context = {"request": request}
    if cu is None or cu["role"] == "employee":
        return templates.TemplateResponse("unauthenticated.html", {"request": request}, status_code=HTTP_401_UNAUTHORIZED)
    return templates.TemplateResponse("viewunassigned.html", context)

@router.get("/unassigneddetail")
async def unassigneddetail(cu: current_user_dependency, request: Request):
    context = {"request": request}
    if cu is None or not cu["role"] == "admin":
        return templates.TemplateResponse("unauthenticated.html", {"request": request}, status_code=HTTP_401_UNAUTHORIZED)
    return templates.TemplateResponse("unassigneddetail.html", context)

@router.get("/assignmanager")
async def assignmanager(cu: current_user_dependency, request: Request):
    context = {"request": request}
    if cu is None or not cu["role"] == "admin":
        return templates.TemplateResponse("unauthenticated.html", {"request": request}, status_code=HTTP_401_UNAUTHORIZED)
    return templates.TemplateResponse("assignmanager.html", context)

@router.get("/assignproject")
async def assignproject(cu: current_user_dependency, request: Request):
    context = {"request": request}
    if cu is None or not cu["role"] == "admin":
        return templates.TemplateResponse("unauthenticated.html", {"request": request}, status_code=HTTP_401_UNAUTHORIZED)
    return templates.TemplateResponse("assignproject.html", context)

@router.get("/unassignproject")
async def unassignproject(cu: current_user_dependency, request: Request):
    context = {"request": request}
    if cu is None or not cu["role"] == "admin":
        return templates.TemplateResponse("unauthenticated.html", {"request": request}, status_code=HTTP_401_UNAUTHORIZED)
    return templates.TemplateResponse("unassignproject.html", context)

@router.get("/unassignmanager")
async def unassignmanager(cu: current_user_dependency, request: Request):
    context = {"request": request}
    if cu is None or not cu["role"] == "admin":
        return templates.TemplateResponse("unauthenticated.html", {"request": request}, status_code=HTTP_401_UNAUTHORIZED)
    return templates.TemplateResponse("unassignmanager.html", context)

