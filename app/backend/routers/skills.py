from fastapi import HTTPException, Depends, APIRouter, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
import models
from auth.auth import get_current_user, bcrypt_context
from typing import List, Annotated
from schema import Skill
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND


router = APIRouter(
    tags= ["skill"]
)

db_dependency = Annotated[Session, Depends(get_db)]

current_user_dependency = Annotated[dict, Depends(get_current_user)]

templates = Jinja2Templates(directory="..\\frontend\\templates\\skill")

@router.post("/skill/")
async def create_skill(skill: Skill, cu:current_user_dependency, db: db_dependency):
    if cu is None or cu["role"] == "admin":
        raise HTTPException(status_code=401, detail='Unauthenticated or unauthorized user')
    if cu["id"] != skill.emp_id:
        raise HTTPException(status_code=401, detail='Unauthenticated or unauthorized user')
    db_user = db.query(models.Users).filter(models.Users.id == skill.emp_id).first()
    if db_user:
        db_skill = models.Skills(name=skill.name, emp_id = skill.emp_id)
    else:
        raise HTTPException(status_code=404, detail='User id is invalid')
    db.add(db_skill)
    db.commit()
    db.refresh(db_skill)
    return db_skill

@router.get("/skill/")
async def get_skill_data(cu:current_user_dependency, db:db_dependency):
    if cu is None:
        raise HTTPException(status_code=401, detail='Unauthenticated or unauthorized user')
    output = db.query(models.Skills).all()
    if not output:
        raise HTTPException(status_code=404, detail='Skill table not found')
    result = []
    for out in output:
        emp = db.query(models.Users).filter(models.Users.id == out.emp_id).first()
        data = {
            "id" : out.id,
            "name" : out.name,
            "emp_id" : out.emp_id,
            "emp_name" : emp.name
        }
        result.append(data)
    return result

@router.get("/skill/skill={skill_name}")
async def get_single_skill_data(skill_name: str, cu:current_user_dependency, db:db_dependency):
    if cu is None:
        raise HTTPException(status_code=401, detail='Unauthenticated or unauthorized user')
    output = db.query(models.Skills).filter(models.Skills.name == skill_name).all()
    if not output:
        raise HTTPException(status_code=404, detail='Skill was not found in the table')
    result = []
    for out in output:
        emp = db.query(models.Users).filter(models.Users.id == out.emp_id).first()
        skilldata = {
            "id": out.id,
            "name": out.name,
            "emp_id": out.emp_id,
            "emp_name": emp.name
        }
        result.append(skilldata)
    return result

# @router.get("/skill/emp={emp_id}")
# async def get_employee_skill_data(emp_id: int, cu:current_user_dependency, db:db_dependency):
#     if cu is None :
#         raise HTTPException(status_code=401, detail='Unauthenticated or unauthorized user')
#     output = db.query(models.Skills).filter(models.Skills.emp_id == emp_id).all()
#     if not output:
#         raise HTTPException(status_code=404, detail='Employee was not found in the table')
#     return output 


@router.delete("/skill/{skill_id}")
async def delete_skill(skill_id: int, cu:current_user_dependency, db: db_dependency):
    if cu is None or cu["role"] == "admin":
        raise HTTPException(status_code=401, detail='Unauthenticated or unauthorized user')
    db_skill = db.query(models.Skills).filter(models.Skills.id == skill_id).first()
    if cu["id"] != db_skill.emp_id:
        raise HTTPException(status_code=401, detail='Unauthenticated or unauthorized user')
    if db_skill is None:
        raise HTTPException(status_code=404, detail='Skill was not found in the table')
    db.delete(db_skill)
    db.commit()
    return {"message": "Skill Deleted"}


@router.get("/skill/unique")
async def get_unique_skill(cu:current_user_dependency, db: db_dependency):
    if cu is None :
        raise HTTPException(status_code=401, detail='Unauthenticated or unauthorized user')
    skills = db.query(models.Skills).distinct(models.Skills.name).all()
    if not skills:
        raise HTTPException(status_code=404, detail='Skill table was not found')
    return skills










@router.get("/viewemp_skill")
async def viewemp_skill(cu:current_user_dependency, request: Request):
    if cu is None:
        return templates.TemplateResponse("unauthenticated.html", {"request": request}, status_code=HTTP_401_UNAUTHORIZED)
    context = {"request": request}
    return templates.TemplateResponse("viewemp_skill.html", context)

@router.get("/viewskill")
async def viewskill(cu:current_user_dependency, request: Request):
    if cu is None:
        return templates.TemplateResponse("unauthenticated.html", {"request": request}, status_code=HTTP_401_UNAUTHORIZED)
    context = {"request": request}
    return templates.TemplateResponse("viewskill.html", context)

@router.get("/viewskillunique")
async def viewskill(cu:current_user_dependency, request: Request):
    if cu is None:
        return templates.TemplateResponse("unauthenticated.html", {"request": request}, status_code=HTTP_401_UNAUTHORIZED)
    context = {"request": request}
    return templates.TemplateResponse("view_unique.html", context)

@router.get("/addskill")
async def addskill(cu:current_user_dependency, request: Request):
    if cu is None:
        return templates.TemplateResponse("unauthenticated.html", {"request": request}, status_code=HTTP_401_UNAUTHORIZED)
    context = {"request": request}
    return templates.TemplateResponse("addskill.html", context)

@router.get("/deleteskill")
async def deleteskill(cu:current_user_dependency, request: Request):
    if cu is None:
        return templates.TemplateResponse("unauthenticated.html", {"request": request}, status_code=HTTP_401_UNAUTHORIZED)
    context = {"request": request}
    return templates.TemplateResponse("deleteskill.html", context)