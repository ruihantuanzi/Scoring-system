from sqlalchemy import create_engine, Column, String, Float, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class User(Base):
    """用户表模型"""
    __tablename__ = 'users'
    
    id_card = Column(String(18), primary_key=True)  # 身份证号
    name = Column(String(50))                      # 姓名
    company = Column(String(100))                  # 所属单位
    company_code = Column(String(10))              # 单位编码
    department = Column(String(100))               # 部门名称
    department_code = Column(String(10))           # 部门编码
    position_type = Column(String(50))             # 职位类别
    password = Column(String(50))                  # 密码
    is_admin = Column(Boolean)                     # 是否管理员

class Score(Base):
    """评分表模型"""
    __tablename__ = 'scores'
    
    id = Column(String(50), primary_key=True)       # 组合主键：评分人+被评分人
    rater_id = Column(String(18), nullable=False)   # 评分人身份证号
    rater_name = Column(String(50), nullable=False) # 评分人姓名
    rater_position = Column(String(50), nullable=False) # 评分人职位
    ratee_id = Column(String(18), nullable=False)   # 被评分人身份证号
    ratee_name = Column(String(50), nullable=False) # 被评分人姓名
    ratee_position = Column(String(50), nullable=False) # 被评分人职位
    weight = Column(Float, nullable=False)          # 权重
    indicator1 = Column(Float, default=0)           # 指标1
    indicator2 = Column(Float, default=0)           # 指标2
    indicator3 = Column(Float, default=0)           # 指标3
    indicator4 = Column(Float, default=0)           # 指标4
    indicator5 = Column(Float, default=0)           # 指标5
    total = Column(Float, default=0)                # 合计（自动计算）
    status = Column(String(20), default='待评分')    # 评分状态：待评分/已评分

# 数据库连接配置（SQLite示例）
engine = create_engine('sqlite:///scores.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
