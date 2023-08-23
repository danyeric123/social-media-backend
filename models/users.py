import pydantic

class User(pydantic.BaseModel):
    username: str
    password: str
    scopes: list[str] = []