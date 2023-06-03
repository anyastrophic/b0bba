class HttpException(Exception):
    def __init__(self, message="default error", status: int = 0):
        self.message = message
        self.status = status
        super().__init__(self.message)
