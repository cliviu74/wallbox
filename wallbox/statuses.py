from aenum import MultiValueEnum


class Statuses(MultiValueEnum):
    WAITING = 164, 180, 181, 183, 184, 185, 186, 187, 188, 189,
    CHARGING = 193, 194, 195,
    READY = 161, 162,
    PAUSED = 178, 182,
    SCHEDULED = 177, 179,
    DISCHARGING = 196,
    ERROR = 14, 15,
    DISCONNECTED = 0, 163, None,
    LOCKED = 209, 210, 165,
    UPDATING = 166
