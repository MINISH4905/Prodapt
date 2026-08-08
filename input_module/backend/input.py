import sqlite3
import os
from datetime import datetime

from ai_parser import parse_idea


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_DIR = os.path.join(BASE_DIR, "database")
DATABASE_PATH = os.path.join(DATABASE_DIR, "inputs.db")


os.makedirs(DATABASE_DIR, exist_ok=True)


def get_connection():
    return sqlite3.connect(DATABASE_PATH)


def initialize_database():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT UNIQUE,
            original_idea TEXT,
            problem TEXT,
            solution TEXT,
            target_customer TEXT,
            business_model TEXT,
            market TEXT,
            assumptions TEXT,
            status TEXT,
            created_at TEXT
        )
    """)

    connection.commit()
    connection.close()


def create_project(idea: str):

    connection = get_connection()
    cursor = connection.cursor()

    # Generate project ID
    cursor.execute("SELECT COUNT(*) FROM projects")
    count = cursor.fetchone()[0]

    project_id = f"VX-{count + 1:03d}"

    # Parse startup idea
    structured_idea = parse_idea(idea)

    created_at = datetime.now().isoformat()

    assumptions = "|".join(
        structured_idea["assumptions"]
    )

    cursor.execute("""
        INSERT INTO projects (
            project_id,
            original_idea,
            problem,
            solution,
            target_customer,
            business_model,
            market,
            assumptions,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        project_id,
        idea,
        structured_idea["problem"],
        structured_idea["solution"],
        structured_idea["target_customer"],
        structured_idea["business_model"],
        structured_idea["market"],
        assumptions,
        "INPUT_COMPLETED",
        created_at
    ))

    connection.commit()
    connection.close()

    return {
        "project_id": project_id,
        "original_idea": idea,
        "startup": structured_idea,
        "status": "INPUT_COMPLETED",
        "created_at": created_at
    }


def get_project(project_id: str):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            project_id,
            original_idea,
            problem,
            solution,
            target_customer,
            business_model,
            market,
            assumptions,
            status,
            created_at
        FROM projects
        WHERE project_id = ?
    """, (project_id,))

    row = cursor.fetchone()

    connection.close()

    if not row:
        return None

    return {
        "project_id": row[0],
        "original_idea": row[1],
        "startup": {
            "problem": row[2],
            "solution": row[3],
            "target_customer": row[4],
            "business_model": row[5],
            "market": row[6],
            "assumptions": row[7].split("|")
        },
        "status": row[8],
        "created_at": row[9]
    }