from fastapi import FastAPI

from backend.app.api import simulation_routes

app = FastAPI(title="PetroLumen API")
app.include_router(simulation_routes.router, prefix="/api")
