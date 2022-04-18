#!/usr/bin/env python3
"""Starts PyLims using command-line."""
import os
import sys

# Change current working directory to the directory of this script.
os.chdir(os.path.dirname(os.path.realpath(__file__)))

from pylims.shell import Shell


def main():
    """Starts the application."""
    args = sys.argv[1:]
    app = Shell()
    code = app.main(args)
    sys.exit(code)


if __name__ == '__main__':
    main()
