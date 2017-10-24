#==============================================================================
#                               Local Imports
#==============================================================================
from .constants import PACKAGE_NAME, LOGGING_LEVELS

#==============================================================================
#                               Global Imports
#==============================================================================
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

import pkg_resources

#==============================================================================
#                         Command line option handling
#==============================================================================
def register_options(option_parser=None):
    """ Command Line Option Handling """
    if option_parser is None:
        option_parser = ArgumentParser(
            description="PV Data Utilities",
            formatter_class=ArgumentDefaultsHelpFormatter,
        )

    option_parser.add_argument(
        "--data-folder",
        default=pkg_resources.resource_filename(PACKAGE_NAME, "dataset"),
        help="The pv data folder"
    )

    option_parser.add_argument(
        "--log-level",
        help="Logging level",
        choices=LOGGING_LEVELS.keys(),
        dest="log_level",
        default="info",
    )

    return option_parser
