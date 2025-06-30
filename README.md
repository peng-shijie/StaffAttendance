# 企业员工管理系统

## 项目简介
企业员工管理系统是一个基于 Flask 框架开发的 Web 应用程序，用于企业内部员工信息管理和考勤记录管理。该系统提供了用户注册、登录、员工信息添加、员工信息管理、考勤记录提交以及月度考勤汇总下载等功能，帮助企业更高效地管理员工信息和考勤情况。

## 功能特性
1. **用户认证**：支持用户注册和登录功能，确保系统的安全性。
2. **员工信息管理**：允许管理员添加、删除、恢复员工信息，支持按状态筛选和搜索员工。
3. **考勤记录管理**：支持考勤记录的提交和更新，方便记录员工的考勤情况。
4. **月度考勤汇总**：提供月度考勤汇总功能，并支持将汇总数据下载为 CSV 文件。
5. **用户友好界面**：采用 Tailwind CSS 框架构建，界面简洁美观，易于使用。

## 技术栈
- **后端**：Flask、SQLAlchemy
- **前端**：HTML、Tailwind CSS、JavaScript
- **数据库**：MySQL

## 安装与配置
### 1. 克隆项目
```bash
git clone https://github.com/your-repo/StaffAttendance.git
cd StaffAttendance
```

### 2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate  # Windows
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 配置数据库
在 `app copy.py` 文件中修改数据库连接信息：
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost/quality_reports'
```

### 5. 初始化数据库
```bash
python
```
```python
from app copy import app, db
with app.app_context():
    db.create_all()
```

## 运行项目
```bash
python app copy.py
```
打开浏览器，访问 `http://127.0.0.1:5000` 即可进入系统登录页面。

## 项目结构
```
StaffAttendance/
├── app copy.py         # 主应用程序文件
├── app.py              # 月度考勤汇总下载路由文件
├── templates/          # 模板文件目录
│   ├── add_employee.html
│   ├── dashboard.html
│   ├── index.html
│   ├── login.html
│   ├── manage_employees.html
│   ├── monthly_summary.html
│   ├── register.html
└── ...
```

## 路由说明
- `/register`：用户注册页面
- `/`：用户登录页面
- `/logout`：退出登录
- `/dashboard`：用户中心页面
- `/add_employee`：添加员工页面
- `/manage_employees`：员工管理页面
- `/delete_employee/<employee_id>`：删除员工
- `/restore_employee/<employee_id>`：恢复员工
- `/submit_attendance`：考勤提交接口
- `/download_monthly_summary`：月度考勤汇总下载接口

## 贡献
如果你对该项目感兴趣，可以通过以下方式贡献：
1. 提交 Bug 报告或功能请求。
2. 提交 Pull Request 改进代码。

## 许可证
该项目采用 [MIT 许可证](LICENSE)。
