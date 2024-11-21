from functools import wraps
import logging
from typing import Type, Union, Tuple, Callable
import sqlite3
import traceback

class ExceptionHandler:
    """异常处理装饰器类"""
    
    def __init__(
        self, 
        error_message: str = "操作失败", 
        return_value = None,
        log_level: int = logging.ERROR
    ):
        """
        Args:
            error_message: ValueError 的错误消息前缀
            return_value: 发生异常时的返回值
            log_level: 日志级别
        """
        self.error_message = error_message
        self.return_value = return_value
        self.log_level = log_level
    
    def __call__(self, func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ValueError as e:
                # ValueError 使用指定的错误消息前缀
                error_msg = f"{self.error_message}：{str(e)}"
                logging.log(self.log_level, error_msg)
                return self.return_value
            except Exception as e:
                # 其他异常显示原始错误信息和堆栈
                logging.log(self.log_level, f"发生异常：{str(e)}\n{traceback.format_exc()}")
                return self.return_value
        return wrapper

class DBExceptionHandler(ExceptionHandler):
    """数据库操作异常处理装饰器"""
    
    def __init__(
        self, 
        error_message: str = "数据库操作失败",
        return_value = None,
        auto_rollback: bool = True
    ):
        super().__init__(error_message=error_message, return_value=return_value)
        self.auto_rollback = auto_rollback
    
    def __call__(self, func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ValueError as e:
                # ValueError 使用指定的错误消息前缀
                error_msg = f"{self.error_message}：{str(e)}"
                logging.error(error_msg)
                if self.auto_rollback and args and hasattr(args[0], 'conn'):
                    try:
                        args[0].conn.rollback()
                    except:
                        pass
                return self.return_value
            except (sqlite3.Error, Exception) as e:
                # 其他异常显示原始错误信息和堆栈
                logging.error(f"数据库异常：{str(e)}\n{traceback.format_exc()}")
                if self.auto_rollback and args and hasattr(args[0], 'conn'):
                    try:
                        args[0].conn.rollback()
                    except:
                        pass
                return self.return_value
        return wrapper