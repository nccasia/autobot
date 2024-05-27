from pydantic import BaseModel


class Message(BaseModel):
    text: str

    class Config:
        schema_extra = {"example": {"text": "This is a sample message"}}
