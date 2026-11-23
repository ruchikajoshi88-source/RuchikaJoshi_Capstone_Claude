from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src import models  # noqa: F401  (registers Task on Base.metadata)
from src.database import Base, engine
from src.routers import tasks


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Task Management REST API", lifespan=lifespan)
app.include_router(tasks.router)
