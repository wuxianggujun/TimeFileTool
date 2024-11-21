from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                           QPushButton, QLineEdit, QLabel, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QObject
from PyQt6.QtGui import QColor, QPalette, QTextCursor, QMouseEvent
import sys
import logging

class QTextEditLogger(logging.Handler,QObject):
    """自定义日志处理器，将日志输出重定向到QTextEdit"""
    append_signal = pyqtSignal(str)

    def __init__(self,text_edit):
        super().__init__()
        QObject.__init__(self)
        self.text_edit = text_edit
        self.append_signal.connect(self.text_edit.append)
        self._is_valid = True

        # 设置日志格式
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        self.setFormatter(formatter)

    def emit(self,record):
        """处理日志记录"""
        if self._is_valid and self.text_edit:
            msg = self.format(record)
            self.append_signal.emit(msg)

    def cleanup(self):
        """清理资源"""
        self._is_valid = False
        if hasattr(self, 'append_signal'):
            try:
                self.append_signal.disconnect()
            except:
                pass
        self.text_edit = None


class PrintRedirector(QObject):
    """重定向print"""
    print_signal = pyqtSignal(str)

    def __init__(self,text_edit):
        super().__init__()
        self.text_edit = text_edit
        self.print_signal.connect(self.text_edit.append)

    def write(self,text):
        if text.strip(): # 如果文本不为空，则发出信号
            self.print_signal.emit(text)
        
    def flush(self):
        pass


class LogPanel(QWidget):
    search_text_changed = pyqtSignal(str)
    closed = pyqtSignal()  # 新增关闭信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_logger()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建顶部工具栏
        toolbar = QWidget()
        toolbar.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                border-top: 1px solid #e0e0e0;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(5, 2, 5, 2)
        
        # 添加"输出"标签
        output_label = QLabel("输出")
        output_label.setStyleSheet("color: #333333; font-weight: bold;")
        toolbar_layout.addWidget(output_label)
        
        # 添加搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索日志...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 1px solid #cccccc;
                border-radius: 2px;
                padding: 2px 5px;
                max-width: 200px;
            }
            QLineEdit:focus {
                border: 1px solid #0078d7;
            }
        """)
        self.search_input.textChanged.connect(self.on_search_text_changed)
        toolbar_layout.addWidget(self.search_input)
        
        # 添加弹簧
        toolbar_layout.addStretch()
        
        # 添加清除按钮
        self.clear_button = QPushButton("清除")
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #666666;
                padding: 2px 8px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.clear_button.clicked.connect(self.clear_log)
        toolbar_layout.addWidget(self.clear_button)
        
        # 添加关闭按钮
        self.close_button = QPushButton("×")
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #666666;
                padding: 2px 8px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                color: #333333;
            }
        """)
        self.close_button.clicked.connect(self.close_panel)
        toolbar_layout.addWidget(self.close_button)
        
        # 添加工具栏到主布局
        main_layout.addWidget(toolbar)
        
        # 创建日志文本区域
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("""
            QTextEdit {
                background-color: white;
                color: #333333;
                border: none;
                border-top: 1px solid #e0e0e0;
                font-family: Consolas, 'Courier New', monospace;
            }
        """)
        main_layout.addWidget(self.log_area)

    def setup_logger(self):
        """设置日志记录器"""
        self.logger_handler = QTextEditLogger(self.log_area)

        logging.getLogger().addHandler(self.logger_handler)
        logging.getLogger().setLevel(logging.INFO)

        self.stdout_redirector = PrintRedirector(self.log_area)
        self.stderr_redirector = PrintRedirector(self.log_area)

        sys.stdout = self.stdout_redirector
        sys.stderr = self.stderr_redirector


    def cleanup(self):
        """清理"""
        if hasattr(self, 'logger_handler'):
            self.logger_handler.cleanup()
            logging.getLogger().removeHandler(self.logger_handler)
            self.logger_handler = None

        if hasattr(self, 'stdout_redirector'):
            sys.stdout = sys.__stdout__
            self.stdout_redirector = None

        if hasattr(self, 'stderr_redirector'):
            sys.stderr = sys.__stderr__
            self.stderr_redirector = None


    def closeEvent(self,event):
        """关闭事件"""
        self.cleanup()
        super().closeEvent(event)

    def close_panel(self):
        """关闭面板"""
        self.hide()
        self.closed.emit()
        
    def on_search_text_changed(self, text):
        """处理搜索文本变化"""
        self.search_text_changed.emit(text)
        self.highlight_search_text(text)
    
    def highlight_search_text(self, text):
        """高亮搜索文本"""
        if not text:
            # 清除所有高亮
            cursor = self.log_area.textCursor()
            cursor.select(QTextCursor.SelectionType.Document)
            format = cursor.charFormat()
            format.setBackground(QColor("white"))
            cursor.mergeCharFormat(format)
            return
            
        # 设置高亮颜色
        highlight_color = QColor("#cce8ff")  # 浅蓝色背景
        
        # 保存当前滚动位置
        scrollbar = self.log_area.verticalScrollBar()
        scroll_pos = scrollbar.value()
        
        # 开始搜索和高亮
        cursor = self.log_area.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        
        # 清除之前的高亮
        cursor.select(QTextCursor.SelectionType.Document)
        format = cursor.charFormat()
        format.setBackground(QColor("white"))
        cursor.mergeCharFormat(format)
        cursor.clearSelection()
        
        # 高亮新的匹配项
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        while True:
            cursor = self.log_area.document().find(text, cursor)
            if cursor.isNull():
                break
            format = cursor.charFormat()
            format.setBackground(highlight_color)
            cursor.mergeCharFormat(format)
        
        # 恢复滚动位置
        scrollbar.setValue(scroll_pos)
    
    def append_log(self, text):
        """添加日志文本"""
        self.log_area.append(text)
        
    def clear_log(self):
        """清空日志"""
        self.log_area.clear()