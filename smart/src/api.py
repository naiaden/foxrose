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


######### HOME

room_previous_state = {}

def _every_room_inactive():
    res = True
    for room in home.rooms:
        for group in room.groups:
            print(f'{room.id} -- {group.id} -- {group.on} -- {group.brightness}')
            if group.on:
                res = False

    return res

@app.get('/home')
async def home_overview():
    return {'home_active': not _every_room_inactive()}
#            'rooms': {
#                {'room_id': r.id,
#                 'groups': {
#                     g.id for g in r.groops
#                 }

@app.post('/home/active/toggle')
async def home_toggle():
    if _every_room_inactive():
        _room_active("9755fa99-be58-4f8d-bb83-c880f7bc193f", "on") # eetkamer
        _room_active("be712559-b2d8-4fb3-b5ea-5a97a66e5de4", "on") # woonkamer
    else:
        _ikea_active("off")
        for room in home.rooms:
            _room_active(room.id, "off")

@app.post('/home/active/{active}')
async def home_active(active):
    for room in home.rooms:
        _room_active(room.id, active)
    _ikea_active(active)

def _ikea_active(active):
    active_val = active == "true" or active == "on"
    devices_command = gateway.get_devices()
    devices_commands = api(devices_command)
    devices = api(devices_commands)
    for socket in [d for d in devices if d.has_socket_control]:
        api(socket.socket_control.set_state(1 if active_val else 0))

######### ROOM

@app.get('/room')
async def room_list():
    return [(r.name, r.id) for r in home.rooms]

@app.get('/room/{room_id}')
async def room_info(room_id):
    if room := home.get_room_with_id(room_id):
        return room.summary()

def _room_active(room_id, active):
    if room := home.get_room_with_id(room_id):
        active_val = active == "true" or active == "on"

        for group in room.groups:
            group.activate(active_val)

@app.post('/room/{room_id}/active/{active}')
async def room_active(room_id, active):
    return _room_active(room_id, active)
#    if room := home.get_room_with_id(room_id):
#        active_val = active == "true" or active == "on"
#        
#        for group in room.groups:
#            group.activate(active_val)


@app.post('/room/{room_id}/brightness/{step}')
async def room_brightness(room_id, step):
    if room := home.get_room_with_id(room_id):
        for group in room.groups:
            group.brightness = group.brightness + int(step)

@app.get('/room/{room_id}/scenes')
async def room_scenes(room_id):
    if room := home.get_room_with_id(room_id):
        return [str(s) for s in room.scenes]

@app.post('/room/{room_id}/scene/night')
async def room_night(room_id):
    if room := home.get_room_with_id(room_id):
        for scene in room.scenes:
            if scene.name == "Nightlight":
                scene.activate()

current_scene_room = {}
@app.post('/room/{room_id}/scene/next')
async def room_next(room_id):
    if room_id not in current_scene_room:
        current_scene_room[room_id] = 0


    if room := home.get_room_with_id(room_id):
        selected_scene = current_scene_room[room_id] % len(room.scenes)
        current_scene_room[room_id] += 1

        room.scenes[selected_scene].activate()


    

@app.post('/room/{room_id}/scene/bright')
async def room_bright(room_id):
    if room := home.get_room_with_id(room_id):
        for scene in room.scenes:
            if scene.name == "Bright":
                scene.activate()


########## LAMP

@app.post('/lamp/{lamp_id}/active/{active}')
async def lamp_active(lamp_id, active):
    if lamp := home.get_lamp_with_id(lamp_id):
        lamp.on = active == "true" or active == "on"

@app.post('/lamp/{lamp_id}/brightness/{step}')
async def lamp_brightness(lamp_id, step):
    if lamp := home.get_lamp_with_id(lamp_id):
        lamp.brightness = lamp.brightness + int(step)

#
