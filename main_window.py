from PyQt6.QtWidgets import (QMainWindow, QWidget,QTreeWidget, QVBoxLayout, QPushButton,
                             QTabWidget,QTableWidget, QTableWidgetItem, QFileDialog, QComboBox,
                             QMessageBox, QHBoxLayout, QLabel, QProgressBar, 
                             QSplitter,QMenu, QFrame, QStatusBar, QSpacerItem, QSizePolicy,
                             QListWidget, QStackedWidget, QTextEdit, QTreeWidgetItem, QApplication,
                             QTableView)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont
from excel_processor import ExcelProcessor
from models.table_model import TableModel
import os
from widgets.run_button import RunButton
from widgets.log_panel import LogPanel
import logging
from datetime import datetime
from models.file_history import FileHistory
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from widgets.document_area import DocumentArea

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Excel数据管理器")
        self.setMinimumSize(1024, 768)

        # 设置无边框窗口
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 初始化数据库连接
        self.engine = create_engine('sqlite:///file_history.db')
        FileHistory.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.db_session = Session()

        
        # 设置中心部件
        self.setup_ui()
        
        # 加载文件历史记录（在UI设置完成后加载）
        self.load_file_history()
        
    def setup_ui(self):
        """设置UI界面"""
        self.create_title_bar()

        # 创建主布局容器
        main_container = QWidget()
        self.main_layout.addWidget(main_container)

        main_container_layout = QVBoxLayout(main_container)
        main_container_layout.setContentsMargins(0, 0, 0, 0)
        main_container_layout.setSpacing(0)

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_container_layout.addWidget(self.main_splitter)

        # 左侧导航区，包含文件树和脚本树
        left_panel = QWidget()
        left_panel.setMaximumWidth(400)
        left_panel.setMinimumWidth(200)
        left_panel_layout = QVBoxLayout(left_panel)
        left_panel_layout.setContentsMargins(0, 0, 0, 0)
        left_panel_layout.setSpacing(0)  

        self.left_panel_tab = QTabWidget()
        self.left_panel_tab.setDocumentMode(True)
        # 设置TabWidget的大小策略为扩展
        self.left_panel_tab.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # 将TabWidget添加到布局中，并设置拉伸因子
        left_panel_layout.addWidget(self.left_panel_tab, 1)
        # 修改样式表，确保标签页平均分配宽度
        self.left_panel_tab.setStyleSheet("""
        QTabWidget {
            background: #252526;
        }
        QTabWidget::pane {
            border: none;
            background: #252526;
        }
        QTabBar::tab {
            min-width: 50%;
            padding: 5px;
            background: #2d2d2d;
            color: #ffffff;
        }
        QTabBar::tab:selected {
            background: #1e1e1e;
            border-bottom: 2px solid #007acc;
            color: #ffffff;
        }
        QTabBar::tab:!selected {
            background: #2d2d2d;
            color: #ffffff;
        }
    """)

        tab_bar = self.left_panel_tab.tabBar()
        tab_bar.setExpanding(True)
        tab_bar.setDrawBase(False)
        tab_bar.setElideMode(Qt.TextElideMode.ElideNone)
        tab_bar.setUsesScrollButtons(False)

        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels(["文件名", "修改日期", "类型", "大小"])
        self.file_tree.setColumnWidth(0, 200)  # 文件名列宽
        self.file_tree.setColumnWidth(1, 150)  # 修改日期列宽
        self.file_tree.setColumnWidth(2, 80)   # 类型列宽
        self.file_tree.setColumnWidth(3, 100)  # 大小列宽

        # self.file_tree.setHeaderHidden(True)
        self.file_tree.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # 文件树的缩进设置为0
        self.file_tree.setIndentation(0)
        self.file_tree.setMouseTracking(True)
        self.file_tree.itemEntered.connect(self.show_file_path_tooltip)
        
        # 添加右键菜单
        self.file_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_tree.customContextMenuRequested.connect(self.show_file_tree_context_menu)

        # 设置文件树点击打开文件
        self.file_tree.itemClicked.connect(self.open_file_from_tree)
        
        self.file_tree.setStyleSheet("""
        QTreeWidget {
            background-color: #252526;
            border: none;
            color: #ffffff;
        }
        QTreeWidget::item {
            min-height: 25px;
            padding: 2px;
        }
        QTreeWidget::item:hover {
            background-color: #2a2a2a;
        }
        QTreeWidget::item:selected {
            background-color: #094771;
        }
    """)
        self.script_tree = QTreeWidget()
        self.script_tree.setHeaderHidden(True)
        self.script_tree.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.script_tree.setStyleSheet(self.file_tree.styleSheet())

        self.left_panel_tab.addTab(self.file_tree, "文件") 
        self.left_panel_tab.addTab(self.script_tree, "脚本")

        left_panel_layout.addWidget(self.left_panel_tab)
        self.main_splitter.addWidget(left_panel)

        self.right_splitter = QSplitter(Qt.Orientation.Vertical)

        center_splitter = QSplitter(Qt.Orientation.Horizontal)

        self.document_area = DocumentArea()

        center_splitter.addWidget(self.document_area)


        property_panel = QWidget()
        property_panel.setMinimumWidth(200)
        property_panel.setMaximumWidth(350)  # 设置最大宽度

        property_panel_layout = QVBoxLayout(property_panel)
        property_panel_layout.setContentsMargins(0, 0, 0, 0)
        
        self.property_stack = QStackedWidget()
        property_panel_layout.addWidget(self.property_stack)
        center_splitter.addWidget(property_panel)


        self.right_splitter.addWidget(center_splitter)

        self.bottom_panel = QWidget()
        self.bottom_panel.setMinimumHeight(100)
        self.bottom_panel_layout = QVBoxLayout(self.bottom_panel)
        self.bottom_panel_layout.setContentsMargins(0, 0, 0, 0)
        self.bottom_panel_layout.setSpacing(0)


        self.log_panel = LogPanel()
        self.log_panel.closed.connect(self.hide_bottom_panel)
        self.bottom_panel_layout.addWidget(self.log_panel)
        self.right_splitter.addWidget(self.bottom_panel)



        # 设置右侧分割器的初始大小比例
        self.right_splitter.setSizes([700, 250])  # 设置初始大小比例，上面区域700，下面区域100
        
        # 设置分割器的拉伸因子
        self.right_splitter.setStretchFactor(0, 1)  # 上面区域（文档区域）可以拉伸
        self.right_splitter.setStretchFactor(1, 0)  # 下面区域（日志面板）不自动拉伸


        self.main_splitter.addWidget(self.right_splitter)
    
      
        # 设置主分割器的属性
        self.main_splitter.setCollapsible(0, False)  # 禁止左侧面板完全折叠
        self.main_splitter.setSizes([200, 800])  # 设置左右区域的初始大小比例

        # 设置分割器的样式
        self.main_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #2d2d2d;
                width: 2px;
            }
            QSplitter::handle:hover {
                background-color: #007acc;
            }
        """)


    def closeEvent(self,event):
        """关闭事件"""
        if hasattr(self, 'log_panel'):
            self.log_panel.cleanup()
        event.accept()

    def hide_bottom_panel(self):
        """隐藏底部面板"""
        self.bottom_panel.hide()
        sizes = self.right_splitter.sizes()
        self.right_splitter.setSizes([sizes[0]+sizes[1],0])

    def create_title_bar(self):
        """创建标题栏"""
        title_bar = QWidget()
        title_bar.setFixedHeight(30)
        title_bar.setStyleSheet("""
            QWidget {
                background-color: #f3f3f3;
                border-bottom: 1px solid #e0e0e0;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 5px 10px; /* 增加水平内边距 */
                margin: 0 2px; /* 增加水平外边距 */
                color: #666666;
            }
            QPushButton::menu-indicator {
                width: 0px;  /* 隐藏菜单指示器 */
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton#close_button:hover {
                background-color: #e81123;
                color: white;
            }
            QMenu {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                padding: 5px 0px;
            }
            QMenu::item {
                padding: 5px 30px 5px 20px;
                color: #333333;
            }
            QMenu::item:selected {
                background-color: #e5f3ff;
                color: #000000;
            }
            QMenu::separator {
                height: 1px;
                background-color: #e0e0e0;
                margin: 5px 0px;
            }
        """)
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(5, 0, 0, 0)
        title_layout.setSpacing(0)
        
        # 添加图标
        icon_label = QLabel()
        # icon_label.setPixmap(QIcon("path/to/your/icon.png").pixmap(20, 20))
        icon_label.setFixedSize(30, 30)
        title_layout.addWidget(icon_label)
        
        # 添加菜单按钮
        menu_data = {
            "文件": [
                ("新建", "Ctrl+N"),
                ("打开", "Ctrl+O"),
                ("保存", "Ctrl+S"),
                ("另存为", "Ctrl+Shift+S"),
                None,  # 这里的 None 必须单独一行
                ("导入", "Ctrl+I"),
                ("导出", "Ctrl+E"),
                None,  # 这里的 None 必须单独一行
                ("退出", "Alt+F4")
            ],
            "编辑":[
                ("撤销","Ctrl+Z"),
                ("重做","Ctrl+Y"),
                None,
                ("剪切","Ctrl+X"),
                ("复制","Ctrl+C"),
                ("粘贴","Ctrl+V")
            ],
            "视图":[
                ("显示日志面板","Ctrl+J"),
                ("显示属性面板","Ctrl+P"),
                None,
                ("放大","Ctrl++"),
                ("缩小","Ctrl+-"),
                None,
                ("重置缩放","Ctrl+0")
            ],
            "帮助":[
                ("文档","F1"),
                ("检查更新","Ctrl+U"),
                None,
                ("关于","Ctrl+H")
            ]
        }
        for menu_name, menu_items in menu_data.items():
            menu_btn = QPushButton(menu_name)
            menu_btn.setFixedHeight(30)
            menu = QMenu(menu_btn)

            for item in menu_items:
                if item is None:
                    menu.addSeparator()
                else:
                    action_name,shortcut = item
                    action = menu.addAction(action_name)
                    if shortcut:
                        action.setShortcut(shortcut)
                    # 修复lambda函数的写法
                    action.triggered.connect(lambda checked, an=action_name: self.handle_menu_action(an))
           
            menu_btn.setMenu(menu)
            title_layout.addWidget(menu_btn)
        
        # 添加标题
        title_label = QLabel("Excel数据管理器")
        title_label.setStyleSheet("color: #666666;")
        title_layout.addWidget(title_label)
        
        # 添加弹簧
        title_layout.addStretch()
        
        # 添加设置按钮
        settings_btn = QPushButton("⚙")
        settings_btn.setFixedSize(45, 30)
        title_layout.addWidget(settings_btn)
        
        # 添加最小化按钮
        min_btn = QPushButton("─")
        min_btn.setFixedSize(45, 30)
        min_btn.clicked.connect(self.showMinimized)
        title_layout.addWidget(min_btn)
        
        # 添加最大化/还原按钮
        self.max_btn = QPushButton("□")
        self.max_btn.setFixedSize(45, 30)
        self.max_btn.clicked.connect(self.toggle_maximize)
        title_layout.addWidget(self.max_btn)
        
        # 添加关闭按钮
        close_btn = QPushButton("×")
        close_btn.setObjectName("close_button")
        close_btn.setFixedSize(45, 30)
        close_btn.clicked.connect(self.close)
        title_layout.addWidget(close_btn)
        
        self.main_layout.addWidget(title_bar)
        self.title_bar = title_bar


    def handle_menu_action(self, action_name):
        """处理菜单动作"""
        print(f"执行菜单动作: {action_name}")

        if action_name == "新建":
            pass
        elif action_name == "打开":
            self.open_file()
        elif action_name == "保存":
            pass
        elif action_name == "显示日志面板":
            self.show_bottom_panel()
        elif action_name == "显示属性面板":
            # self.show_property_panel()
            pass

    def show_bottom_panel(self):
        """显示底部面板"""
        self.bottom_panel.show()
        self.log_panel.show()
        # 调整分割器大小，给底部面板留出空间
        sizes = self.right_splitter.sizes()
        total = sum(sizes)
        self.right_splitter.setSizes([total - 200, 200])

    def hide_bottom_panel(self):
        """隐藏底部面板"""
        self.bottom_panel.hide()
        sizes = self.right_splitter.sizes()
        self.right_splitter.setSizes([sizes[0] + sizes[1], 0])
    

    def mousePressEvent(self, event):
        """处理鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 检查是否在标题栏区域
            if self.title_bar.geometry().contains(event.pos()):
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
    
    def mouseMoveEvent(self, event):
        """处理鼠标移动事件"""
        if hasattr(self, 'drag_position'):
            if event.buttons() & Qt.MouseButton.LeftButton:
                self.move(event.globalPosition().toPoint() - self.drag_position)
                event.accept()
    
    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件"""
        if hasattr(self, 'drag_position'):
            delattr(self, 'drag_position')
    
    def toggle_maximize(self):
        """切换最大化/还原状态"""
        if self.isMaximized():
            self.showNormal()
            self.max_btn.setText("□")
        else:
            self.showMaximized()
            self.max_btn.setText("❐")


    def toggle_header_style(self):
        """切换列名显示方式"""
        self.use_excel_style = not self.use_excel_style
        self.header_style_button.setText("使用Excel列名" if not self.use_excel_style else "使用文档列名")
        
        # 如果当前有数据，更新表头显示
        if self.sheet_selector.currentText():
            self.load_sheet_data(self.sheet_selector.currentText())

    def on_run_button_state_changed(self, is_running: bool):
        """处理运行按钮状态改变"""
        if is_running:
            print("开始运行")
            # 在这里添加运行时的逻辑
        else:
            print("暂停运行")
            # 在这里添加暂停时的逻辑

    def on_log_panel_closed(self):
        """处理日志面板关闭事件"""
        # 可以添加重新显示日志面板的方法，比如添加一个菜单项或工具栏按钮
        pass

    def show_log_panel(self):
        """显示日志面板"""
        self.log_panel.show()

    def on_log_search(self, text):
        """处理日志搜索"""
        # 在这里可以添加额外的搜索逻辑
        pass

      # 修改原来使用 log_area 的地方，改为使用 log_panel
    def log_message(self, message):
        """添加日志消息"""
        self.log_panel.append_log(message)


    def update_progress(self, value: int):
        """更新进度条"""
        self.progress_bar.setValue(value)

    def handle_error(self, error_msg: str):
        """处理错误"""
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "错误", error_msg)

    def update_table(self, headers: tuple, data: list):
        """更新表格数据"""
        if  hasattr(self,'table_model') and self.table_model._current_sheet:
            self.table_model.setData(
                self.table_model._current_sheet,
                headers,
                data
            )

            if hasattr(self,'table'):
                self.table.resizeColumnsToContents()
        else:
            logging.error("表格数据更新失败，没有当前工作表")

    def save_file_history(self, file_path: str):
        """保存文件历史到数据库"""
        try:
            file_info = os.stat(file_path)
            file_name = os.path.basename(file_path)
            file_type = os.path.splitext(file_name)[1]
            
            # 检查文件是否已存在
            existing_record = self.db_session.query(FileHistory).filter_by(file_path=file_path).first()
            
            if existing_record:
                # 更新现有记录
                existing_record.file_name = file_name
                existing_record.file_type = file_type
                existing_record.file_size = file_info.st_size
                existing_record.modified_date = datetime.fromtimestamp(file_info.st_mtime)
                logging.info(f"更新文件历史记录: {file_path}")
            else:
                # 创建新的文件历史记录
                file_history = FileHistory(
                    file_name=file_name,
                    file_path=file_path,
                    file_type=file_type,
                    file_size=file_info.st_size,
                    modified_date=datetime.fromtimestamp(file_info.st_mtime)
                )
                self.db_session.add(file_history)
                logging.info(f"添加新的文件历史记录: {file_path}")
            
            # 保存到数据库
            self.db_session.commit()
            
            # 更新文件树显示
            self.update_file_tree()
            
        except Exception as e:
            logging.error(f"保存文件历史时出错: {str(e)}")
            self.db_session.rollback()
    
    def open_file_from_tree(self, item):
        """从文件树打开文件"""
        try:
            # 获取存储在item中的文件路径
            file_path = item.data(0, Qt.ItemDataRole.UserRole)
            
            if not os.path.exists(file_path):
                QMessageBox.warning(self, "文件不存在", 
                                f"文件 {file_path} 已不存在。\n将从历史记录中移除。")
                # 从树中移除该项
                parent = item.parent()
                if parent:
                    parent.removeChild(item)
                else:
                    self.file_tree.takeTopLevelItem(
                        self.file_tree.indexOfTopLevelItem(item))
                return
                
            # 直接调用文件处理方法，但不更新历史记录
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension in ['.xlsx', '.xls']:
                self.open_excel_file(file_path, update_history=False)
            elif file_extension in ['.txt', '.md', '.py', '.json', '.xml', '.yaml', '.yml']:
                self.open_text_file(file_path, update_history=False)
            else:
                QMessageBox.warning(self, "警告", f"不支持的文件类型: {file_extension}")
                return
            
        except Exception as e:
            error_msg = f"打开文件时出错: {str(e)}"
            logging.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)

    def update_file_tree(self):
        """更新文件树显示"""
        try:
            # 获取所有文件历史记录
            file_histories = self.db_session.query(FileHistory).order_by(FileHistory.created_at.desc()).all()
            
            # 清空现有项
            self.file_tree.clear()
            
            # 添加文件历史到树形控件
            for history in file_histories:
                item = QTreeWidgetItem(self.file_tree)
                item.setText(0, history.file_name)  # 文件名
                item.setText(1, history.modified_date.strftime("%Y-%m-%d %H:%M:%S"))  # 修改日期
                item.setText(2, history.file_type)  # 文件类型
                item.setText(3, f"{history.file_size / 1024:.2f} KB")  # 文件大小
                item.setData(0, Qt.ItemDataRole.UserRole, history.file_path)  # 将路径存储在数据中
                item.setToolTip(0, history.file_path)  # 设置悬浮提示显示完整路径
                
        except Exception as e:
            logging.error(f"更新文件树时出错: {str(e)}")

    def open_file(self):
        """打开文件对话框"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "打开文件",
                "",
                "Excel文件 (*.*)"
            )
            
            if file_path:
                file_extension = os.path.splitext(file_path)[1].lower()

                if file_extension in ['.xlsx','.xls']:
                    self.open_excel_file(file_path)
                # 这里可以添加其他文件类型的处理
                elif  file_extension in ['.txt', '.md', '.py', '.json', '.xml', '.yaml', '.yml']:
                    self.open_text_file(file_path)
                else:
                    QMessageBox.warning(self, "警告", f"不支持的文件类型: {file_extension}")
            
                self.save_file_history(file_path)
    
        except Exception as e:
            error_msg = f"打开文件对话框时出错: {str(e)}"
            logging.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)


    def open_text_file(self, file_path: str, update_history: bool = True):
        """打开文本文件"""
        try:
            doc_tab = self.document_area.open_document(file_path, "text")
            text_edit = doc_tab.setup_text_view()
            
            # 尝试不同的编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin1']
            content = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    logging.info(f"成功使用 {encoding} 编码打开文件")
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                raise ValueError("无法以任何支持的编码格式读取文件")
                
            text_edit.setText(content)
            
            # 只在需要时更新历史记录
            if update_history:
                self.update_file_history(file_path)
                
            logging.info(f"成功打开文本文件: {file_path}")
            
        except Exception as e:
            error_msg = f"打开文本文件时出错: {str(e)}"
            logging.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
            
            # 如果已经创建了标签页，需要关闭它
            if 'doc_tab' in locals():
                index = self.document_area.tab_widget.indexOf(doc_tab)
                if index != -1:
                    self.document_area.close_tab(index)
            

    def open_excel_file(self, file_path: str, update_history: bool = True):
        """打开Excel文件并显示数据"""
        try:
            # 打开文档
            self.document_area.open_document(file_path, '.xlsx')
            
            # 更新文件历史
            if update_history:
                self.update_file_history(file_path)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开Excel文件失败：{str(e)}")
            logging.error(f"打开Excel文件失败：{str(e)}")


    def show_file_path_tooltip(self, item: QTreeWidgetItem, column: int):
        """显示文件路径工具提示"""
        file_path = item.data(0, Qt.ItemDataRole.UserRole)  # 获取路径列的文本
        item.setToolTip(column, file_path)  # 为当前列设置工具提示
        
    def show_file_tree_context_menu(self, position):
        """显示文件树的右键菜单"""
        item = self.file_tree.itemAt(position)
        if item is None:
            return
            
        menu = QMenu()
        copy_action = menu.addAction("复制文件路径")
        
        # 获取全局坐标
        global_pos = self.file_tree.viewport().mapToGlobal(position)
        
        # 显示菜单并获取选中的动作
        action = menu.exec(global_pos)
        
        if action == copy_action:
            file_path = item.data(0, Qt.ItemDataRole.UserRole)  # 获取路径列的文本
            clipboard = QApplication.clipboard()
            clipboard.setText(file_path)
            logging.info(f"已复制文件路径: {file_path}")

    def load_file_history(self):
        """初始化时加载文件历史记录"""
        try:
            # 获取所有文件历史记录
            file_histories = self.db_session.query(FileHistory).all()
            
            # 用于存储有效的文件历史记录
            valid_histories = []
            
            # 验证文件是否仍然存在
            for history in file_histories:
                if os.path.exists(history.file_path):
                    valid_histories.append(history)
                else:
                    # 如果文件不存在，从数据库中删除记录
                    self.db_session.delete(history)
            
            # 提交更改
            self.db_session.commit()
            
            # 添加有效的文件历史到树形控件
            for history in valid_histories:
                item = QTreeWidgetItem(self.file_tree)
                item.setText(0, history.file_name)  # 文件名
                item.setText(1, history.modified_date.strftime("%Y-%m-%d %H:%M:%S"))  # 修改日期
                item.setText(2, history.file_type)  # 文件类型
                item.setText(3, f"{history.file_size / 1024:.2f} KB")  # 文件大小
                item.setData(0, Qt.ItemDataRole.UserRole, history.file_path)  # 将路径存储在数据中
                item.setToolTip(0, history.file_path)  # 设置悬浮提示显示完整路径
                
            logging.info("文件历史记录加载完成")
                
        except Exception as e:
            logging.error(f"加载文件历史记录时出错: {str(e)}")

    def update_file_history(self, file_path: str):
        """更新文件历史记录"""
        try:
            # 检查文件是否已经在历史记录中
            existing_record = self.db_session.query(FileHistory).filter_by(
                file_path=file_path).first()
            
            if existing_record:
                # 更新现有记录的修改时间
                existing_record.modified_time = datetime.now()
            else:
                # 创建新的历史记录
                new_record = FileHistory(
                    file_path=file_path,
                    modified_time=datetime.now()
                )
                self.db_session.add(new_record)
            
            # 提交更改
            self.db_session.commit()
            
            # 更新文件树显示
            self.update_file_tree()
            
            logging.info(f"添加新的文件历史记录: {file_path}")
            
        except Exception as e:
            logging.error(f"更新文件历史记录失败: {str(e)}")
            # 回滚事务
            self.db_session.rollback()
