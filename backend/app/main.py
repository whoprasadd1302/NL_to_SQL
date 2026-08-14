from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .llm import generate_response


app = FastAPI(
    title="MitraAI",
    description="LLM-Based Multilingual Conversational Chatbot",
    version="0.1.0",
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


@app.get("/")
def root():
    return {
        "message": "Welcome to MitraAI",
        "status": "Backend is running",
        "model": "qwen3:8b",
        "provider": "Ollama",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    if not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty."
        )

    try:
        response = generate_response(request.message)

        return ChatResponse(
            response=response
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"LLM error: {str(e)}"
        )