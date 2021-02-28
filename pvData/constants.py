#==============================================================================
#                                 Global Imports
#==============================================================================
from os import getenv

import pkg_resources
import logging

#==============================================================================
#                                Logging constants
#==============================================================================
LOGGING_LEVELS = {
    _name.lower(): _lookup[_name]
    for _attrname in ["_levelNames", "_levelToName"]
    for _lookup in [getattr(logging, _attrname, None)] if _lookup is not None 
    for _name in _lookup.keys()
    if type(_name) != type(0)
}

#==============================================================================
#                                  Package Naming
#==============================================================================
PACKAGE_NAME = 'pvData'

#==============================================================================
#                                  Files / Folders
#==============================================================================
PACKAGE_DATASET_VARIABLE = "PVDATA_DATASET"

DEFAULT_DATASET = getenv(
    PACKAGE_DATASET_VARIABLE,
    pkg_resources.resource_filename(PACKAGE_NAME, "dataset"),
)

#==============================================================================
#                                    Enumerations
#==============================================================================
class FileTypes(object):
    Consumption = "XBSYS.LOAD.P.csv"
    Generation = "XBSYS.PV.P.csv"
    Battery = "XBSYS.BATT_BANK1_V.csv"
