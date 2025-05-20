from flask import Flask, render_template, request, jsonify, redirect, url_for, session, Response
from io import StringIO
import csv
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from models import Session, User, Score
from collections import defaultdict
import json

# 密码最小长度
MIN_PASSWORD_LENGTH = 6

# 验证密码复杂度
def validate_password(password):
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"密码长度必须至少为{MIN_PASSWORD_LENGTH}个字符"
    if not any(c.isupper() for c in password):
        return False, "密码必须包含大写字母"
    if not any(c.islower() for c in password):
        return False, "密码必须包含小写字母"
    if not any(c.isdigit() for c in password):
        return False, "密码必须包含数字"
    return True, "密码验证通过"

# 登录验证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function

# 管理员验证装饰器
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function

# 数据库会话装饰器
def db_session_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        db_session = Session()
        try:
            result = f(db_session, *args, **kwargs)
            return result
        except Exception as e:
            db_session.rollback()
            return jsonify({'success': False, 'message': f'操作失败: {str(e)}'})
        finally:
            db_session.close()
    return decorated_function

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # 生产环境需替换

# 登录路由
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        id_card = request.form.get('id_card')
        password = request.form.get('password')
        
        if not id_card or not password:
            return render_template('login.html', error='请输入完整信息')
            
        db_session = Session()
        try:
            user = db_session.query(User).filter_by(id_card=id_card).first()
            if not user:
                return render_template('login.html', error='用户不存在')
            if not check_password_hash(user.password, password):
                return render_template('login.html', error='用户名或密码错误')
            # 设置会话
            session['user_id'] = user.id_card
            session['is_admin'] = user.is_admin
            return redirect('/admin' if user.is_admin else '/user')
        except Exception as e:
            db_session.rollback()
            return render_template('login.html', error=f'登录失败: {str(e)}')
        finally:
            db_session.close()
    
    # 重置会话
    session.clear()
    return render_template('login.html')

# 获取用户信息
@app.route('/api/user_info')
@login_required
def get_user_info():
    db_session = Session()
    try:
        user = db_session.query(User).filter_by(id_card=session['user_id']).first()
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
            
        return jsonify({
            'success': True,
            'data': {
                'name': user.name,
                'company': user.company,
                'department': user.department,
                'position_type': user.position_type
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        db_session.close()

# 查看已评分信息
@app.route('/view_scores')
@login_required
def view_scores():
    db_session = Session()
    try:
        # 获取当前用户已评分的记录
        scores = db_session.query(Score).filter_by(
            rater_id=session['user_id'],
            status='已评分'
        ).all()
        
        return render_template('view_scores.html', scores=scores)
    except Exception as e:
        flash(f'获取评分信息失败: {str(e)}')
        return redirect('/user')
    finally:
        db_session.close()

# 用户界面
@app.route('/user')
@login_required
def user():
    db_session = Session()
    try:
        user = db_session.query(User).filter_by(id_card=session['user_id']).first()
        if not user:
            return redirect('/')
            
        # 获取当前用户需要评分的用户
        scores = db_session.query(Score).filter_by(
            rater_id=session['user_id'],
            status='待评分'
        ).all()
        
        # 添加被评分人的单位和部门信息
        for score in scores:
            ratee = db_session.query(User).filter_by(id_card=score.ratee_id).first()
            if ratee:
                score.ratee_company = ratee.company
                score.ratee_department = ratee.department
                score.ratee_position_type = ratee.position_type
        
        return render_template('user.html', user=user, scores=scores)
    except Exception as e:
        flash(f'获取用户信息失败: {str(e)}')
        return redirect('/')
    finally:
        db_session.close()



# 获取评分信息
@app.route('/api/score_info')
@login_required
def get_score_info():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    db_session = Session()
    
    # 获取当前用户的评分任务
    score = db_session.query(Score).filter_by(
        rater_id=session['user_id'],
        status='待评分'
    ).first()
    
    if not score:
        return jsonify({'success': False, 'message': '没有待评分任务'})
    
    ratee = db_session.query(User).filter_by(id_card=score.ratee_id).first()
    
    score_info = {
        'ratee_name': ratee.name if ratee else '未知',
        'ratee_company': ratee.company if ratee else '未知',
        'ratee_position': ratee.position_type if ratee else '未知',
        'current_weight': score.weight
    }
    
    return jsonify({'success': True, 'data': score_info})

def parse_form_data(form_data):
    """解析嵌套表单数据"""
    print("\n=== Raw Form Data ===")
    for key, value in form_data.items():
        print(f"Raw Key: {key}, Value: {value}")
    print("=== End of Raw Data ===")
    
    data = {}
    for key, value in form_data.items():
        if '[' in key:  # 处理scores[0][indicators][1]格式
            print(f"\nProcessing key: {key}")
            parts = key.replace(']', '').split('[')
            print(f"Split parts: {parts}")
            
            ptr = data
            for part in parts[:-1]:
                print(f"Creating/Accessing part: {part}")
                ptr = ptr.setdefault(part, {})
            
            print(f"Setting final value: {value}")
            ptr[parts[-1]] = value
    
    print("\n=== Final Parsed Data ===")
    print(data)
    print("=== End of Final Data ===")
    return data

@app.route('/submit_score', methods=['POST'])
@login_required
def submit_score():
    db_session = Session()
    try:
        # 获取JSON数据
        if request.is_json:
            data = request.get_json()
            print("\n=== Received JSON Data ===")
            print(data)
            print("=== End of JSON Data ===\n")
        else:
            # 处理表单数据
            print("\n=== Raw Form Data ===")
            for key, value in request.form.items():
                print(f"{key}: {value}")
            print("=== End of Raw Form Data ===\n")

            # 结构化数据收集
            score_data = defaultdict(dict)
            for key, value in request.form.items():
                if key.startswith('score_id_'):
                    _, _, index = key.partition('_id_')
                    score_data[index]['score_id'] = value
                elif key.startswith('indicator'):
                    _, indicator, index = key.split('_', 2)
                    score_data[index][indicator] = value
            
            data = list(score_data.values())

        # 批量处理评分
        updated = 0
        for item in data:
            if not all(k in item for k in ['score_id'] + [f'indicator{i}' for i in range(1,6)]):
                continue

            # 精确匹配评分记录
            score = db_session.query(Score).filter_by(
                id=item['score_id'],
                rater_id=session['user_id']  # 确保评分人匹配
            ).first()

            if score and all(0 <= float(item[f'indicator{i}']) <= 20 for i in range(1,6)):
                for i in range(1,6):
                    setattr(score, f'indicator{i}', float(item[f'indicator{i}']))
                score.total = sum(float(item[f'indicator{i}']) for i in range(1,6)) * score.weight
                score.status = '已评分'
                updated += 1

        db_session.commit()
        if updated:
            flash(f'成功更新 {updated} 条评分记录', 'success')
        else:
            flash('没有评分被更新', 'warning')
        return jsonify({
            'success': bool(updated),
            'message': '评分已提交'
        })

    except Exception as e:
        db_session.rollback()
        print(f"Error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'评分提交失败: {str(e)}'
        }), 500
    finally:
        db_session.close()

# 管理员界面
@app.route('/admin')
@admin_required
def admin_portal():
    if not session.get('is_admin'):
        return redirect('/')
    
    db_session = Session()
    # 获取当前管理员信息
    admin_id = session.get('user_id')
    admin = db_session.query(User).filter_by(id_card=admin_id).first()
    users = db_session.query(User).all()
    scores = db_session.query(Score).all()
    
    # 统计评分完成情况
    db_session = Session()
    
    # 获取所有单位
    companies = db_session.query(User.company).distinct().all()
    
    # 获取所有评分人
    all_raters = db_session.query(Score.rater_id).distinct().all()
    
    # 获取已完成评分的评分人
    completed_raters = db_session.query(Score.rater_id).distinct().filter(Score.status == '已评分').all()
    
    # 计算完成率排名
    company_stats = []
    for company in companies:
        company_name = company[0]
        
        # 该单位的所有评分人
        company_users = db_session.query(User.id_card).filter(User.company == company_name).all()
        company_user_ids = [user[0] for user in company_users]
        
        # 该单位的评分人总数
        total_users = len(company_user_ids)
        
        # 该单位已完成评分的评分人
        completed_count = db_session.query(Score.rater_id).distinct().filter(
            Score.status == '已评分',
            Score.rater_id.in_(company_user_ids)
        ).count()
        
        # 计算完成率
        completion_rate = (completed_count / total_users * 100) if total_users > 0 else 0
        
        company_stats.append({
            'company': company_name,
            'total_users': total_users,
            'completed': completed_count,
            'pending': total_users - completed_count,
            'completion_rate': completion_rate
        })
    
    # 按完成率排序
    company_stats.sort(key=lambda x: x['completion_rate'], reverse=True)
    
    # 为每个单位添加排名
    for i, stat in enumerate(company_stats, 1):
        stat['rank'] = i
    
    # 关闭数据库会话
    db_session.close()
    
    # 将数据转换为JSON字符串
    company_stats_json = json.dumps(company_stats)
    
    return render_template('admin.html', 
                         users=users, 
                         scores=scores, 
                         admin=admin, 
                         company_stats=company_stats,
                         company_stats_json=company_stats_json)

# 更新用户信息
@app.route('/update_user', methods=['POST'])
@admin_required
def update_user():
    if not session.get('is_admin'):
        return jsonify({'success': False, 'message': '权限不足'})
    
    id_card = request.form.get('id_card')
    if not id_card:
        return jsonify({'success': False, 'message': '缺少用户ID'})
        
    db_session = Session()
    try:
        user = db_session.query(User).filter_by(id_card=id_card).first()
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'})
        
        # 获取新密码
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # 验证密码是否匹配
        if new_password != confirm_password:
            return jsonify({'success': False, 'message': '两次输入的密码不一致'})
            
        # 验证密码复杂度
        valid, msg = validate_password(new_password)
        if not valid:
            return jsonify({'success': False, 'message': msg})
            
        # 更新密码
        user.password = generate_password_hash(new_password)
        db_session.commit()
        return jsonify({'success': True, 'message': '密码更新成功'})
    except Exception as e:
        db_session.rollback()
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'})
    finally:
        db_session.close()
# 导出用户数据
@app.route('/export_users')
@admin_required
def export_users():
    if not session.get('is_admin'):
        return redirect('/')
    
    db_session = Session()
    users = db_session.query(User).all()
    
    # 创建 CSV 数据
    csv_data = "身份证号,姓名,所属单位,单位编码,部门名称,部门编码,职位类别,是否管理员\n"
    for user in users:
        csv_data += f"{user.id_card},{user.name},{user.company},{user.company_code},"\
                   f"{user.department},{user.department_code},{user.position_type},"\
                   f"{user.is_admin}\n"
    
    db_session.close()
    
    # 设置响应头
    response = Response(
        csv_data,
        mimetype='text/csv',
        headers={
            'Content-Disposition': 'attachment; filename=users.csv'
        }
    )
    return response

# 导出用户评分记录（普通用户使用）
@app.route('/export_scores')
@login_required
def export_scores():
    db_session = Session()
    try:
        # 获取当前用户的所有评分记录
        scores = db_session.query(Score).filter_by(
            rater_id=session['user_id'],
            status='已评分'
        ).all()
        
        # 创建CSV数据
        csv_data = "被评分人姓名,职位,指标1,指标2,指标3,指标4,指标5,总分,状态\n"
        for score in scores:
            csv_data += f"{score.ratee_name},{score.ratee_position},"\
                       f"{score.indicator1},{score.indicator2},{score.indicator3},"\
                       f"{score.indicator4},{score.indicator5},{score.total},{score.status}\n"
        
        db_session.close()
        
        # 设置响应头
        response = Response(
            csv_data,
            mimetype='text/csv',
            headers={
                'Content-Disposition': 'attachment; filename=ratings.csv'
            }
        )
        return response
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'导出评分记录失败: {str(e)}'
        }), 500

# 导出所有评分记录（管理员使用）
@app.route('/admin/export_scores')
@admin_required
def export_all_scores():
    db_session = Session()
    try:
        # 获取所有评分记录
        scores = db_session.query(Score).all()
        
        # 创建CSV数据
        csv_data = StringIO()
        writer = csv.writer(csv_data)
        
        # 写入表头
        writer.writerow([
            '评分ID', '评分人', '被评分人', '权重',
            '指标1', '指标2', '指标3', '指标4', '指标5',
            '总分', '状态', '评分人职位', '被评分人职位'
        ])
        
        # 写入数据
        for score in scores:
            writer.writerow([
                score.id,
                score.rater_name,
                score.ratee_name,
                score.weight,
                score.indicator1,
                score.indicator2,
                score.indicator3,
                score.indicator4,
                score.indicator5,
                score.total,
                score.status,
                score.rater_position,
                score.ratee_position
            ])
        
        db_session.close()
        
        # 设置响应
        response = Response(
            csv_data.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': 'attachment; filename=all_scores.csv'
            }
        )
        return response
    except Exception as e:
        print(f"导出评分失败: {str(e)}")
        return jsonify({'success': False, 'message': '导出评分失败'}), 500
    finally:
        db_session.close()

# 退出登录
@app.route('/logout', methods=['POST'])
def logout():
    try:
        # 清除session
        session.clear()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
