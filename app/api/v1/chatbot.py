from fastapi import APIRouter
from pydantic import BaseModel
from app.services.chatbot_service import process_chat, create_chain, setup_chroma_db
from app.schemas.message import Message

vectordb = setup_chroma_db()
chain = create_chain(vectordb)

router = APIRouter()


@router.post("/")
async def chatbot_handler(message: Message):
    user_input = message.text
    response = process_chat(chain, user_input)
    return {"Response": response}
