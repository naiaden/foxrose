from fastapi import APIRouter, HTTPException

router = APIRouter()

_home = None


def set_home(h) -> None:
    global _home
    _home = h


@router.get("/lamp/{lamp_id}")
async def lamp_info(lamp_id: str) -> dict:
    if lamp := _home.get_lamp_with_id(lamp_id):
        return lamp.summary()
    raise HTTPException(status_code=404, detail="Lamp not found")


@router.post("/lamp/{lamp_id}/active/{active}")
async def lamp_active(lamp_id: str, active: str) -> None:
    """Set the state of the hue lamp `lamp_id` to `active`, regardless of its current state.

    \f
    Args:
        lamp_id (str): The hue id of the lamp.
        active (str): The (new) state for the lamp (`on` or `off`).
    """
    if lamp := _home.get_lamp_with_id(lamp_id):
        lamp.on = active == "on"
    else:
        raise HTTPException(status_code=404, detail="Lamp not found")


@router.post("/lamp/{lamp_id}/brightness/{step}")
async def lamp_brightness(lamp_id: str, step: int) -> None:
    """Increases the brightness of lamp `lamp_id` with `value`. The result of the increment
    (which can be either positive or negative) is `0 <= brightness <= 100`, with overflows to
    either side being restricted.

    \f
    Args:
        lamp_id (str): The hue id of the lamp.
        step (int): The increment (or decrement) for the hue lamp.
    """
    if lamp := _home.get_lamp_with_id(lamp_id):
        lamp.brightness = lamp.brightness + int(step)
    else:
        raise HTTPException(status_code=404, detail="Lamp not found")


@router.post("/lamp/{lamp_id}/colour/{colour_value}")
async def lamp_colour(lamp_id: str, colour_value: int) -> None:
    if lamp := _home.get_lamp_with_id(lamp_id):
        lamp.colour = colour_value
    else:
        raise HTTPException(status_code=404, detail="Lamp not found")
