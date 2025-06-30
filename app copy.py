from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost/quality_reports'
db = SQLAlchemy(app)

# 用户模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(10), db.ForeignKey('employee_info.employee_id'), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)
    port = db.Column(db.String(100), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# 员工信息模型
class EmployeeInfo(db.Model):
    employee_id = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    department_name = db.Column(db.String(100), nullable=False)
    job_title = db.Column(db.String(100), nullable=False)
    port = db.Column(db.String(100), nullable=False)
    status = db.Column(db.CHAR(1), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    user = db.relationship('User', backref='employee', uselist=False)

# 考勤记录模型
class AttendanceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(10), db.ForeignKey('employee_info.employee_id'), nullable=False)  # 工号
    name = db.Column(db.String(50), nullable=False)  # 姓名
    department = db.Column(db.String(100), nullable=False)  # 部门
    job_title = db.Column(db.String(100), nullable=False)  # 岗位
    attendance_date = db.Column(db.Date, nullable=False, index=True)  # 时间
    shift_type = db.Column(db.String(10), nullable=False)  # 白班/夜班
    attendance_status = db.Column(db.String(20), nullable=False)  # 考勤状态
    overtime_hours = db.Column(db.Float, default=0)  # 加班时长（单位小时）

# 登录保护装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# 注册路由
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('用户名已存在')
            return redirect(url_for('register'))
        user = User(username=username, port=EmployeeInfo.query.filter_by(employee_id=username).first().port)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('注册成功，请登录')
        return redirect(url_for('login'))
    return render_template('register.html')

# 登录路由
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            # flash('登录成功')
            return redirect(url_for('dashboard'))
        else:
            flash('用户名或密码错误')
    return render_template('login.html')

# 退出登录路由
@app.route('/logout')
def logout():
    session.clear()
    flash('已退出登录')
    return redirect(url_for('login'))

# 仪表盘路由
@app.route('/dashboard')
@login_required
def dashboard():
    # 假设用户名和员工姓名是一致的，这里可以根据实际情况修改匹配逻辑
    employee = EmployeeInfo.query.filter_by(employee_id=session['username']).first()
    if employee:
        department_name = employee.department_name
        department_employees = EmployeeInfo.query.filter_by(department_name=department_name, status='t').all()
    else:
        department_employees = []
    return render_template('dashboard.html', department_employees=department_employees)


# 添加员工路由
@app.route('/add_employee', methods=['GET', 'POST'])
def add_employee():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # 获取表单数据
        employee_id = request.form['employee_id']
        name = request.form['name']
        job_title = request.form['job_title']

        current_user = EmployeeInfo.query.filter_by(employee_id=session['username']).first()
        if current_user:
            department = current_user.department_name
            port = current_user.port
        else:
            flash('无法获取您的部门信息，请联系管理员', 'error')
            return redirect(url_for('add_employee'))
        
        # 验证员工编号是否已存在
        existing_employee = EmployeeInfo.query.filter_by(employee_id=employee_id).first()
        if existing_employee:
            flash('员工编号已存在，请使用其他编号', 'error')
            return redirect(url_for('add_employee'))
        
        # 创建新员工对象
        new_employee = EmployeeInfo(
            employee_id=employee_id,
            name=name,
            department_name=department,
            job_title=job_title,
            port=port,
            status='t'  # 默认状态为 't' (在职)
        )
        
        # 保存到数据库
        try:
            db.session.add(new_employee)
            db.session.commit()
            flash('员工信息添加成功！', 'success')
            return redirect(url_for('add_employee'))
        except Exception as e:
            db.session.rollback()
            flash(f'添加员工失败: {str(e)}', 'error')
            return redirect(url_for('add_employee'))
    
    return render_template('add_employee.html')

# 管理员工路由
@app.route('/manage_employees')
@login_required
def manage_employees():
    # 获取当前用户信息
    current_user = EmployeeInfo.query.filter_by(employee_id=session['username']).first()
    
    if not current_user:
        flash('无法获取您的部门信息，请联系管理员', 'error')
        return redirect(url_for('dashboard'))
    
    # 获取当前用户所在部门的所有员工（包括已删除的）
    employees = EmployeeInfo.query.filter_by(department_name=current_user.department_name).all()
    
    return render_template('manage_employees.html', employees=employees, current_user=current_user)

# 删除员工路由
@app.route('/delete_employee/<employee_id>')
@login_required
def delete_employee(employee_id):
    employee = EmployeeInfo.query.filter_by(employee_id=employee_id).first()
    if employee:
        employee.status = 'f'  # 将状态修改为 'f' 表示删除
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'删除员工失败: {str(e)}', 'error')
    else:
        flash('未找到该员工信息', 'error')
    return redirect(url_for('manage_employees'))

# 恢复员工路由
@app.route('/restore_employee/<employee_id>')
@login_required
def restore_employee(employee_id):
    employee = EmployeeInfo.query.filter_by(employee_id=employee_id).first()
    if employee:
        employee.status = 't'  # 将状态修改为 't' 表示恢复
        try:
            db.session.commit()

        except Exception as e:
            db.session.rollback()
    else:
        flash('未找到该员工信息', 'error')
    return redirect(url_for('manage_employees'))

# 考勤提交路由
@app.route('/submit_attendance', methods=['POST'])
@login_required
def submit_attendance():
    if request.method == 'POST':
        # 获取当前用户信息
        current_user = EmployeeInfo.query.filter_by(employee_id=session['username']).first()
        if not current_user:
            flash('无法获取您的信息，请联系管理员', 'error')
            return redirect(url_for('dashboard'))

        # 获取表单数据
        attendance_date = request.form.get('attendance_date')
        employee_ids = request.form.getlist('employee_ids[]')
        shift_types = request.form.getlist('shift_types[]')
        attendance_statuses = request.form.getlist('attendance_statuses[]')
        overtime_hours = request.form.getlist('overtime_hours[]')

        # 转换日期格式
        # attendance_date = datetime.strptime(attendance_date, '%Y-%m-%d').date()

        try:
            for i in range(len(employee_ids)):
                employee = EmployeeInfo.query.filter_by(employee_id=employee_ids[i]).first()
                if employee:
                    # 检查是否存在当天的考勤记录
                    existing_record = AttendanceRecord.query.filter_by(
                        employee_id=employee.employee_id,
                        attendance_date=attendance_date
                    ).first()

                    if existing_record:
                        # 更新现有记录
                        existing_record.shift_type = shift_types[i]
                        existing_record.attendance_status = attendance_statuses[i]
                        existing_record.overtime_hours = float(overtime_hours[i]) if overtime_hours[i] else 0
                    else:
                        # 创建新记录
                        new_attendance = AttendanceRecord(
                            employee_id=employee.employee_id,
                            name=employee.name,
                            department=employee.department_name,
                            job_title=employee.job_title,
                            attendance_date=attendance_date,
                            shift_type=shift_types[i],
                            attendance_status=attendance_statuses[i],
                            overtime_hours=float(overtime_hours[i]) if overtime_hours[i] else 0
                        )
                        db.session.add(new_attendance)
            db.session.commit()
            flash('考勤信息提交成功！', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'提交考勤信息失败: {str(e)}', 'error')

    return redirect(url_for('dashboard'))

# 查看考勤记录路由
@app.route('/view_attendance/<employee_id>', methods=['GET', 'POST'])
@login_required
def view_attendance(employee_id):
    if request.method == 'POST':
        # 获取年月筛选条件
        year = request.form.get('year')
        month = request.form.get('month')
        # 根据年月筛选员工的历史考勤数据
        attendance_records = AttendanceRecord.query.filter(
            AttendanceRecord.employee_id == employee_id,
            db.extract('year', AttendanceRecord.attendance_date) == int(year),
            db.extract('month', AttendanceRecord.attendance_date) == int(month)
        ).all()
    else:
        # 默认显示所有历史数据
        year = datetime.now().year
        month = datetime.now().month
        attendance_records = AttendanceRecord.query.filter(
            AttendanceRecord.employee_id == employee_id,
            db.extract('year', AttendanceRecord.attendance_date) == int(year),
            db.extract('month', AttendanceRecord.attendance_date) == int(month),
            ).all()
    return render_template('view_attendance.html', attendance_records=attendance_records)

# 编辑考勤记录路由
@app.route('/edit_attendance/<employee_id>', methods=['GET', 'POST'])
@login_required
def edit_attendance(employee_id):
    if request.method == 'POST':
        # 获取年月筛选条件
        year = request.form.get('year')
        month = request.form.get('month')
        # 根据年月筛选员工的历史考勤数据
        attendance_records = AttendanceRecord.query.filter(
            AttendanceRecord.employee_id == employee_id,
            db.extract('year', AttendanceRecord.attendance_date) == int(year),
            db.extract('month', AttendanceRecord.attendance_date) == int(month)
        ).all()
    else:
        # 默认显示所有历史数据
        year = datetime.now().year
        month = datetime.now().month
        attendance_records = AttendanceRecord.query.filter(
            AttendanceRecord.employee_id == employee_id,
            db.extract('year', AttendanceRecord.attendance_date) == int(year),
            db.extract('month', AttendanceRecord.attendance_date) == int(month),
            ).all()
    return render_template('edit_attendance.html', attendance_records=attendance_records)

# 更新考勤记录路由
@app.route('/update_attendance', methods=['POST'])
@login_required
def update_attendance():
    attendance_ids = request.form.getlist('attendance_ids[]')
    shift_types = request.form.getlist('shift_types[]')
    attendance_statuses = request.form.getlist('attendance_statuses[]')
    overtime_hours = request.form.getlist('overtime_hours[]')

    try:
        for i in range(len(attendance_ids)):
            attendance_record = AttendanceRecord.query.get(attendance_ids[i])
            if attendance_record:
                attendance_record.shift_type = shift_types[i]
                attendance_record.attendance_status = attendance_statuses[i]
                attendance_record.overtime_hours = float(overtime_hours[i]) if overtime_hours[i] else 0
        db.session.commit()
        flash('考勤记录更新成功！', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'更新考勤记录失败: {str(e)}', 'error')

    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)