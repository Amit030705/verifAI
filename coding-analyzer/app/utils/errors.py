class PlatformServiceError(Exception):
    def __init__(self, platform: str, message: str, status_code: int = 500) -> None:
        super().__init__(message)
        self.platform = platform
        self.message = message
        self.status_code = status_code
