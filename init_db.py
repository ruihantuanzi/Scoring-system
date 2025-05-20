import csv
from sqlalchemy import create_engine
from models import Base, User, Score, Session
from sqlalchemy.orm import sessionmaker

def init_database():
    # 创建数据库连接
    engine = create_engine('sqlite:///scores.db', connect_args={'check_same_thread': False})
    
    # 创建表
    Base.metadata.create_all(engine)
    
    # 创建会话
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 读取用户数据
        with open('users.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            users = []
            for row in reader:
                from werkzeug.security import generate_password_hash
                user = User(
                    id_card=row['身份证号'],
                    name=row['姓名'],
                    company=row['所属单位'],
                    company_code=row['单位编码'],
                    department=row['部门名称'],
                    department_code=row['部门编码'],
                    position_type=row['职位类别'],
                    password=generate_password_hash(row['密码']),
                    is_admin=row['是否管理员'] == '1'
                )
                users.append(user)
            session.add_all(users)
            session.commit()
        
        # 读取评分数据
        with open('scores.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            scores = []
            for row in reader:
                # 生成评分ID（评分人身份证号_被评分人身份证号）
                score_id = f"{row['身份证号1']}_{row['身份证号2']}"
                
                score = Score(
                    id=score_id,
                    rater_id=row['身份证号1'],
                    rater_name=row['评分人'],
                    rater_position=row['职位类别'],
                    ratee_id=row['身份证号2'],
                    ratee_name=row['被评分人'],
                    ratee_position=row['职位类别'],
                    weight=float(row['权重']),
                    status='待评分'  # 默认设置为待评分状态
                )
                scores.append(score)
            session.add_all(scores)
            session.commit()
        
        print("数据库初始化完成！")
    except Exception as e:
        session.rollback()
        print(f"初始化数据库失败: {str(e)}")
    finally:
        session.close()

if __name__ == '__main__':
    init_database()
