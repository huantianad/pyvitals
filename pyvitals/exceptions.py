class BaseError(Exception):
    """
    Base exception class for all pyvitals exceptions.
    """
    pass


class BadRDZipFile(BaseError):
    """
    Raised when a rdzip file is incorrectly zipped, or unable to be unzipped.
    """

    def __init__(self, file_path) -> None:
        self.message = file_path


class BadURLFilename(BaseError):
    """
    Raised when unable to get the filename from a url.
    """

    def __init__(self, message, url) -> None:
        self.message = message
        self.url = url
