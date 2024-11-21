from PyQt6.QtCore import Qt, QAbstractTableModel

class TableModel(QAbstractTableModel):
    """
    表格数据模型
    用于管理表格的数据和表头，继承自QAbstractTableModel
    """
    def __init__(self, data=None, headers=None):
        """
        初始化表格模型
        :param data: 二维列表，表格数据
        :param headers: 列表，表头数据
        """
        super().__init__()
        self._data = data if data is not None else []
        self._headers = headers if headers is not None else []

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        """
        获取单元格数据
        :param index: 单元格索引
        :param role: 数据角色
        :return: 单元格数据
        """
        if not index.isValid():
            return None
            
        if role == Qt.ItemDataRole.DisplayRole:
            return self._data[index.row()][index.column()]
            
        return None

    def rowCount(self, parent=None):
        """
        获取行数
        :return: 表格的总行数
        """
        return len(self._data)

    def columnCount(self, parent=None):
        """
        获取列数
        :return: 表格的总列数（使用表头长度或第一行数据的长度）
        """
        return len(self._headers) if self._headers else (len(self._data[0]) if self._data else 0)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        """
        获取表头数据
        :param section: 行号或列号
        :param orientation: 方向（水平或垂直）
        :param role: 数据角色
        :return: 表头文本
        """
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                # 返回水平表头（列表头）
                return self._headers[section] if section < len(self._headers) else str(section)
            else:
                # 返回垂直表头（行号）
                return str(section + 1)
        return None

    def flags(self, index):
        """
        获取单元格标志
        :return: 单元格的标志（可选中、可使用）
        """
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
