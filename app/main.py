from fastapi import FastAPI
from app.api import user_config, user_config_update, upload

app = FastAPI(title="My Intervals Backend")

@app.get("/")
def root():
    return {"message": "Welcome to the Intervals backend API."}

app.include_router(user_config.router, prefix="/api")
app.include_router(user_config_update.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
