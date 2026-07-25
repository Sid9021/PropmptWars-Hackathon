from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import crisis_router, prevent_router, auth_router
from .db import init_db

app = FastAPI(title="Recover Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(crisis_router.router)
app.include_router(prevent_router.router)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
def read_root():
    return {"message": "Welcome to Recover Platform Backend"}
