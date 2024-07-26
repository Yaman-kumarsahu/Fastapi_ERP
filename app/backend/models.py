from sqlalchemy import Boolean, Integer, String, Column, ForeignKey
from database import Base

class Users(Base):
    __tablename__ = "Users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False)
    manager_id = Column(Integer, ForeignKey("Users.id"))
    project_id = Column(Integer, ForeignKey("Projects.id"))

class Projects(Base):
    __tablename__ = "Projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    manager_id = Column(Integer, ForeignKey("Users.id"), nullable=False)


class Skills(Base):
    __tablename__ = "Skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    emp_id = Column(Integer, ForeignKey("Users.id"), nullable=False)

class Requests(Base):
    __tablename__ = "Requests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(String, nullable=False, index=True)
    manager_id = Column(Integer, ForeignKey("Users.id"), nullable=False)
    status = Column(String, nullable=False, default='Requested')