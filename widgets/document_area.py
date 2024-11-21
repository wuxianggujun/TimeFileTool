from PyQt6.QtWidgets import (QWidget, QTabWidget, QStackedWidget, 
                           QVBoxLayout, QTextEdit)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QSizePolicy
from models.table_model import TableModel
from excel_processor import ExcelProcessor
from models.decorators import ExceptionHandler
from widgets.table_view import MergedTableView
import numpy as np
import logging

class DocumentTab(QWidget):
    """单个文档标签页的容器"""
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)  # 减少空隙

        # 创建堆叠部件来容纳不同类型的视图
        self.stack = QStackedWidget()
        self.layout.addWidget(self.stack)
        
        self.sheet_tabs = QTabWidget()
        self.sheet_tabs.setMaximumHeight(25)
        self.sheet_tabs.setTabPosition(QTabWidget.TabPosition.South)
        self.layout.addWidget(self.sheet_tabs)

        # 初始化各种视图但暂不显示
        self.table_view = None
        self.text_edit = None
        self.table_model = None
        self.excel_processor = None

    def change_sheet(self, index):
        """切换表格视图的sheet"""
        if index >= 0 and self.excel_processor:
            try:
                # 读取数据和合并单元格信息
                data, merged_cells = self.excel_processor.read_sheet_data(index)
                if data:  # 确保有数据
                    # 设置数据
                    self.table_model.setData(data, merged_cells)

                    # 设置新的合并单元格信息
                    if merged_cells:
                        #for (start_row, start_col), (end_row, end_col) in merged_cells:
                            
                        self.table_view.setMergedCells(merged_cells)
                    else:
                        logging.info("没有合并单元格需要处理")
                        
                    # 调整列宽以适应内容
                    self.table_view.resizeColumnsToContents()
                    self.table_view.resizeRowsToContents()
            except Exception as e:
                logging.error(f"切换sheet时出错: {str(e)}")
    
    def move_sheet_tabs(self, show_at_top: bool):
        """移动sheet标签页到顶部或底部"""
        # 先从布局中移除
        self.layout.removeWidget(self.sheet_tabs)
        
        if show_at_top:
            # 插入到顶部（索引0的位置）
            self.layout.insertWidget(0, self.sheet_tabs)
            # 更改标签位置到顶部
            self.sheet_tabs.setTabPosition(QTabWidget.TabPosition.North)
        else:
            # 添加到底部
            self.layout.addWidget(self.sheet_tabs)
            # 更改标签位置到底部
            self.sheet_tabs.setTabPosition(QTabWidget.TabPosition.South)

    
    def setup_text_view(self):
        """设置文本编辑视图"""
        if not self.text_edit:
            self.text_edit = QTextEdit()
            self.text_edit.setReadOnly(False)  # 允许编辑
            self.text_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)  # 不自动换行
            
            # 设置文本编辑器的样式
            self.text_edit.setStyleSheet("""
                QTextEdit {
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                    border: none;
                    font-family: Consolas, 'Courier New', monospace;
                    font-size: 12px;
                }
            """)
            
            self.stack.addWidget(self.text_edit)
            
            # 隐藏sheet标签页，因为文本文件不需要
            self.sheet_tabs.hide()
            
        self.stack.setCurrentWidget(self.text_edit)
        return self.text_edit
    
    @ExceptionHandler(error_message="设置Excel表格视图失败", return_value=None)
    def setup_excel_view(self):
        """设置Excel表格视图"""
        if not self.table_view:
            self.table_view = MergedTableView(self)
            self.table_model = TableModel()
            
            self.table_view.setModel(self.table_model)
            self.table_view.setAlternatingRowColors(True)
            
            # 优化表格显示
            self.table_view.horizontalHeader().setStretchLastSection(True)
            self.table_view.verticalHeader().setDefaultSectionSize(25)
            self.table_view.horizontalHeader().setDefaultSectionSize(100)

            # 设置选择模式为单元格选择
            self.table_view.setSelectionMode(self.table_view.SelectionMode.ExtendedSelection)
            self.table_view.setSelectionBehavior(self.table_view.SelectionBehavior.SelectItems)

            self.stack.addWidget(self.table_view)
            
            # 初始化Excel处理器
            self.excel_processor = ExcelProcessor()
            sheets_info = self.excel_processor.read_excel_structure(self.file_path)
            
            # 清空现有的标签页
            self.sheet_tabs.clear()
            
            # 为每个sheet创建标签页
            for sheet_info in sheets_info:
                # 创建一个空的widget作为标签页的内容
                sheet_widget = QWidget()
                self.sheet_tabs.addTab(sheet_widget, sheet_info.sheet_name)
            
            # 如果有sheet，加载第一个sheet的数据
            if sheets_info:
                data, merged_cells = self.excel_processor.read_sheet_data(0)
                if data:  # 确保有数据
                    self.table_model.setData(data)
                    # 处理合并单元格
                    if merged_cells:
                        self.table_view.setMergedCells(merged_cells)
                self.sheet_tabs.setCurrentIndex(0)
            
            # 显示sheet标签页
            self.sheet_tabs.show()
            
            # 连接sheet切换信号
            self.sheet_tabs.currentChanged.connect(self.change_sheet)
            
        self.stack.setCurrentWidget(self.table_view)
        return self.table_view

class DocumentArea(QWidget):
    """文档区域组件，管理多个文档标签页"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)  # 减少空隙
        
        # 创建标签页管理器
        self.tab_widget = QTabWidget()
        self.tab_widget.setSizePolicy(QSizePolicy.Policy.Expanding, 
                                    QSizePolicy.Policy.Expanding)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.layout.addWidget(self.tab_widget)
        
        # 设置 DocumentArea 自身的大小策略
        self.setSizePolicy(QSizePolicy.Policy.Expanding, 
                          QSizePolicy.Policy.Expanding)
        
        # 存储打开的文档
        self.documents = {}  # {file_path: DocumentTab}
    
    def open_document(self, file_path: str, file_type: str):
        """打开新文档或切换到已存在的文档"""
        # 如果文档已经打开，切换到对应标签
        if file_path in self.documents:
            index = self.tab_widget.indexOf(self.documents[file_path])
            self.tab_widget.setCurrentIndex(index)
            return self.documents[file_path]
        
        # 创建新的文档标签
        doc_tab = DocumentTab(file_path)
        self.documents[file_path] = doc_tab
        
        # 添加到标签页
        file_name = file_path.split('/')[-1]
        self.tab_widget.addTab(doc_tab, file_name)
        self.tab_widget.setCurrentWidget(doc_tab)
        
        # 根据文件类型设置不同的视图
        if file_type.lower() in ['.xlsx', '.xls']:
            return doc_tab.setup_excel_view()
        else:
            return doc_tab.setup_text_view()
    
    def close_tab(self, index):
        """关闭指定的标签页"""
        widget = self.tab_widget.widget(index)
        file_path = next((path for path, tab in self.documents.items() if tab == widget), None)
        if file_path:
            del self.documents[file_path]
        self.tab_widget.removeTab(index)