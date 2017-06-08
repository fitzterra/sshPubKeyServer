#!/usr/bin/env python
"""
Runs the key server.
"""
import sys

# From here: https://gist.github.com/balloob/c7ff7f91458350b548c7
def is_virtual():
    """ Return if we run in a virtual environtment. """
    # Check supports venv && virtualenv
    return (getattr(sys, 'base_prefix', sys.prefix) != sys.prefix or
            hasattr(sys, 'real_prefix'))

assert is_virtual(), "You need to run this from an activated virtual environment."


if __name__ == "__main__":
    from keyServer.server import startServer
    startServer()
