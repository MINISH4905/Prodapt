import os
from fastapi import FastAPI
from fastapi.responses import FileResponse

app = FastAPI(title="VentureX-Ray - Attacker Module (Stub)")

frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend"))

@app.get("/")
async def root():
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Welcome to the Attacker Module Stub. Modules 1, 2, and 3 will reside here."}

