from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from database.main import db
from misc.exceptions import AppError
from .urls import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    
    # When server stopped
    await db.engine.dispose()


app = FastAPI(
    title="PR Reviewer Assignment Service",
    version="1.0.0",
    lifespan=lifespan
)

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)