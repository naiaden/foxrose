from fastapi import FastAPI

from python_hue_v2 import Hue
from pytradfri import Gateway
from pytradfri.api.libcoap_api import APIFactory

from .config import settings
from .components import Home

home = Home(Hue(settings.HUE_IP, settings.hue_key))

app = FastAPI()


api_factory = APIFactory(host=settings['TRADFRI_IP'], psk_id=settings['tradfri_identity'], psk=settings['tradfri_key'])

api = api_factory.request

gateway = Gateway()

@app.get("/")
async def root():
    return {"message": "Hello World"}

from enum import Enum 
class ActiveState(str, Enum):
    off = "off"
    on = "on"
    true = "on"
    false = "off"

######### HOME

def _every_room_inactive() -> bool:
    """Checks whether all hue lamps are off. An (impossible) brightness of 0 does not mean that
    the light is off; it only checks the state of the lamps.
    \f
    Returns:
        bool: `true` if all hue lamps are off.
    """
    res = True
    for room in home.rooms:
        for group in room.groups:
            # print(f'{room.id} -- {group.id} -- {group.on} -- {group.brightness}')
            if group.on:
                res = False

    return res

@app.get('/home')
async def home_overview() -> dict:
    """An overview of the state of the home
    \f
    Returns:
        dict: A json response with the home's state.
    """
    return {'home_active': not _every_room_inactive()}

@app.post('/home/active/toggle')
async def home_toggle() -> None:
    """If any of the hue lights are on, the home is considered to be active. A toggle on home
    then turns off all hue lamps and tradfri resources.
    If none of the hue lights are on, the home is considered to be inactive. A toggle on home
    then turns on selected rooms (eetkamer and woonkamer for now).
    """
    if _every_room_inactive():
        _room_active("9755fa99-be58-4f8d-bb83-c880f7bc193f", "on") # eetkamer
        _room_active("be712559-b2d8-4fb3-b5ea-5a97a66e5de4", "on") # woonkamer
    else:
        _ikea_active("off")
        for room in home.rooms:
            _room_active(room.id, "off")

@app.post('/home/active/{active}')
async def home_active(active: ActiveState) -> None:
    """Change the state of the hue lamps and tradfri resources to `active`. The state is applied 
    to all respective lamps and resources, regardless of their current state.
    \f
    Args:
        active (ActiveState): The (new) state for all resources in the home.
    """
    for room in home.rooms:
        _room_active(room.id, active)
    _ikea_active(active)

def _ikea_active(active: ActiveState) -> None:
    """Change the state of tradfri resources to `active`. The state is applied to all tradfri
    socket resources, regardless of their current state.
    \f
    Args:
        active (ActiveState): The (new) state for all tradfri sockets in the home.
    """
    active_val = active == ActiveState.on
    devices_command = gateway.get_devices()
    devices_commands = api(devices_command)
    devices = api(devices_commands)
    for socket in [d for d in devices if d.has_socket_control]:
        api(socket.socket_control.set_state(1 if active_val else 0))

######### ROOM

@app.get('/room')
async def room_list() -> list[tuple[str, str]]:
    """Overview of all rooms as defined by their comprising hue resources.
    \f
    Returns:
        list[tuple[str, str]]: List of room names and room ids.
    """
    return [(r.name, r.id) for r in home.rooms]

@app.get('/room/{room_id}')
async def room_info(room_id:str) -> dict:
    """Overview of the hue room `room_id`.
    \f
    Args:
        room_id (str): The hue id of the room.

    Returns:
        dict: Overview of the number of resources in the room, and their values.
    """
    if room := home.get_room_with_id(room_id):
        return room.summary()

def _room_active(room_id: str, active: ActiveState) -> None:
    """Set the state of the hue lamps in room `room_id` to `active`, regardless of their current
    state.
    \f
    Args:
        room_id (str): The hue id of the room.
        active (ActiveState): The (new) state for all hue lamps in the room.
    """
    if room := home.get_room_with_id(room_id):
        active_val = active == ActiveState.on

        for group in room.groups:
            group.activate(active_val)

@app.post('/room/{room_id}/active/{active}')
async def room_active(room_id:str, active:ActiveState) -> None:
    """Set the state of the hue lamps in room `room_id` to `active`, regardless of their current
    state.
    \f
    Args:
        room_id (str): The hue id of the room.
        active (ActiveState): The (new) state for all hue lamps in the room.
    """
    return _room_active(room_id, active)


@app.post('/room/{room_id}/brightness/increase_to/{value}')
async def room_increase_to(room_id: str, value: int) -> None:
    """Increases the brightness of room `room_id` to `value`. If the current brightness is lower
    than `value`, the brightness is increased to `value`. Otherwise, the brightness remains
    unchanged.

    This method can be used to implement the incremental steps to mimic a wake-up light. If the
    brightness of the room is below the `value` treshold, you do not want it to go darker first.
    \f
    Args:
        room_id (str): The hue id of the room.
        value (int): The (new) maximum brightness value of the hue lamps in the room.
    """
    if room := home.get_room_with_id(room_id):
        for group in room.groups:
            group.brightness = max(value, group.brightness)

@app.post('/room/{room_id}/brightness/{step}')
async def room_brightness(room_id: str, step: int) -> None:
    """Increases the brightness of room `room_id` with `value`. The result of the increment 
    (which can be either positive or negative) is `0 <= brightness <= 100`, with overflows to
    either side being restricted.
    \f
    Args:
        room_id (str): The hue id of the room.
        step (int): The increment (or decrement) for the hue lamps in the room.
    """
    if room := home.get_room_with_id(room_id):
        for group in room.groups:
            group.brightness = group.brightness + step



@app.get('/room/{room_id}/scenes')
async def room_scenes(room_id: str) -> list[str]:
    """Overview of all hue scenes in room `room_id`.
    \f
    Args:
        room_id (str): The hue id of the room.

    Returns:
        list[str]: List with names (not the ids) of hue scenes in the room.
    """
    if room := home.get_room_with_id(room_id):
        return [str(s) for s in room.scenes]

@app.post('/room/{room_id}/scene/night')
async def room_night(room_id: str) -> None:
    """Activates the "Nightlight" hue scene in room `room_id`. This action only has an effect if
    the room has the "Nightlight" scene defined. Otherwise, nothing happs.
    \f
    Args:
        room_id (str): The hue id of the room.
    """
    if room := home.get_room_with_id(room_id):
        for scene in room.scenes:
            if scene.name == "Nightlight":
                scene.activate()

current_scene_room = {}
@app.post('/room/{room_id}/scene/next')
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


    if room := home.get_room_with_id(room_id):
        selected_scene = current_scene_room[room_id] % len(room.scenes)
        current_scene_room[room_id] += 1

        room.scenes[selected_scene].activate()


    

@app.post('/room/{room_id}/scene/bright')
async def room_bright(room_id: str) -> None:
    """Activates the "Bright" hue scene in room `room_id`. This action only has an effect if the 
    room has the "Bright" scene defined. Otherwise, nothing happs.
    \f
    Args:
        room_id (str): The hue id of the room.
    """
    if room := home.get_room_with_id(room_id):
        for scene in room.scenes:
            if scene.name == "Bright":
                scene.activate()


########## LAMP

@app.post('/lamp/{lamp_id}/active/{active}')
async def lamp_active(lamp_id: str, active: ActiveState) -> None:
    """Set the state of the hue lamp `lamp_id` to `active`, regardless of its current state.
    \f
    Args:
        lamp_id (str): The hue id of the lamp.
        active (ActiveState): The (new) state for the lamp.
    """
    if lamp := home.get_lamp_with_id(lamp_id):
        lamp.on = active == ActiveState.on

@app.post('/lamp/{lamp_id}/brightness/{step}')
async def lamp_brightness(lamp_id: str, step:int) -> None:
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

