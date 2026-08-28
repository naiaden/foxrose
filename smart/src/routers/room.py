from __future__ import annotations

from enum import Enum

from fastapi import APIRouter, HTTPException

router = APIRouter()

_home = None

# Placeholder; swapped for a dynamic `Enum` built from the home's rooms in
# `set_home()`. Because annotations are strings (thanks to the `__future__`
# import), FastAPI re-resolves `RoomId` against this module when routes are
# registered. As long as `set_home()` runs before `include_router()`, the docs
# page renders a dropdown of available rooms for every `/room/{room_id}` path.
RoomId: type = str

# Per-room scene rotation counters, keyed by room id. Persists at module level so
# successive `scene/next` calls rotate through the scenes instead of always
# selecting the first one.
current_scene_room: dict[str, int] = {}


def reset_scene_state() -> None:
    """Clear the per-room scene rotation counters (used by tests)."""
    current_scene_room.clear()


def set_home(h) -> None:
    global _home, RoomId
    _home = h

    rooms = [r for r in (getattr(h, "rooms", None) or [])]
    if rooms:
        # Member *names* must be valid identifiers, so use indexes; the
        # dropdown/validation uses the member *values* (the room ids).
        RoomId = Enum("RoomId", {f"room_{i}": r.id for i, r in enumerate(rooms)})
    else:
        RoomId = str


def _resolve_room_id(room_id: RoomId) -> str:
    """FastAPI hands the handler an Enum member when `room_id` is typed as the
    dynamic `RoomId`. Unwrap it to the plain room id string; plain strings pass
    through untouched (e.g. in tests or when no rooms are configured)."""
    return room_id.value if isinstance(room_id, Enum) else room_id


@router.get("/room")
async def room_list() -> list[tuple[str, str]]:
    """Overview of all rooms as defined by their comprising hue resources.

    Returns:
        list[tuple[str, str]]: List of room names and room ids.
    """
    return [(r.name, r.id) for r in _home.rooms]


@router.get("/room/{room_id}/scenes")
async def room_scenes(room_id: RoomId) -> list[str]:
    """Overview of all hue scenes in room `room_id`.

    Args:
        room_id (str): The hue id of the room.

    Returns:
        list[str]: List with names (not the ids) of hue scenes in the room.
    """
    room_id = _resolve_room_id(room_id)
    if room := _home.get_room_with_id(room_id):
        return [str(s) for s in room.scenes]
    raise HTTPException(status_code=404, detail="Room not found")


@router.get("/room/{room_id}")
async def room_info(room_id: RoomId) -> dict:
    room_id = _resolve_room_id(room_id)
    if room := _home.get_room_with_id(room_id):
        return room.summary()
    raise HTTPException(status_code=404, detail="Room not found")


@router.post("/room/{room_id}/active/{active}")
async def room_active(room_id: RoomId, active: str) -> None:
    """Set the state of all lamps in room `room_id` to `active`, regardless of their current state.

    \f
    Args:
        room_id (str): The hue id of the room.
        active (str): The (new) state for the room (`on` or `off`).
    """
    room_id = _resolve_room_id(room_id)
    if room := _home.get_room_with_id(room_id):
        for group in room.groups:
            group.on = active == "on"
    else:
        raise HTTPException(status_code=404, detail="Room not found")


@router.post("/room/{room_id}/night")
async def room_night(room_id: RoomId) -> None:
    """Activates the "Nightlight" scene in room `room_id`. This action only has an effect if the
    room has the "Nightlight" scene defined. Otherwise, nothing happens.

    \f
    Args:
        room_id (str): The hue id of the room.
    """
    room_id = _resolve_room_id(room_id)
    if room := _home.get_room_with_id(room_id):
        for scene in room.scenes:
            if scene.name == "Nightlight":
                scene.activate()
    else:
        raise HTTPException(status_code=404, detail="Room not found")


@router.post("/room/{room_id}/scene/next")
async def room_next(room_id: RoomId) -> None:
    """Rotate through the hue scenes defined in room `room_id`. The function keeps its own state
    of the scenes that have been chosen previously (e.g. the returned scene is not randomly
    chosen).

    The selected scene is activated for the room.

    \f
    Args:
        room_id (str): The hue id of the room.
    """
    room_id = _resolve_room_id(room_id)
    if room_id not in current_scene_room:
        current_scene_room[room_id] = 0

    if (room := _home.get_room_with_id(room_id)) and room.scenes:
        selected_scene = current_scene_room[room_id] % len(room.scenes)
        current_scene_room[room_id] += 1

        room.scenes[selected_scene].activate()
    else:
        raise HTTPException(status_code=404, detail="Room not found or no scenes")


@router.post("/room/{room_id}/scene/orientation")
async def room_orientation(room_id: RoomId) -> None:
    """Activates the "orientatie" hue scene in room `room_id`. This action only has an effect if the
    room has the "orientatie" scene defined. Otherwise, nothing happens.

    \f
    Args:
        room_id (str): The hue id of the room.
    """
    room_id = _resolve_room_id(room_id)
    if room := _home.get_room_with_id(room_id):
        for scene in room.scenes:
            if scene.name == "orientatie":
                scene.activate()
    else:
        raise HTTPException(status_code=404, detail="Room not found")


@router.post("/room/{room_id}/brightness/{brightness}/{duration_ms}")
async def room_brightness(room_id: RoomId, brightness: int, duration_ms: int) -> None:
    """Set the brightness of all groups in room `room_id` to `brightness`,
    fading over `duration_ms` milliseconds.

    The fade is achieved via the Hue API v2 ``dynamics.duration`` field
    (milliseconds). A ``duration_ms`` of ``0`` applies the brightness
    instantly. ``brightness`` is clamped to the range ``0–100``.

    \f
    Args:
        room_id (str): The hue id of the room.
        brightness (int): Target brightness (``0–100``).
        duration_ms (int): Fade duration in milliseconds (``0`` = instant).
    """
    room_id = _resolve_room_id(room_id)
    if room := _home.get_room_with_id(room_id):
        for group in room.groups:
            group.set_brightness(brightness, duration_ms)
    else:
        raise HTTPException(status_code=404, detail="Room not found")


@router.post("/room/{room_id}/scene/bright")
async def room_bright(room_id: RoomId) -> None:
    """Activates the "Bright" hue scene in room `room_id`. This action only has an effect if the
    room has the "Bright" scene defined. Otherwise, nothing happens.

    \f
    Args:
        room_id (str): The hue id of the room.
    """
    room_id = _resolve_room_id(room_id)
    if room := _home.get_room_with_id(room_id):
        for scene in room.scenes:
            if scene.name == "Bright":
                scene.activate()
    else:
        raise HTTPException(status_code=404, detail="Room not found")
