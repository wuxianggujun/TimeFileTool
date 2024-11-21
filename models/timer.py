from time import perf_counter
from typing import Optional, Callable
import logging
from functools import wraps

class PerformanceTimer:
    """性能计时器类"""
    
    def __init__(self, name: Optional[str] = None):
        self.name = name
        self.start_time: float = 0
        self.end_time: float = 0
        
    def start(self) -> None:
        """开始计时"""
        self.start_time = perf_counter()
        
    def stop(self) -> float:
        """停止计时并返回执行时间"""
        self.end_time = perf_counter()
        return self.duration
        
    @property
    def duration(self) -> float:
        """获取执行时间（秒）"""
        return self.end_time - self.start_time
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop()
        if self.name:
            self._log_performance()
            
    def _log_performance(self):
        """记录性能日志"""
        logging.info(f"{self.name} - 执行耗时: {self.duration:.4f} 秒")
    
    @staticmethod
    def timer(name: Optional[str] = None) -> Callable:
        """计时器装饰器
        
        Args:
            name: 自定义的方法名称，如果不提供则使用方法原名
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                method_name = name or func.__name__
                with PerformanceTimer(method_name):
                    return func(*args, **kwargs)
            return wrapper
        # 支持直接使用@PerformanceTimer.timer方式
        if callable(name):
            func, name = name, None
            return decorator(func)
        return decorator