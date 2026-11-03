from fastapi import FastAPI

from .api import engine_routes, simulation_routes

app = FastAPI(title="PetroLumen API")
app.include_router(simulation_routes.router, prefix="/api")
app.include_router(engine_routes.router, prefix="/api")

from fastapi.responses import RedirectResponse

@app.get('/', include_in_schema=False)
async def root():
    return RedirectResponse(url='/docs')
