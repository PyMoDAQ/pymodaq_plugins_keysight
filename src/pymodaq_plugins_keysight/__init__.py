from pymodaq_utils.utils import get_version, PackageNotFoundError
from pathlib import Path

try:
    __version__ = get_version(__package__)
except PackageNotFoundError:
    __version__ = '0.0.0dev'
