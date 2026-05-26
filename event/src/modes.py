from enum import Enum

class ModeDetails:
    def __init__(self, name, label):
        self.name = name
        self.label = label

class Mode(Enum):
    _ignore_ = ['_by_name_map']

    STANDARD = ModeDetails("All", "🌐 All")
    AWAY = ModeDetails("Away", "🧳 Away") # Trigger on all events, including presence detection
    NIGHT = ModeDetails("Night", "🌙 Night") # Ignore notifications that make sense, such as presence in bed room
    AT_HOME = ModeDetails("At Home", "🏠 At Home") # Ignore inside presence
    


    @classmethod
    def from_name(cls, name_string):
        # If the cache attribute doesn't exist yet, create it on the fly
        if not hasattr(cls, '_by_name_map'):
            cls._by_name_map = {member.value.name: member for member in cls}
            
        return cls._by_name_map.get(name_string)

    @classmethod
    def from_label(cls, label_string):
        # If the cache attribute doesn't exist yet, create it on the fly
        if not hasattr(cls, '_by_label_map'):
            cls._by_label_map = {member.value.label: member for member in cls}
            
        return cls._by_label_map.get(label_string)

    # def handle_presence(self, room:str) -> bool:
    #     match self:
    #         case Mode.STANDARD:
    #             return True  # Always notify in standard mode
                
    #         case Mode.NIGHT:
    #             # Ignore bedroom presence at night, but notify for other rooms
    #             return room.lower() != "bedroom"
                
    #         case Mode.AWAY:
    #             return True  # Always notify if away

    #         case _:
    #             return True

    @property
    def display_name(self):
        return self.value.name

    @property
    def label(self):
        return self.value.label