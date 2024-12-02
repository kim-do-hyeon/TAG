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
            self.progress = 0
            self.num_of_task = 0
            self.now_task = 0
            self.now_log = ''
            self.show = False

    def reset_progress(self) : 
        self.progress = 0
        self.num_of_task = 0
        self.now_task = 0
        self.now_log = ''

    def start_progress(self, num_of_task = 0) :
        self.progress = 0
        self.num_of_task = num_of_task
        self.now_task = 0
        self.show = True
    
    def done_1_task(self) :
        if self.num_of_task > 0 :
            self.now_task += 1
            self.progress = round((self.now_task / self.num_of_task) * 100, 2)
    
    def set_now_log(self, log) :
        self.now_log = log
    
    def set_progress(self, progress) :
        self.progress = progress
    
    def get_now_log(self) :
        return self.now_log
    
    def get_progress(self) :
        return round(self.progress,2)
    
    def progress_end(self) :
        self.reset_progress()
        self.show = False
    
    def isShow(self) :
        return self.show
        

    @classmethod
    def get_instance(cls):
        return cls()