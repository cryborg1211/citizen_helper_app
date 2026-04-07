from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os

# Ensure the 'ai' package can be imported from the directory containing main.py
sys.path.append(os.path.dirname(__file__))

# Import necessary functions from core_engine.py
from ai.ai_engine.core_engine import initialize_cloud_brain, generate_response

app = FastAPI(title="Citizen Helper API")

# REQUIRED: Add CORSMiddleware to allow Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

retriever = None
llm = None


class ChatRequest(BaseModel):
    message: str

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    global retriever, llm

    if retriever is None or llm is None:
        print("[[INFO] loading cloud brain")
        retriever, llm = initialize_cloud_brain()
        print("[[INFO] loading completed! Super speed activated.")
        
    # Process the user query and return the AI response
    response_text = generate_response(request.message, retriever, llm)
    return {"response": response_text}