class ServiceError(Exception):
    """Lỗi nghiệp vụ có mã HTTP. main.py đổi nó thành JSON {"detail": message}."""

    def __init__(self, status, message):
        super().__init__(message)
        self.status, self.message = status, message
