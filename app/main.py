from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.portfolios import router as portfolios_router
from app.api.routes.stocks import router as stocks_router
from app.api.routes.watchlists import router as watchlists_router

app = FastAPI(title="Stock Intelligence API", version="0.1.0")


@app.get("/")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(stocks_router)
app.include_router(watchlists_router)
app.include_router(portfolios_router)
