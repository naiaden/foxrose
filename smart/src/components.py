from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

"""
    The highest level of abstraction for an actual house powered by hue lights.
    Recently, a second bridge was added to our home.
    
    A home consists of physical rooms and lamps, and abstract groups and scenes.
"""


class Home:
    """
    Create a new, and initialised home instance
    """

    def __init__(self, bridges) -> None:
        self.hues = bridges
        print(f"{len(self.hues)} bridges in this home")
        for b in self.hues:
            logger.debug(b.bridge.ip_address)

        self.initialise()

    """
        Rooms are lazily initialised, and its groups and scenes are added afterwards 
        as they can have a reference to their parent (Room).
    """

    def initialise(self) -> None:
        self.lamps = self.initialise_lamps()
        logger.info(f"{len(self.lamps)} lamps initialised")
        for lamp in self.lamps:
            logger.debug(
                lamp.id, lamp.name, lamp.parent_id, lamp.bridge.bridge.ip_address
            )

        self.rooms = self.initialise_rooms()
        logger.info(f"{len(self.rooms)} rooms lazily initialised")
        for r in self.rooms:
            print(str(r))

        self.scenes = self.initialise_scenes()
        logger.info(f"{len(self.scenes)} scenes initialised")
        for s in self.scenes:
            logger.debug(str(s))

        self.connect_scenes_to_rooms()

        self.groups = self.initialise_groups()
        print(f"{len(self.groups)} groups initialised")
        for g in self.groups:
            logger.debug(str(g))

        self.connect_groups_to_rooms()

    def connect_groups_to_rooms(self) -> None:
        for group in self.groups:
            room_id = group.reference.data_dict["owner"]["rid"]
            if room := self.get_room_with_id(room_id):
                room.groups.append(group)

    def connect_scenes_to_rooms(self) -> None:
        for scene in self.scenes:
            room_id = scene.reference.data.data_dict["group"]["rid"]
            if room := self.get_room_with_id(room_id):
                room.scenes.append(scene)

    def get_lamp_with_id(self, lamp_id: str) -> Lamp | None:
        for lamp in self.lamps:
            if lamp.id == lamp_id:
                return lamp

    def get_lamp_with_pid(self, lamp_pid: str) -> Lamp | None:
        for lamp in self.lamps:
            if lamp.parent_id == lamp_pid:
                return lamp

    def get_room_with_id(self, room_id: str) -> Room | None:
        for room in self.rooms:
            if room.id == room_id:
                return room

    def get_room_with_name(self, room_name: str) -> Room | None:
        for room in self.rooms:
            if room.name == room_name:
                return room

    def initialise_lamps(self) -> list[Lamp]:
        return [Lamp(light, bridge) for bridge in self.hues for light in bridge.lights]

    def initialise_rooms(self) -> list[Room]:
        return [Room(room, self) for bridge in self.hues for room in bridge.rooms]

    def initialise_scenes(self) -> list[Scene]:
        return [Scene(scene) for bridge in self.hues for scene in bridge.scenes]

    def initialise_groups(self) -> list[Group]:
        return [Group(group) for bridge in self.hues for group in bridge.grouped_lights]


class Room:
    def __init__(self, room, home: Home):
        self.id = room.id
        self.name = room.get().data_dict["metadata"]["name"]

        self.reference = room

        self.lamps = []
        for child in room.get().children:
            lamp = home.get_lamp_with_pid(child.data_dict["rid"])
            self.lamps.append(lamp)

        self.scenes = []
        self.groups = []

    def __str__(self) -> str:
        return f"{self.name} [{self.id}]"

    def summary(self) -> dict:
        return {
            "name": self.name,
            "id": self.id,
            "nr_lamps": len(self.lamps),
            "lamps": [(str(lamp), str(lamp.id)) for lamp in self.lamps],
            "nr_scenes": len(self.scenes),
            "scenes": [str(s) for s in self.scenes],
            "nr_groups": len(self.groups),
            "groups": [str(g) for g in self.groups],
        }


class Group:
    def __init__(self, group):
        self.id = group.data_dict["id"]

        self.reference = group

    def activate(self, active):
        self.reference.on = active

    def __str__(self):
        return f"{self.id}"

    @property
    def brightness(self):
        return self.reference.brightness

    @brightness.setter
    def brightness(self, brightness):
        self.on = True
        self.reference.brightness = max(0, min(brightness, 100))

    @property
    def on(self):
        return self.reference.on

    @on.setter
    def on(self, active):
        self.reference.on = active


class Scene:
    def __init__(self, scene):
        self.id = scene.id
        self.name = scene.data.data_dict["metadata"]["name"]

        self.reference = scene

    def activate(self):
        self.reference.recall(action="active")

    def __str__(self):
        return f"{self.name}"


class Lamp:
    def __init__(self, light, bridge):
        self.data = light.data_dict
        self.id = self.data["id"]
        self.name = self.data["metadata"]["name"]
        self.parent_id = self.data["owner"]["rid"]
        self.bridge = bridge

        self.reference = light

    @property
    def brightness(self):
        return self.reference.brightness

    @brightness.setter
    def brightness(self, brightness):
        self.reference.brightness = max(0, min(brightness, 100))
        self.on = True

    @property
    def colour(self):
        color_temp = self.reference.data_dict.get("color_temperature")
        if color_temp is not None:
            return ("mirek", color_temp["mirek"])
        return ("colour", self.reference.color_xy)

    @colour.setter
    def colour(self, value: int):
        if "color_temperature" in self.reference.data_dict:
            self.reference._set("color_temperature", {"mirek": value})
        else:
            self.reference.color_xy = value

    @property
    def on(self):
        return self.reference.on

    @on.setter
    def on(self, active):
        self.reference.on = active

    def __str__(self) -> str:
        return self.name

    def summary(self):
        return {
            "name": self.name,
            "id": self.id,
            "on": self.on,
            "brightness": self.brightness,
            "colour": self.colour,
            "data": self.reference.data_dict,
            "bridge": self.bridge.bridge.ip_address,
        }
