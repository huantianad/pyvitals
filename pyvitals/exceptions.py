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


class No2PLevel(BaseError):
    """
    Raised when trying to parse the seperate 2P level when it doesn't exist
    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)
