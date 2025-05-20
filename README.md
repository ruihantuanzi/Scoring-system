# 员工综合考核评价管理系统

这是一个基于Flask的员工综合考核评价管理系统，用于管理和记录员工的考核评分信息。

## 功能特点

### 用户功能
- 用户登录认证
- 查看个人信息
- 进行员工评分
- 查看已评分记录
- 导出评分记录CSV

### 管理员功能
- 用户信息管理
- 评分信息管理
- 评分完成情况统计
- 导出用户和评分数据

## 系统架构

### 技术栈
- 后端：Flask
- 数据库：SQLite
- 前端：HTML/CSS/JavaScript

### 目录结构
```
pingfen/
├── __pycache__/
├── app.py            # 主应用文件
├── init_db.py        # 数据库初始化脚本
├── models.py         # 数据库模型定义
├── requirements.txt  # 依赖文件
├── scores.csv        # 评分数据文件
├── scores.db        # SQLite数据库文件
├── scoring_system.db # 评分系统数据库
├── templates/        # 模板文件
├── update_passwords.py # 密码更新脚本
└── users.csv        # 用户数据文件
```

## 安装与运行

### 环境要求
- Python 3.13+
- Flask
- SQLAlchemy
- Werkzeug

### 安装依赖
```bash
pip install -r requirements.txt
```

### 初始化数据库
```bash
python init_db.py
```

### 运行应用
```bash
python app.py
```

访问 http://127.0.0.1:5000 查看应用

## 数据模型

### 用户(User)
- id_card: 身份证号
- name: 姓名
- company: 所属单位
- company_code: 单位编码
- department: 部门名称
- department_code: 部门编码
- position_type: 职位类别
- password: 密码（加密存储）
- is_admin: 是否管理员

### 评分(Score)
- id: 评分ID（评分人身份证号_被评分人身份证号）
- rater_id: 评分人ID
- rater_name: 评分人姓名
- rater_position: 评分人职位
- ratee_id: 被评分人ID
- ratee_name: 被评分人姓名
- ratee_position: 被评分人职位
- weight: 权重
- indicator1-5: 评分指标1-5
- total: 总分
- status: 评分状态（待评分/已评分）

## 使用说明

### 用户登录
- 访问登录页面
- 输入用户名和密码
- 登录后进入评分界面

### 评分操作
1. 在评分界面填写被评分人信息
2. 为每个指标打分
3. 点击"提交评分"按钮
4. 提交后可查看已评分记录

### 管理员操作
1. 登录管理员账号
2. 在导航栏选择不同管理界面
3. 可以查看和管理用户信息
4. 可以查看和管理评分信息
5. 可以查看评分完成情况统计
6. 可以导出相关数据

## 注意事项
- 系统使用HTTPS加密传输
- 密码使用加密存储
- 管理员权限需要特别注意安全
- 数据导出功能需要权限控制

## 开发者信息
- 项目维护者：[Ye zhiquan]
- 联系方式：[yzqonelife@gmail.com]

## 许可证
本项目采用MIT许可证。
