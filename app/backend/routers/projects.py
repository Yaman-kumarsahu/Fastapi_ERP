from fastapi import HTTPException, Depends, APIRouter, Request 
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
import models
from auth.auth import get_current_user, bcrypt_context
from typing import List, Annotated
from schema import Project
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND


router = APIRouter(
    tags= ["project"]
)

db_dependency = Annotated[Session, Depends(get_db)]

current_user_dependency = Annotated[dict, Depends(get_current_user)]

templates = Jinja2Templates(directory="..\\frontend\\templates\\project")

@router.post("/project/")
async def create_project(project: dict, cu : current_user_dependency, db: db_dependency):
    if cu is None or not cu["role"] == "admin":
        raise HTTPException(status_code=401, detail='Unauthenticated or unauthorized user')
    db_manager = db.query(models.Users).filter(models.Users.id == project['manager_id']).first()
    if db_manager and db_manager.role == "manager":
        db_project = models.Projects(name=project['name'], manager_id = project['manager_id'])
    else:
        raise HTTPException(status_code=404, detail='Manager id is invalid')
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.get("/project/")
async def get_project_data(cu : current_user_dependency, db:db_dependency):
    if cu is None or cu["role"] == "employee":
        raise HTTPException(status_code=401, detail='Unauthenticated or unauthorized user')
    output = db.query(models.Projects).order_by(models.Projects.id).all()
    if not output:
        raise HTTPException(status_code=404, detail='Project table not found')
    return output 

# @router.get("/project/projectid={project_id}")
# async def get_single_project_data(project_id:int, cu : current_user_dependency, db:db_dependency):
#     if cu is None or not cu["role"] == "admin":
#         raise HTTPException(status_code=401, detail='Unauthenticated or unauthorized user')
#     output = db.query(models.Projects).filter(models.Projects.id == project_id).first()
#     if not output:
#         raise HTTPException(status_code=404, detail='Project was not found in the table')
#     return output 

# @router.get("/project/managerid={manager_id}")
# async def get_manager_projects(manager_id: int, cu : current_user_dependency, db: db_dependency):
#     if cu is None or not cu["role"] == "admin":
#         raise HTTPException(status_code=401, detail='Unauthenticated or unauthorized user')
#     db_manager = db.query(models.Users).filter(models.Users.id == manager_id).first()
#     if db_manager:
#         if db.query(models.Projects).filter(models.Projects.manager_id == manager_id):
#             db_project = db.query(models.Projects).filter(models.Projects.manager_id == manager_id).all()
#         else:
#             raise HTTPException(status_code=404, detail='Manager has no project')
#     else:
#         raise HTTPException(status_code=404, detail='Manager id is not valid')
#     return db_project 

@router.delete("/project/{project_id}")
async def delete_project(project_id: int, cu : current_user_dependency, db: db_dependency):
    if cu is None or not cu["role"] == "admin":
        raise HTTPException(status_code=401, detail='Unauthenticated or unauthorized user')
    db_project = db.query(models.Projects).filter(models.Projects.id == project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail='Project was not found in the table')
    db.delete(db_project)
    db.commit()
    return {"message": "Project Deleted"}










@router.get("/addproject")
async def addempdata(cu : current_user_dependency, request: Request):
    if cu is None or not cu["role"] == "admin":
        return templates.TemplateResponse("unauthenticated.html", {"request": request}, status_code=HTTP_401_UNAUTHORIZED)
    context = {"request": request}
    return templates.TemplateResponse("addproject.html", context)

@router.get("/viewproject")
async def viewproject(cu : current_user_dependency, request: Request):
    if cu is None or cu["role"] == "employee":
        return templates.TemplateResponse("unauthenticated.html", {"request": request}, status_code=HTTP_401_UNAUTHORIZED)
    context = {"request": request}
    return templates.TemplateResponse("viewproject.html", context)

@router.get("/projectdelete")
async def projectdelete(cu : current_user_dependency, request: Request):
    if cu is None or not cu["role"] == "admin":
        return templates.TemplateResponse("unauthenticated.html", {"request": request}, status_code=HTTP_401_UNAUTHORIZED)
    context = {"request": request}
    return templates.TemplateResponse("projectdelete.html", context)
