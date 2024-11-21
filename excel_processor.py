import sqlite3
from typing import Optional, List, Dict, Tuple, Union, Any
import os
import logging
import polars as pl
from dataclasses import dataclass
from models.timer import PerformanceTimer
from models.decorators import ExceptionHandler
from fastexcel import read_excel
from python_calamine import CalamineWorkbook
# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('excel_processor.log')
    ]
)

@dataclass
class SheetInfo:
    """Sheet 信息数据表示"""
    sheet_name: str
    sheet_id:int

class ExcelProcessor:
    def __init__(self, db_path: str = "data.db"):
        """初始化Excel处理器
        
        Args:
            db_path: SQLite数据库路径
        """
        self.db_path = db_path
        self.file_path = None
        self.sheet_info = [] # 缓存工作表信息
        self.excel_reader = None
    
    def _handle_duplicate_headers(self, headers: List[str]) -> List[str]:
        """处理重复的列名
        
        Args:
            headers: 原始列名列表
            
        Returns:
            处理后的列名列表
        """
        seen = set()
        unique_headers = []
        
        for header in headers:
            if not header:  # 处理空列名
                header = "Column"
            
            # 清理列名（移除不允许的字符）
            header = str(header).strip().replace('\n', ' ').replace('\r', '')
            
            # 如果列名已存在，添加数字后缀
            base_header = header
            counter = 1
            while header in seen:
                header = f"{base_header}_{counter}"
                counter += 1
            
            seen.add(header)
            unique_headers.append(header)
        
        return unique_headers


        
    def _get_table_name(self, file_path: str, sheet_name: str) -> str:
        """生成数据库表名
        
        Args:
            file_path: Excel文件路径
            sheet_name: 工作表名称
            
        Returns:
            表名
        """
        # 使用文件名（不含路径和扩展名）和工作表名称组合成表名
        file_name = os.path.splitext(os.path.basename(file_path))[0]
        # 将非法字符替换为下划线
        file_name = ''.join(c if c.isalnum() else '_' for c in file_name)
        return f"{file_name}_{sheet_name}"

    @ExceptionHandler(error_message="打开Excel文件失败", return_value=[])
    def read_excel_structure(self, file_path: str) -> List[SheetInfo]:
        """读取 Excel 文件的所有 sheet 信息"""

        self.file_path = file_path

        if not self.file_path:
            raise FileNotFoundError("文件路径未指定")
            
        # 只测量实际读取 Excel 的时间
        with PerformanceTimer("Excel读取操作"):
            self.excel_reader = read_excel(self.file_path)
            sheets:List[str] = self.excel_reader.sheet_names

            self.sheets_info = [
                SheetInfo(sheet_id=idx, sheet_name=name)
                for idx, name in enumerate(sheets)
            ]
            print(self.sheets_info)
            logging.info(f"成功读取 {len(self.sheets_info)} 个工作表")
        return self.sheets_info    
  
    @ExceptionHandler(error_message="读取工作表数据失败", return_value=([], []))
    def read_sheet_data(self, sheet: Union[SheetInfo, int, str]) -> Tuple[List[List[Any]], List[Tuple[Tuple[int, int], Tuple[int, int]]]]:
        """读取指定工作表的数据和合并单元格信息
        
        Returns:
            Tuple[List[List[Any]], List[Tuple[Tuple[int, int], Tuple[int, int]]]]:
            - 第一个元素是工作表数据
            - 第二个元素是合并单元格信息，格式为 [((start_row, start_col), (end_row, end_col)), ...]
        """
        if not self.excel_reader:
            raise ValueError("请先调用 read_excel_structure 方法读取工作表信息")
        
        target_sheet = None
        if isinstance(sheet,SheetInfo):
            target_sheet = sheet
        elif isinstance(sheet, int):
            if  0<= sheet < len(self.sheets_info):
                target_sheet = self.sheets_info[sheet]
            else:
                raise ValueError(f"工作表索引超出范围: {sheet}")
        elif isinstance(sheet, str):
            target_sheet = next(
                (s for s in self.sheets_info if s.sheet_name == sheet), None
            )

            if not target_sheet:
                raise ValueError(f"未找到Sheet名为: {sheet} 的工作表")
        
        with PerformanceTimer("读取工作表数据"):
            # 使用 python-calamine 读取数据
            workbook = CalamineWorkbook.from_path(self.file_path)
            sheet_data = workbook.get_sheet_by_name(target_sheet.sheet_name)
            
            # 获取数据
            data = sheet_data.to_python(skip_empty_area=False)
            
            # 获取并转换合并单元格信息
            raw_merged_cells = sheet_data.ranges
            merged_cells = []
            
            # 详细的调试信息
            logging.info(f"工作表 {target_sheet.sheet_name} 的原始合并单元格信息: {raw_merged_cells}")
            
            if raw_merged_cells:
                for cell_range in raw_merged_cells:
                    # 获取起始和结束位置
                    start_row, start_col = cell_range[0]
                    end_row, end_col = cell_range[1]
                        
                    # 确保坐标是整数
                    start_row, start_col = int(start_row), int(start_col)
                    end_row, end_col = int(end_row), int(end_col)
                        
                    # 添加到合并单元格列表
                    merged_cells.append(((start_row, start_col), (end_row, end_col)))
                        

            logging.info(f"成功读取工作表 {target_sheet.sheet_name} 的数据：{len(data)} 行")
            logging.info(f"处理后的合并单元格信息: {merged_cells}")
            
            return data, merged_cells
        
            
    def create_table_for_sheet(self, conn: sqlite3.Connection, file_path: str, sheet_name: str, columns: List[str]) -> str:
        """为工作表创建数据表
        
        Args:
            conn: 数据库连接
            file_path: Excel文件路径
            sheet_name: 工作表名称
            columns: 列名列表
            
        Returns:
            表名
        """
        try:
            # 生成表名
            table_name = self._get_table_name(file_path, sheet_name)
            
            # 先删除已存在的表
            conn.execute(f"DROP TABLE IF EXISTS [{table_name}]")
            
            # 构建CREATE TABLE语句
            columns_def = []
            for col in columns:
                # SQLite中列名使用方括号包裹，可以处理特殊字符
                col_name = f"[{col}]"
                columns_def.append(f"{col_name} TEXT")
            
            create_table_sql = f"""
            CREATE TABLE [{table_name}] (
                {', '.join(columns_def)}
            )
            """
            
            logging.info(f"创建表SQL: {create_table_sql}")
            conn.execute(create_table_sql)
            return table_name
            
        except Exception as e:
            logging.error(f"创建表失败: {str(e)}\nSQL: {create_table_sql}")
            raise
    
    def save_sheet_data(self, file_path: str, sheet_name: str, headers: List[str], data: List[Dict]):
        """保存工作表数据到数据库
        
        Args:
            file_path: Excel文件路径
            sheet_name: 工作表名称
            headers: 列名列表
            data: 数据行列表
        """
        if not headers or not data:
            logging.error("无效的数据：headers或data为空")
            return

        conn = sqlite3.connect(self.db_path)
        try:
            # 创建表
            table_name = self.create_table_for_sheet(conn, file_path, sheet_name, headers)
            
            # 构建INSERT语句，使用方括号包裹列名
            columns = [f"[{h}]" for h in headers]
            placeholders = ','.join(['?' for _ in headers])
            insert_sql = f"""INSERT INTO [{table_name}] 
                ({','.join(columns)}) 
                VALUES ({placeholders})"""
            
            # 插入数据
            for row in data:
                try:
                    values = []
                    for header in headers:
                        value = row.get(header, "")
                        # 处理特殊字符和换行符
                        if isinstance(value, str):
                            value = value.replace('\x00', '').strip()
                        values.append(value)
                    conn.execute(insert_sql, values)
                except Exception as e:
                    logging.error(f"插入数据失败: {str(e)}\nSQL: {insert_sql}\n数据: {values}")
                    raise
            
            conn.commit()
            logging.info(f"成功保存 {len(data)} 行数据到表 {table_name}")
            
        except Exception as e:
            logging.error(f"保存数据失败: {str(e)}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def get_sheet_data_from_db(self, file_path: str, sheet_name: str) -> Tuple[List[str], List[Dict]]:
        """从数据库获取工作表数据
        
        Args:
            file_path: Excel文件路径
            sheet_name: 工作表名称
            
        Returns:
            (列名列表, 数据行列表)
        """
        conn = sqlite3.connect(self.db_path)
        try:
            table_name = self._get_table_name(file_path, sheet_name)
            
            # 检查表是否存在
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=?
            """, (table_name,))
            if not cursor.fetchone():
                raise Exception(f"表 {table_name} 不存在")
            
            # 获取列名
            cursor = conn.execute(f"PRAGMA table_info([{table_name}])")
            headers = []
            for row in cursor:
                col_name = row[1].strip('[]')  # 移除列名中的方括号
                headers.append(col_name)
            
            if not headers:
                raise Exception(f"表 {table_name} 没有列")
            
            # 构建查询语句，使用方括号包裹列名
            columns = [f"[{h}]" for h in headers]
            select_sql = f"""
                SELECT {','.join(columns)}
                FROM [{table_name}]
            """
            
            # 获取数据
            try:
                cursor = conn.execute(select_sql)
                data = []
                for row in cursor:
                    row_data = {}
                    for header, value in zip(headers, row):
                        row_data[header] = value if value is not None else ""
                    data.append(row_data)
                
                logging.info(f"成功从表 {table_name} 读取 {len(data)} 行数据")
                return headers, data
            except Exception as e:
                logging.error(f"查询数据失败: {str(e)}\nSQL: {select_sql}")
                raise
                
        except Exception as e:
            logging.error(f"获取数据失败: {str(e)}")
            raise
        finally:
            conn.close()

    def get_sheet_names(self) -> List[str]:
        """获取所有工作表名称"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'sheet_%'")
            tables = cursor.fetchall()
            return [table[0].replace('sheet_', '').replace('_', ' ') for table in tables]
        finally:
            conn.close()