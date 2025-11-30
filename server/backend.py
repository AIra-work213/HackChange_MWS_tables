from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from model import MyModel

app = FastAPI()
model = MyModel()

class ClientQuery(BaseModel):
    query: str
    session_id: Optional[str] = "default"

class ClearSessionRequest(BaseModel):
    session_id: str

@app.get("/")
async def read_root(query: ClientQuery):
    response = model.answer_query(query.query, query.session_id)
    if isinstance(response, dict) and response.get("error"):
        return {"response": response["error"]}
    return {"response": response}

@app.post("/clear")
async def clear_session(request: ClearSessionRequest):
    """Очищает историю диалога для указанной сессии."""
    model.clear_session(request.session_id)
    return {"status": "ok", "message": f"Сессия {request.session_id} очищена"}