
from miio import AirPurifierMiot as AirPurifier
from miio import AirHumidifierJsqs as AirHumidifier
from discovery import get_mi_devices

import os

get_mi_devices(username=os.environ.get('MI_USERNAME'))

air_purifier = AirPurifier(ip='192.168.1.66', token='6f1f001e582df06081595926fb344074')
humidifier = AirHumidifier(ip='192.168.1.63', token='5aa0046065ab93e4ef93d0b2d49caf19')
# status = air_purifier.status()
# status = humidifier.status()

# todo - cfg describing home layout inc. what devices are in each room (+token) (YAML)
# todo - persistence to a database through a database writer thread (use messaging queue)
# todo - monitor (AT, RH, AQI) to database
# todo - visualisation (flutter)
# todo - automation
# todo - daemon tool and deploy on homeserver

# home
#     room
#         dev1
#             name
#             ip
#             token
#             param
#               unit poll

# https://hackersandslackers.com/simplify-your-python-projects-configuration/