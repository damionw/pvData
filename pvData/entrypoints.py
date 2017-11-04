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

#==============================================================================
#                                Entry Point
#==============================================================================
if __name__ == "__main__":
    try:
        exit(main())
    except (KeyboardInterrupt):
        exit(0)
