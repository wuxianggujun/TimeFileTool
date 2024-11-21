import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt
from widgets.table_view import MergedTableView
from widgets.table_model import TableModel
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Merged Cell Test")
        self.resize(600, 400)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 创建表格视图
        self.table_view = MergedTableView()
        layout.addWidget(self.table_view)
        
        # 创建数据模型
        headers = ["Column 1", "Column 2", "Column 3", "Column 4", "Column 5"]
        data = [
            ["Row 1", "Merged Cells Content", "", "", ""],
            ["Row 2", "Normal Cell", "Merged", "Cells", "Here"],
            ["Row 3", "Another Cell", "", "", "Last"]
        ]
        model = TableModel(data, headers)
        self.table_view.setModel(model)
        
        # 设置合并单元格
        merged_cells = [
            ((0, 1), (0, 4)),  # 第一行的2-5列合并
            ((1, 2), (1, 4))   # 第二行的3-5列合并
        ]
        self.table_view.setMergedCells(merged_cells)

def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    app.exec()

if __name__ == "__main__":
    main()
