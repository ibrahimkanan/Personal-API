from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routes import logs, metrics, sessions, tasks

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Personal Tracker API")

# Lets the Electron renderer call this API:
#  - http://localhost:5173 is the Vite dev server
#  - "null" is the origin of a packaged Electron app loaded from file://
# Tighten this if you ever deploy the API publicly.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "null"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(metrics.router)
app.include_router(logs.router)
app.include_router(sessions.router)
app.include_router(tasks.router)


@app.get("/")
def root():
    return {"status": "ok"}