class AuthError(Exception):
    def __init__(self, message, *, field=None, status=400, code="invalid"):
        super().__init__(message)
        self.message = message
        self.field = field
        self.status = status
        self.code = code
