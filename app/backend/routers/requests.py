from fastapi import HTTPException, Depends, APIRouter, Request as req
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
import models
from auth.auth import get_current_user, bcrypt_context
from typing import List, Annotated
from schema import Request, ReqStat
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND


router = APIRouter(
    tags= ["request"]
)

db_dependency = Annotated[Session, Depends(get_db)]

current_user_dependency = Annotated[dict, Depends(get_current_user)]


templates = Jinja2Templates(directory="..\\frontend\\templates\\request")

@router.post("/request/")
async def create_request(request: dict, cu : current_user_dependency, db: db_dependency):
    if cu is None or not cu["role"] == "manager":
        raise HTTPException(status_code=401, detail='Unauthenticated or unauthorized user')
    db_manager = db.query(models.Users).filter(models.Users.id == request["manager_id"]).first()
    if db_manager:
        db_request = models.Requests(name=request["name"], description=request["description"], manager_id = request["manager_id"])
    else:
        raise HTTPException(status_code=404, detail='Manager id is invalid')
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request

@router.get("/request/")
async def get_request_data(cu : current_user_dependency, db:db_dependency):
    if cu is None or cu["role"] == "employee":
        raise HTTPException(status_code=401, detail='Unauthenticated or unauthorized user')
    output = db.query(models.Requests).order_by(models.Requests.id).all()
    if not output:
        raise HTTPException(status_code=404, detail='Request table not found')
    return output 

# @router.get("/request/requestid={request_id}")
# async def get_single_request_data(request_id:int, cu : current_user_dependency, db:db_dependency):
#     if cu is None or not cu["role"] == "admin":
#         raise HTTPException(status_code=401, detail='Unauthenticated or unauthorized user')
#     output = db.query(models.Requests).filter(models.Requests.id == request_id).first()
#     if not output:
#         raise HTTPException(status_code=404, detail='Request was not found in the table')
#     return output

# @router.get("/request/managerid={manager_id}")
# async def get_manager_requests(manager_id: int, cu : current_user_dependency, db: db_dependency):
#     if cu is None or not cu["role"] == "admin":
#         raise HTTPException(status_code=401, detail='Unauthenticated or unauthorized user')
#     db_manager = db.query(models.Users).filter(models.Users.id == manager_id).first()
#     if db_manager:
#         if db.query(models.Requests).filter(models.Requests.manager_id == manager_id):
#             db_request = db.query(models.Requests).filter(models.Requests.manager_id == manager_id).all()
#         else:
#             raise HTTPException(status_code=404, detail='Manager has no request')
#     else:
#         raise HTTPException(status_code=404, detail='Manager id is not valid')
#     return db_request 

@router.put("/request/accept/{request_id}")
async def approve(request_id:int, cu : current_user_dependency, db:db_dependency):
    if cu is None or not cu["role"] == "admin":
        raise HTTPException(status_code=401, detail='Unauthenticated or unauthorized user')
    output = db.query(models.Requests).filter(models.Requests.id == request_id).first()
    if not output:
        raise HTTPException(status_code=404, detail='Request was not found in the table')
    else:
        output.status = "Accepted"
    db.add(output)
    db.commit()
    db.refresh(output)
    return output

@router.put("/request/reject/{request_id}")
async def reject(request_id:int, cu : current_user_dependency, db:db_dependency):
    if cu is None or not cu["role"] == "admin":
        raise HTTPException(status_code=401, detail='Unauthenticated or unauthorized user')
    output = db.query(models.Requests).filter(models.Requests.id == request_id).first()
    if not output:
        raise HTTPException(status_code=404, detail='Request was not found in the table')
    else:
        output.status = "Rejected"
    db.add(output)
    db.commit()
    db.refresh(output)
    return output

@router.delete("/request/{request_id}")
async def delete_request(request_id: int, cu : current_user_dependency, db: db_dependency):
    if cu is None or not cu["role"] == "admin":
        raise HTTPException(status_code=401, detail='Unauthenticated or unauthorized user')
    db_request = db.query(models.Requests).filter(models.Requests.id == request_id).first()
    if db_request is None:
        raise HTTPException(status_code=404, detail='Request was not found in the table')
    db.delete(db_request)
    db.commit()
    return {"message": "Request Deleted"}







@router.get("/viewrequest", response_class=HTMLResponse)
async def viewrequest(cu : current_user_dependency, request: req):
    if cu is None or cu["role"] == "employee":
        return templates.TemplateResponse("unauthenticated.html", {"request": request}, status_code=HTTP_401_UNAUTHORIZED)
    context = {"request": request}
    if cu["role"] == "manager":
        return templates.TemplateResponse("viewrequestmanager.html", context)
    return templates.TemplateResponse("viewrequest.html", context)

@router.get("/deleterequest", response_class=HTMLResponse)
async def deleterequest(cu : current_user_dependency, request: req):
    if cu is None or not cu["role"] == "admin":
        return templates.TemplateResponse("unauthenticated.html", {"request": request}, status_code=HTTP_401_UNAUTHORIZED)
    context = {"request": request}
    return templates.TemplateResponse("deleterequest.html", context)

@router.get("/createrequest", response_class=HTMLResponse)
async def createrequest(cu : current_user_dependency, request: req):
    if cu is None or not cu["role"] == "manager":
        return templates.TemplateResponse("unauthenticated.html", {"request": request}, status_code=HTTP_401_UNAUTHORIZED)
    context = {"request": request}
    return templates.TemplateResponse("createrequest.html", context)
