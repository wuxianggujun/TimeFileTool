from PyQt6.QtWidgets import QPushButton,QToolTip
from PyQt6.QtGui import QPainter, QColor, QPen,QFont
from PyQt6.QtCore import QPoint, pyqtSignal, Qt,QRect

class RunButton(QPushButton):
    # 自定义信号，用于通知状态改变
    state_changed = pyqtSignal(bool)  # True 表示运行状态，False 表示暂停状态
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # 初始化属性
        self.setFixedSize(40, 40)
        self.is_running = True  # True 表示显示绿色（运行状态），False 表示显示红色（暂停状态）
        
        # 设置颜色 - 直接使用字符串创建 QColor
        self.run_color = QColor("#4CAF50")    # 绿色
        self.pause_color = QColor("#FF0000")   # 红色
        
        # 设置按钮属性
        self.setFlat(True)  # 设置为平面按钮
        self.setCursor(Qt.CursorShape.PointingHandCursor)  # 设置鼠标悬停时的光标
        
        self.setToolTip("点击切换运行/暂停状态")
        tooltip_font = QFont()
        tooltip_font.setPointSize(10)  # 设置字体大小
        QToolTip.setFont(tooltip_font)

        # 连接点击信号
        self.clicked.connect(self.toggle_state)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 获取按钮中心点并转换为整数
        center_x = int(self.width() / 2)
        center_y = int(self.height() / 2)
        
        # 设置当前颜色
        color = self.run_color if self.is_running else self.pause_color
        painter.setBrush(color)
        painter.setPen(QPen(color))
        
        if self.is_running:
            # 绘制三角形（运行状态）
            points = [
                QPoint(int(center_x - 8), int(center_y - 8)),   # 左上角
                QPoint(int(center_x - 8), int(center_y + 8)),   # 左下角
                QPoint(int(center_x + 8), int(center_y))        # 右中点
            ]
            painter.drawPolygon(points)
        else:
            # 绘制暂停符号（两个竖条）
            rect1 = QRect(center_x - 8, center_y - 8, 5, 16)
            rect2 = QRect(center_x + 3, center_y - 8, 5, 16)
            painter.drawRect(rect1)
            painter.drawRect(rect2)
    
    def toggle_state(self):
        """切换按钮状态"""
        self.is_running = not self.is_running
        # 更新工具提示文本
        self.setToolTip("运行" if self.is_running else "暂停")
        self.state_changed.emit(self.is_running)
        self.update()
    
    def set_state(self, is_running: bool):
        """设置按钮状态"""
        if self.is_running != is_running:
            self.is_running = is_running
            self.setToolTip("运行" if self.is_running else "暂停")
            self.state_changed.emit(self.is_running)
            self.update()
    
    def set_colors(self, run_color: str, pause_color: str):
        """设置按钮颜色"""
        self.run_color = QColor(run_color)
        self.pause_color = QColor(pause_color)
        self.update()

    def enterEvent(self, event):
        """鼠标进入事件"""
        QToolTip.showText(self.mapToGlobal(self.rect().bottomLeft()), 
                         "运行" if self.is_running else "暂停")
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开事件"""
        QToolTip.hideText()
        super().leaveEvent(event)