from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users import BaseUserManager
from fastapi import Request

from database import get_db
from models import User, UserCreate, UserDB

user_db = SQLAlchemyUserDatabase(UserDB, get_db, User)

# User Manager
class UserManager(BaseUserManager[UserCreate, UserDB]):
    user_db_model = UserDB
    reset_password_token_secret = "RESET_PASSWORD_SECRET"
    verification_token_secret = "VERIFY_SECRET"

    async def on_after_register(self, user: UserDB, request: Request):
        # Here you can perform actions after user registration
        print(f"User {user.id} has registered.")