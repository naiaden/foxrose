from fastapi import APIRouter, HTTPException

router = APIRouter()

_home = None

# Per-room scene rotation counters, keyed by room id. Persists at module level so
# successive `scene/next` calls rotate through the scenes instead of always
# selecting the first one.
current_scene_room: dict[str, int] = {}


def reset_scene_state() -> None:
    """Clear the per-room scene rotation counters (used by tests)."""
    current_scene_room.clear()


def set_home(h) -> None:
    global _home
    _home = h


@router.get("/room/{room_id}")
async def room_info(room_id: str) -> dict:
    if room := _home.get_room_with_id(room_id):
        return room.summary()
    raise HTTPException(status_code=404, detail="Room not found")


@router.post("/room/{room_id}/active/{active}")
async def room_active(room_id: str, active: str) -> None:
    """Set the state of all lamps in room `room_id` to `active`, regardless of their current state.

    \f
    Args:
        room_id (str): The hue id of the room.
        active (str): The (new) state for the room (`on` or `off`).
    """
    if room := _home.get_room_with_id(room_id):
        for group in room.groups:
            group.on = active == "on"
    else:
        raise HTTPException(status_code=404, detail="Room not found")


@router.post("/room/{room_id}/night")
async def room_night(room_id: str) -> None:
    """Activates the "Nightlight" scene in room `room_id`. This action only has an effect if the
    room has the "Nightlight" scene defined. Otherwise, nothing happens.

    \f
    Args:
        room_id (str): The hue id of the room.
    """
    if room := _home.get_room_with_id(room_id):
        for scene in room.scenes:
            if scene.name == "Nightlight":
                scene.activate()
    else:
        raise HTTPException(status_code=404, detail="Room not found")


@router.post("/room/{room_id}/scene/next")
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

    if (room := _home.get_room_with_id(room_id)) and room.scenes:
        selected_scene = current_scene_room[room_id] % len(room.scenes)
        current_scene_room[room_id] += 1

        room.scenes[selected_scene].activate()
    else:
        raise HTTPException(status_code=404, detail="Room not found or no scenes")


@router.post("/room/{room_id}/scene/orientation")
async def room_orientation(room_id: str) -> None:
    """Activates the "orientatie" hue scene in room `room_id`. This action only has an effect if the
    room has the "orientatie" scene defined. Otherwise, nothing happens.

    \f
    Args:
        room_id (str): The hue id of the room.
    """
    if room := _home.get_room_with_id(room_id):
        for scene in room.scenes:
            if scene.name == "orientatie":
                scene.activate()
    else:
        raise HTTPException(status_code=404, detail="Room not found")


@router.post("/room/{room_id}/scene/bright")
async def room_bright(room_id: str) -> None:
    """Activates the "Bright" hue scene in room `room_id`. This action only has an effect if the
    room has the "Bright" scene defined. Otherwise, nothing happens.

    \f
    Args:
        room_id (str): The hue id of the room.
    """
    if room := _home.get_room_with_id(room_id):
        for scene in room.scenes:
            if scene.name == "Bright":
                scene.activate()
    else:
        raise HTTPException(status_code=404, detail="Room not found")
