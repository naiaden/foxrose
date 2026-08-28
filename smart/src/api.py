from fastapi import FastAPI
from python_hue_v2 import Hue

from .components import Home
from .config import get_hue_bridges, load_config
from .routers import home as home_router
from .routers import lamp as lamp_router
from .routers import room as room_router


def create_app() -> FastAPI:
    config = load_config()
    hue_bridges = get_hue_bridges()
    home = Home([Hue(b.ip, b.key) for b in hue_bridges])

    # Configure routers *before* registration so FastAPI resolves dynamic path
    # parameter types (e.g. the room-id dropdown) at route-registration time.
    home_router.set_home(home)
    home_router.set_config(config)
    room_router.set_home(home)
    lamp_router.set_home(home)

    app = FastAPI()

    app.include_router(home_router.router, prefix="", tags=["home"])
    app.include_router(room_router.router, prefix="", tags=["room"])
    app.include_router(lamp_router.router, prefix="", tags=["lamp"])

    @app.get("/")
    async def root():
        return {"message": "Hello World"}

    return app


app = create_app()
