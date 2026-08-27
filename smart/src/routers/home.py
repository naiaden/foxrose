from enum import Enum

from fastapi import APIRouter

from ..config import SmartConfig

router = APIRouter()

_home = None
_config: SmartConfig | None = None


def set_home(h) -> None:
    global _home
    _home = h


def set_config(c: SmartConfig) -> None:
    global _config
    _config = c


class ActiveState(str, Enum):
    off = "off"
    on = "on"
    true = "on"  # noqa: PIE796
    false = "off"  # noqa: PIE796


def _any_room_active() -> bool:
    """Checks whether any hue lamps are on.

    \f
    Returns:
        bool: `True` if any hue lamps are on.
    """
    for room in _home.rooms:
        for group in room.groups:
            print(f"{room.id} -- {group.id} -- {group.on} -- {group.brightness}")
            if group.on:
                return True

    return False


def _room_active(room_id: str, active: ActiveState) -> None:
    """Change the state of all lamps in room `room_id` to `active`.

    \f
    Args:
        room_id (str): The hue id of the room.
        active (ActiveState): The (new) state for the room.
    """
    active_val = active == ActiveState.on
    if room := _home.get_room_with_id(room_id):
        for group in room.groups:
            group.on = active_val


@router.get("/home")
async def home_overview() -> dict:
    """An overview of the state of the home

    \f
    Returns:
        dict: A json response with the home's state.
    """
    return {"home_active": _any_room_active(), "nr_bridges": len(_home.hues)}


@router.post("/home/update")
async def home_update() -> None:
    """Processes all changes in the bridges, such as new scenes for the rooms, new references
    to lights, and new rooms on the existing bridges.
    """
    _home.initialise()


@router.post("/home/active/toggle")
async def home_toggle() -> None:
    """If any of the hue lights are on, the home is considered to be active. A toggle on home
    then turns off all hue lamps.
    If none of the hue lights are on, the home is considered to be inactive. A toggle on home
    then turns on the default active rooms.
    """
    if _any_room_active():
        for room in _home.rooms:
            _room_active(room.id, "off")
    else:
        for room_id in _config.default_active_rooms:
            _room_active(room_id, "on")


@router.post("/home/active/{active}")
async def home_active(active: ActiveState) -> None:
    """Change the state of the hue lamps to `active`. The state is applied
    to all respective lamps, regardless of their current state.

    \f
    Args:
        active (ActiveState): The (new) state for all resources in the home.
    """
    for room in _home.rooms:
        _room_active(room.id, active)
