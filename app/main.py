from fastapi import FastAPI

from app.api.routes.auth import router as auth_router

app = FastAPI(title="Stock Intelligence API", version="0.1.0")


@app.get("/")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth_router)
