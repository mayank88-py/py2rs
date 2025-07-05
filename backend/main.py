from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
import uvicorn
import os
import sys

# Add the backend directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from py2rs_transpiler import PythonToRustTranspiler

app = FastAPI(title="Python to Rust Converter", version="1.0.0")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize transpiler
transpiler = PythonToRustTranspiler()


class ConversionRequest(BaseModel):
    python_code: str


class ConversionResponse(BaseModel):
    rust_code: str
    success: bool
    error: Optional[str] = None


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main web UI."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/convert", response_model=ConversionResponse)
async def convert_python_to_rust(request: ConversionRequest):
    """Convert Python code to Rust code."""
    try:
        if not request.python_code.strip():
            raise HTTPException(status_code=400, detail="Python code cannot be empty")
        
        rust_code = transpiler.transpile(request.python_code)
        
        return ConversionResponse(
            rust_code=rust_code,
            success=True
        )
    except Exception as e:
        return ConversionResponse(
            rust_code="",
            success=False,
            error=str(e)
        )


@app.post("/convert-form")
async def convert_form(request: Request, python_code: str = Form(...)):
    """Handle form-based conversion for the web UI."""
    try:
        if not python_code.strip():
            rust_code = "// Please enter some Python code to convert"
            error = "No Python code provided"
        else:
            rust_code = transpiler.transpile(python_code)
            error = None
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "python_code": python_code,
            "rust_code": rust_code,
            "error": error
        })
    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "python_code": python_code,
            "rust_code": "",
            "error": str(e)
        })


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Python to Rust converter is running"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 