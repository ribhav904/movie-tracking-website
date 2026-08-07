from pydantic import BaseModel, ConfigDict


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page[T](APIModel):
    items: list[T]
    next_cursor: str | None = None


class Message(APIModel):
    message: str
