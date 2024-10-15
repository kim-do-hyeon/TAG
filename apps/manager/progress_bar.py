import threading

class ProgressBar:
    _instance = None
    _lock = threading.Lock()  # 스레드 안전성을 위한 락

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:  # 스레드 안전성을 보장하기 위해 락 사용
                if not cls._instance:  # 이중 검사를 통해 인스턴스 생성
                    cls._instance = super(ProgressBar, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):  # 초기화 방지
            self._initialized = True

    @classmethod
    def get_instance(cls):
        return cls()