#==============================================================================
#                             Global Imports
#==============================================================================
from functools import wraps

import logging

#==============================================================================
#                                Logging
#==============================================================================
LOG = logging.getLogger(__name__)

#==============================================================================
#                            Decorators
#==============================================================================
def cast(type_reference):
    """ Cast the passed in value to the specified type """
    def cast_decorator(call_reference):
        @wraps(call_reference)
        def cast_wrapper(*args, **kwargs):
            return type_reference(call_reference(*args, **kwargs))

        return cast_wrapper

    return cast_decorator

def cached(function_reference):
    @wraps(function_reference)
    def mywrapper(*args, **kwargs):
        cache_name = "_cached_result_%s" % id((args + (None,))[0])

        if not hasattr(function_reference, cache_name):
            setattr(function_reference, cache_name, function_reference(*args, **kwargs))

        return getattr(function_reference, cache_name)

    return mywrapper
