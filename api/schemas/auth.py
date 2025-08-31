from pydantic import BaseModel

# LOGIN
class LoginRequest(BaseModel):
    email: str
    password: str
