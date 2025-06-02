from typing import NamedTuple
from collections import namedtuple

DataBaseSettings = namedtuple('DBSetting', ['host', 'user', 'password', 'port', 'charset', 'database'])
db_config = DataBaseSettings(
    host="localhost",
    user="root",
    password="",
    port=3306,
    charset="utf8mb4",
    database="cine_db"
)