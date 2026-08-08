from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from models import ReportRequest
from report_generator import generate_report
from pitch_generator import generate_pitch

import os


# ---------------------------------------
# PATHS
# ---------------------------------------

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

FRONTEND_DIR = os.path.join(
    BASE_DIR,
    "frontend"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "output"
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# ---------------------------------------
# FASTAPI
# ---------------------------------------

app = FastAPI(
    title="VentureX-Ray Report Module"
)


# ---------------------------------------
# HOME PAGE
# ---------------------------------------

@app.get(
    "/",
    response_class=HTMLResponse
)
async def home():

    html_file = os.path.join(
        FRONTEND_DIR,
        "index.html"
    )

    if not os.path.exists(html_file):
        return HTMLResponse(
            content="<h1>index.html not found</h1>",
            status_code=404
        )

    with open(
        html_file,
        "r",
        encoding="utf-8"
    ) as file:

        return file.read()


# ---------------------------------------
# STATIC FILES
# ---------------------------------------
# CSS / JS / images should be accessed as:
#
# /static/style.css
# /static/script.js
# /static/images/example.png
#
# ---------------------------------------

app.mount(
    "/static",
    StaticFiles(
        directory=FRONTEND_DIR
    ),
    name="static"
)


# ---------------------------------------
# GENERATE REPORT
# ---------------------------------------

@app.post("/generate-report")
async def create_report(
    data: ReportRequest
):

    report_path = os.path.join(
        OUTPUT_DIR,
        "final_report.pdf"
    )

    pitch_path = os.path.join(
        OUTPUT_DIR,
        "final_pitch.pptx"
    )

    # Generate PDF report
    generate_report(
        data,
        report_path
    )

    # Generate PowerPoint pitch deck
    generate_pitch(
        data,
        pitch_path
    )

    return {
        "status": "success",
        "message": "Report and pitch deck generated successfully.",
        "report": "/download/report",
        "pitch_deck": "/download/pitch"
    }


# ---------------------------------------
# DOWNLOAD PDF
# ---------------------------------------

@app.get("/download/report")
async def download_report():

    file_path = os.path.join(
        OUTPUT_DIR,
        "final_report.pdf"
    )

    if not os.path.exists(file_path):

        return {
            "error": "Report has not been generated yet."
        }

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename="final_report.pdf"
    )


# ---------------------------------------
# DOWNLOAD PPTX
# ---------------------------------------

@app.get("/download/pitch")
async def download_pitch():

    file_path = os.path.join(
        OUTPUT_DIR,
        "final_pitch.pptx"
    )

    if not os.path.exists(file_path):

        return {
            "error": "Pitch deck has not been generated yet."
        }

    return FileResponse(
        path=file_path,
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "presentationml.presentation"
        ),
        filename="final_pitch.pptx"
    )