DOMAIN = "autonomic_m401"
DEFAULT_PORT = 17037
DEFAULT_ZONES = [5, 6, 7, 8]
DEFAULT_NAMES = ["Küche", "Wohnzimmer", "Bad", "Schlafzimmer"]

SOURCE_MAP = {
    "S1": 0x05,
    "S2": 0x06,
    "S3": 0x07,
    "S4": 0x03,
    "S5": 0x00,
    "S6": 0x01,
    "S7": 0x02,
    "S8": 0x04,
}
SOURCE_FROM_CODE = {v: k for k, v in SOURCE_MAP.items()}
