#! /usr/bin/env python

#==============================================================================
#                               Local Imports
#==============================================================================
from .options import register_options
from .dataset import pvDataSet

#==============================================================================
#                               Global Imports
#==============================================================================
import logging
import code

#==============================================================================
#                                   Logging
#==============================================================================
LOG = logging.getLogger(__name__)

#==============================================================================
#                                  Entry Points
#==============================================================================
def main():
    option_parser = register_options()
    arguments = option_parser.parse_args()
    logging.basicConfig(level=arguments.log_level.upper())

    dataset = pvDataSet(
        folder=arguments.data_folder,
    )

    df = dataset.full

    code.interact(local=dict(globals().items() + locals().items()))

def pvdata():
    def _register_options(option_parser=None):
        """ Command Line Option Handling
        """
        if option_parser is None:
            option_parser = ArgumentParser(
                description="PV Data Statistics",
                formatter_class=ArgumentDefaultsHelpFormatter,
            )

        option_parser = register_options(option_parser)

        option_parser.add_argument(
            "--sync",
            default=None,
            destination="sync_folder",
            help="Import data from folder"
        )

        return option_parser

    option_parser = _register_options()
    arguments = option_parser.parse_args()

    logging.basicConfig(level=arguments.log_level.upper())

    dataset = pvDataSet(
        folder=arguments.data_folder,
    )

    if exists(arguments.sync_folder):
        dataset.sync(folder=arguments.sync_folder)

#==============================================================================
#                                Entry Point
#==============================================================================
if __name__ == "__main__":
    try:
        exit(main())
    except (KeyboardInterrupt):
        exit(0)
