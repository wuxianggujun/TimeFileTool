from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, pyqtSignal
from string import ascii_uppercase
import numpy as np
import logging

class TableModel(QAbstractTableModel):

    def __init__(self):
        super().__init__()
        self._data = []  # 存储所有行数据
        self._merged_cells = []  # 存储合并单元格信息
    
    def rowCount(self, parent=QModelIndex()):
        return len(self._data)
    
    def columnCount(self, parent=QModelIndex()):
        return len(self._data[0]) if self._data else 0
    
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        
        if role == Qt.ItemDataRole.DisplayRole:
            return self._data[index.row()][index.column()]  
        return None

    def _get_excel_column_name(self, column_number: int) -> str:
        """生成Excel风格的列名（A, B, C, ..., Z, AA, AB, ...）"""
        result = ""
        while column_number >= 0:
            result = ascii_uppercase[column_number % 26] + result
            column_number = column_number // 26 - 1
        return result

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        """
        Args:
            section: 行号或列号（从0开始）
            orientation: Qt.Orientation.Horizontal 或 Qt.Orientation.Vertical
            role: 数据角色，通常是 DisplayRole
        """
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                # 使用Excel风格的列名（A, B, C, ...）
                return self._get_excel_column_name(section)
            else:
                return str(section + 1)
        return None
        
    def flags(self, index):
        """
        获取单元格标志
        :return: 单元格的标志（可选中、可使用）
        """
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def setData(self, data, merged_cells=None):
        """设置表格数据和合并单元格信息"""
        self.beginResetModel()
        self._data = data
        if merged_cells is not None:
            self._merged_cells = merged_cells
            logging.info(f"TableModel设置合并单元格: {merged_cells}")
        self.endResetModel()
        return True
