class ServiceError(Exception):
    """Lỗi nghiệp vụ có mã HTTP. main.py đổi nó thành JSON {"detail": message}.
    retry_after (giây, tùy chọn) -> header Retry-After để frontend biết khi nào thử lại."""

    def __init__(self, status, message, retry_after=None):
        super().__init__(message)
        self.status, self.message, self.retry_after = status, message, retry_after
