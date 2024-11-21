from PyQt6.QtWidgets import QTableView, QStyledItemDelegate, QStyle, QStyleOptionViewItem, QAbstractItemView
from PyQt6.QtCore import Qt, QRect, QModelIndex, pyqtSignal
from PyQt6.QtGui import QPainter, QPen
import logging

class MergedCellTableModel:
    """
    合并单元格的数据模型包装器
    用于管理表格中的合并单元格信息，包括合并区域和单元格跨度
    """
    def __init__(self):
        # 存储所有合并单元格的信息，格式为: [((start_row, start_col), (end_row, end_col)), ...]
        self.merged_cells = []
        
        # 存储每个单元格的跨度信息，格式为: {(row, col): (rowspan, colspan)}
        # 如果单元格被合并，且不是起始单元格，则跨度为(0, 0)
        self.span_info = {}

    def add_merged_cell(self, start_pos, end_pos):
        """
        添加一个合并单元格区域
        :param start_pos: 起始单元格位置(row, col)
        :param end_pos: 结束单元格位置(row, col)
        """
        start_row, start_col = start_pos
        end_row, end_col = end_pos
        # 计算行和列的跨度
        rowspan = end_row - start_row + 1
        colspan = end_col - start_col + 1
        
        # 记录合并单元格信息
        self.merged_cells.append((start_pos, end_pos))
        # 记录起始单元格的跨度
        self.span_info[(start_row, start_col)] = (rowspan, colspan)
        
        # 标记被合并的单元格（非起始单元格）
        for row in range(start_row, end_row + 1):
            for col in range(start_col, end_col + 1):
                if (row, col) != (start_row, start_col):
                    # 将非起始单元格的跨度设为0，表示它们是被合并的
                    self.span_info[(row, col)] = (0, 0)

    def clear_merged_cells(self):
        """清除所有合并单元格信息"""
        self.merged_cells.clear()
        self.span_info.clear()

    def get_cell_span(self, row, col):
        """
        获取指定单元格的跨度信息
        :return: (rowspan, colspan) 元组，默认为(1, 1)表示未合并
        """
        return self.span_info.get((row, col), (1, 1))

class MergedTableView(QTableView):
    """
    支持合并单元格的表格视图
    通过继承QTableView并使用Qt的原生setSpan方法实现单元格合并
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        # 创建合并单元格模型
        self.merge_model = MergedCellTableModel()
        # 显示网格线
        self.setShowGrid(True)
        # 设置选择模式为单选
        self.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        # 设置选择行为为选择单元格
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectItems)

    def setSpan(self, row, column, rowSpan, columnSpan):
        """
        设置单元格的跨度（合并单元格）
        :param row: 起始行
        :param column: 起始列
        :param rowSpan: 跨越的行数
        :param columnSpan: 跨越的列数
        """
        # 调用Qt原生的setSpan方法进行单元格合并
        super().setSpan(row, column, rowSpan, columnSpan)
        # 如果是合并单元格（跨度大于1），则更新合并单元格模型
        if rowSpan > 1 or columnSpan > 1:
            start_pos = (row, column)
            end_pos = (row + rowSpan - 1, column + columnSpan - 1)
            self.merge_model.add_merged_cell(start_pos, end_pos)

    def setMergedCells(self, merged_cells):
        """
        批量设置合并单元格
        :param merged_cells: 合并单元格信息列表，格式为[((start_row, start_col), (end_row, end_col)), ...]
        """
        # 清除现有的合并单元格信息
        self.merge_model.clear_merged_cells()
        
        # 处理每个合并单元格
        for cell in merged_cells:
            try:
                # 验证数据格式
                if not isinstance(cell, tuple) or len(cell) != 2:
                    continue
                    
                start_pos, end_pos = cell
                if not isinstance(start_pos, tuple) or not isinstance(end_pos, tuple):
                    continue
                    
                start_row, start_col = start_pos
                end_row, end_col = end_pos
                
                if not all(isinstance(x, int) for x in (start_row, start_col, end_row, end_col)):
                    continue
                    
                # 计算跨度
                rowspan = end_row - start_row + 1
                colspan = end_col - start_col + 1
                
                # 设置单元格跨度
                self.setSpan(start_row, start_col, rowspan, colspan)
                
            except Exception as e:
                logging.error(f"Error setting merged cell {cell}: {str(e)}")
        
        # 更新视图
        self.viewport().update()