from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from input import (
    initialize_database,
    create_project,
    get_project
)


app = FastAPI(
    title="VentureX-Ray Input Module",
    version="1.0"
)


# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProjectRequest(BaseModel):
    idea: str


@app.on_event("startup")
def startup():

    initialize_database()


@app.get("/")
def home():

    return {
        "message": "VentureX-Ray API is running"
    }


@app.post("/api/projects")
def create_new_project(request: ProjectRequest):

    if not request.idea.strip():
        raise HTTPException(
            status_code=400,
            detail="Startup idea cannot be empty"
        )

    if len(request.idea.strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail="Please provide a more detailed startup idea"
        )

    project = create_project(request.idea)

    return project


@app.get("/api/projects/{project_id}")
def fetch_project(project_id: str):

    project = get_project(project_id)

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    return project