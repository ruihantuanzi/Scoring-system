from models import Session, User
from werkzeug.security import generate_password_hash

def update_passwords():
    db_session = Session()
    try:
        users = db_session.query(User).all()
        for user in users:
            # 生成密码哈希
            hashed_password = generate_password_hash(user.password)
            user.password = hashed_password
        db_session.commit()
        print("密码更新完成！")
    except Exception as e:
        db_session.rollback()
        print(f"更新密码失败: {str(e)}")
    finally:
        db_session.close()

if __name__ == '__main__':
    update_passwords()
