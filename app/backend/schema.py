from pydantic import BaseModel,EmailStr
from enum import Enum


class UserType(str, Enum):
    admin = 'admin'
    employee = 'employee'
    manager = 'manager'

class ReqStat(str, Enum):
    requested = 'Requested'
    accepted = 'Accepted'
    rejected = 'Rejected'

class User(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserType

class Project(BaseModel):
    name: str
    manager_id: int

class Skill(BaseModel):
    name: str
    emp_id: int

class Request(BaseModel):
    name: str
    description: str
    manager_id: int
    status: ReqStat 