from enum import Enum

from fastapi import FastAPI
from python_hue_v2 import Hue

from .components import Home
from .config import get_hue_bridges, load_config

config = load_config()

hue_bridges = get_hue_bridges()
home = Home([Hue(b.ip, b.key) for b in hue_bridges])

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


class ActiveState(str, Enum):
    off = "off"
    on = "on"
    true = "on"  # noqa: PIE796
    false = "off"  # noqa: PIE796


######### HOME


def _any_room_active() -> bool:
    """Checks whether any hue lamps are on.

    \f
    Returns:
        bool: `True` if any hue lamps are on.
    """
    for room in home.rooms:
        for group in room.groups:
            print(f"{room.id} -- {group.id} -- {group.on} -- {group.brightness}")
            if group.on:
                return True

    return False


@app.get("/home")
async def home_overview() -> dict:
    """An overview of the state of the home

    \f
    Returns:
        dict: A json response with the home's state.
    """
    return {"home_active": _any_room_active(), "nr_bridges": len(home.hues)}


@app.post("/home/update")
async def home_update() -> None:
    """Processes all changes in the bridges, such as new scenes for the rooms, new references
    to lights, and new rooms on the existing bridges.
    """
    home.initialise()


@app.post("/home/active/toggle")
async def home_toggle() -> None:
    """If any of the hue lights are on, the home is considered to be active. A toggle on home
    then turns off all hue lamps.
    If none of the hue lights are on, the home is considered to be inactive. A toggle on home
    then turns on the default active rooms.
    """
    if _any_room_active():
        for room in home.rooms:
            _room_active(room.id, "off")
    else:
        for room_id in config.default_active_rooms:
            _room_active(room_id, "on")


@app.post("/home/active/{active}")
async def home_active(active: ActiveState) -> None:
    """Change the state of the hue lamps to `active`. The state is applied
    to all respective lamps, regardless of their current state.

    \f
    Args:
        active (ActiveState): The (new) state for all resources in the home.
    """
    for room in home.rooms:
        _room_active(room.id, active)


def _room_active(room_id: str, active: ActiveState) -> None:
    """Change the state of all lamps in room `room_id` to `active`.

    \f
    Args:
        room_id (str): The hue id of the room.
        active (ActiveState): The (new) state for the room.
    """
    active_val = active == ActiveState.on
    if room := home.get_room_with_id(room_id):
        for group in room.groups:
            group.on = active_val


########## ROOM


@app.get("/room/{room_id}")
async def room_info(room_id: str) -> dict:
    if room := home.get_room_with_id(room_id):
        return room.summary()


@app.post("/room/{room_id}/active/{active}")
async def room_active(room_id: str, active: ActiveState) -> None:
    """Set the state of all lamps in room `room_id` to `active`, regardless of their current state.

    \f
    Args:
        room_id (str): The hue id of the room.
        active (ActiveState): The (new) state for the room.
    """
    _room_active(room_id, active)


@app.post("/room/{room_id}/night")
async def room_night(room_id: str) -> None:
    """Activates the "Nightlight" scene in room `room_id`. This action only has an effect if the
    room has the "Nightlight" scene defined. Otherwise, nothing happens.

    \f
    Args:
        room_id (str): The hue id of the room.
    """
    if room := home.get_room_with_id(room_id):
        for scene in room.scenes:
            if scene.name == "Nightlight":
                scene.activate()


current_scene_room = {}


@app.post("/room/{room_id}/scene/next")
async def room_next(room_id: str) -> None:
    """Rotate through the hue scenes defined in room `room_id`. The function keeps its own state
    of the scenes that have been chosen previously (e.g. the returned scene is not randomly
    chosen).

    The selected scene is activated for the room.

    \f
    Args:
        room_id (str): The hue id of the room.
    """

    if room_id not in current_scene_room:
        current_scene_room[room_id] = 0

    if (room := home.get_room_with_id(room_id)) and room.scenes:
        selected_scene = current_scene_room[room_id] % len(room.scenes)
        current_scene_room[room_id] += 1

        room.scenes[selected_scene].activate()


@app.post("/room/{room_id}/scene/orientation")
async def room_orientation(room_id: str) -> None:
    """Activates the "orientatie" hue scene in room `room_id`. This action only has an effect if the
    room has the "orientatie" scene defined. Otherwise, nothing happens.

    \f
    Args:
        room_id (str): The hue id of the room.
    """
    if room := home.get_room_with_id(room_id):
        for scene in room.scenes:
            if scene.name == "orientatie":
                scene.activate()


@app.post("/room/{room_id}/scene/bright")
async def room_bright(room_id: str) -> None:
    """Activates the "Bright" hue scene in room `room_id`. This action only has an effect if the
    room has the "Bright" scene defined. Otherwise, nothing happens.

    \f
    Args:
        room_id (str): The hue id of the room.
    """
    if room := home.get_room_with_id(room_id):
        for scene in room.scenes:
            if scene.name == "Bright":
                scene.activate()


########## LAMP


@app.get("/lamp/{lamp_id}")
async def lamp_info(lamp_id: str) -> dict:
    if lamp := home.get_lamp_with_id(lamp_id):
        return lamp.summary()


@app.post("/lamp/{lamp_id}/active/{active}")
async def lamp_active(lamp_id: str, active: ActiveState) -> None:
    """Set the state of the hue lamp `lamp_id` to `active`, regardless of its current state.

    \f
    Args:
        lamp_id (str): The hue id of the lamp.
        active (ActiveState): The (new) state for the lamp.
    """
    if lamp := home.get_lamp_with_id(lamp_id):
        lamp.on = active == ActiveState.on


@app.post("/lamp/{lamp_id}/brightness/{step}")
async def lamp_brightness(lamp_id: str, step: int) -> None:
    """Increases the brightness of lamp `lamp_id` with `value`. The result of the increment
    (which can be either positive or negative) is `0 <= brightness <= 100`, with overflows to
    either side being restricted.

    \f
    Args:
        lamp_id (str): The hue id of the lamp.
        step (int): The increment (or decrement) for the hue lamp.
    """
    if lamp := home.get_lamp_with_id(lamp_id):
        lamp.brightness = lamp.brightness + int(step)


@app.post("/lamp/{lamp_id}/colour/{colour_value}")
async def lamp_colour(lamp_id: str, colour_value: int) -> None:
    if lamp := home.get_lamp_with_id(lamp_id):
        lamp.colour = colour_value
