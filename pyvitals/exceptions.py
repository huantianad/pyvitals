from pathlib import Path
from zipfile import BadZipFile


class BaseError(Exception):
    """
    Base exception class for all pyvitals exceptions.
    """
    pass


class BadRDZipFile(BaseError, BadZipFile):
    """
    Raised when a rdzip file is incorrectly zipped, or unable to be unzipped.
    """

    def __init__(self, message: str, file_path: Path) -> None:  # TODO: better path type hint
        self.message = message
        self.file_path = file_path
        super().__init__(self.message)


class BadURLFilename(BaseError):
    """
    Raised when unable to get the filename from a url.
    """

    def __init__(self, message: str, url: str) -> None:
        self.message = message
        self.url = url
        super().__init__(self.message)
