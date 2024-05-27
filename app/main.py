from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import chatbot

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chatbot.router, prefix="/chatbot")


@app.get("/")
async def hello():
    return {"Hello": "World"}
