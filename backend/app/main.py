from fastapi import FastAPI

from .database import Base, engine
from .routes import logs, metrics

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Personal Tracker API")

app.include_router(metrics.router)
app.include_router(logs.router)


@app.get("/")
def root():
    return {"status": "ok"}