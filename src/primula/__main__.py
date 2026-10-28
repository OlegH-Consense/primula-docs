"""Entry point for ``python -m primula``; equivalent to the ``primula`` command."""

import sys

from primula.cli import main

if __name__ == "__main__":
    sys.exit(main())
