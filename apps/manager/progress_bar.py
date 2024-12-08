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

    def reset_progress(self, num_of_task = 0) : 
        self.progress = 0
        self.num_of_task = num_of_task
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
    
    def append_log(self, log_msg : str) :
        self.now_log += f'{log_msg}\n'
        
    def append_progress(self, log_msg = '', progress = 0) :
        if progress != 0 :
            self.progress += progress
        if len(log_msg) > 0 :
            self.now_log += log_msg + '\n'
    
    def get_progress(self) :
        return round(self.progress,2)
    
    def progress_end(self) :
        self.reset_progress()
        self.show = False
    
    def isShow(self) :
        return self.show
    
    def status_bundle(self, flush_log=False) :
        return_dict = {'progress' : self.get_progress(), 'message' : self.get_now_log(), 'show' : self.show}
        if flush_log :
            self.now_log = ''
        return return_dict
        

    @classmethod
    def get_instance(cls):
        return cls()