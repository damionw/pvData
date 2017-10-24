#==============================================================================
#                                 Global Imports
#==============================================================================
from os import getenv

import logging

#==============================================================================
#                                Logging constants
#==============================================================================
LOGGING_LEVELS = {
    _name.lower(): logging._levelNames[_name]
    for _name
    in logging._levelNames
    if type(_name) != type(0)
}

#==============================================================================
#                                  Package Naming
#==============================================================================
PACKAGE_NAME = 'pvData'

#==============================================================================
#                                  Files / Folders
#==============================================================================
DEFAULT_FOLDER=getenv("DATADIR")

class FileTypes(object):
    Consumption = "XBSYS.LOAD.P.csv"
    Generation = "XBSYS.PV.P.csv"
    Battery = "XBSYS.BATT_BANK1_V.csv"
