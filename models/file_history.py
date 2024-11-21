from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class FileHistory(Base):
    __tablename__ = 'file_history'

    id = Column(Integer, primary_key=True)
    file_name = Column(String(255), nullable=False)  # 文件名
    file_path = Column(String(1024), nullable=False, unique=True)  # 文件完整路径（唯一）
    file_type = Column(String(50))  # 文件类型
    file_size = Column(Integer)  # 文件大小（字节）
    modified_date = Column(DateTime)  # 文件修改日期
    created_at = Column(DateTime, default=datetime.now)  # 记录创建时间

    def __repr__(self):
        return f"<FileHistory(file_name='{self.file_name}', file_path='{self.file_path}')>"
