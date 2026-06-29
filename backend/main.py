from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importing the models package registers all ORM models with SQLAlchemy.
from app import models  # noqa: F401
from app.routes import links, redirect, analytics, users

# Create the FastAPI application instance.
app = FastAPI(title="LinkPulse API")

# Allow the Vite dev server (and other local origins) to call this API
# from the browser. Without CORS, the browser blocks cross-origin requests.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach the links router (adds POST /api/links and GET /api/links).
app.include_router(links.router)

# Attach the users router (adds GET /api/users).
app.include_router(users.router)

# Attach the analytics router (adds GET /api/analytics/{short_code}).
app.include_router(analytics.router)


# A GET endpoint at /health. It's a simple "is the server alive?" check.
@app.get("/health")
def health_check():
    return {"status": "ok"}


# Register the catch-all redirect router LAST so that specific paths like
# /health and /docs are matched before the /{short_code} wildcard.
app.include_router(redirect.router)
