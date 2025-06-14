import os
import json
import time
import secrets
import string
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, make_response
from werkzeug.utils import secure_filename
import pandas as pd
import hashlib

# 导入问卷分析和报告生成功能
import analysis_engine

# 初始化Flask应用
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_change_in_production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上传文件大小为16MB

# 管理员密码配置
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')  # 默认密码，生产环境应该修改

# 生成随机路由ID
def generate_route_id():
    """生成16位随机路由ID（数字+大小写字母）"""
    chars = string.ascii_letters + string.digits  # a-z, A-Z, 0-9
    route_id = ''.join(secrets.choice(chars) for _ in range(16))
    if route_exists(route_id):
        return generate_route_id() 
    return route_id

# 辅助函数：格式化文件大小
def format_file_size(size_bytes):
    """将字节数转换为人类可读的文件大小格式"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

# 注册模板过滤器
app.jinja_env.filters['format_file_size'] = format_file_size

# 辅助函数：生成密码哈希
def generate_password_hash(password):
    """生成密码的哈希值"""
    return hashlib.sha256((password + app.secret_key).encode()).hexdigest()

# 辅助函数：验证管理员权限
def check_admin_auth():
    """检查管理员权限"""
    admin_hash = request.cookies.get('admin_auth')
    expected_hash = generate_password_hash(ADMIN_PASSWORD)
    return admin_hash == expected_hash

# 辅助函数：检查路由是否存在
def route_exists(route_id):
    """检查路由是否已存在"""
    if not route_id:
        return False
    questionnaire_dir = os.path.join('original_questionnaire', route_id)
    return os.path.exists(questionnaire_dir)

# 辅助函数：验证路由编号
def validate_route_id(route_id):
    """验证路由编号是否合法"""
    if not route_id:
        return False
    # 只允许字母、数字和下划线
    return route_id.replace('_', '').replace('-', '').isalnum() and len(route_id) <= 50

# 确保必要的目录存在
def ensure_directories(route_id=None):
    """创建必要的目录结构"""
    base_directories = [
        'templates',
        'static/css',
        'static/js',
    ]
    
    # 创建基础目录
    for directory in base_directories:
        os.makedirs(directory, exist_ok=True)
    
    # 如果指定了路由编号，创建对应的目录
    if route_id:
        route_directories = [
            f'original_questionnaire/{route_id}',
            f'output/{route_id}/student_reports',
            f'output/{route_id}/internal_reports',
        ]
        for directory in route_directories:
            os.makedirs(directory, exist_ok=True)

# 初始化基础目录
ensure_directories()

# 主页（重定向到路由选择页面）
@app.route('/')
def index():
    """显示路由选择页面或重定向"""
    return render_template('route_selection.html')

# 学生问卷页面（带路由编号）
@app.route('/<route_id>')
def questionnaire(route_id):
    """显示特定路由的问卷填写页面"""
    if not validate_route_id(route_id):
        flash("无效的路由编号", "error")
        return redirect(url_for('index'))
    
    # 检查路由是否存在
    if not route_exists(route_id):
        flash("路由编号不存在，请检查您输入的路由编号是否正确", "error")
        return redirect(url_for('index'))
    
    return render_template('questionnaire.html', route_id=route_id)

# 问卷提交处理（带路由编号）
@app.route('/submit/<route_id>', methods=['POST'])
def submit_questionnaire(route_id):
    """处理提交的问卷数据"""
    if not validate_route_id(route_id):
        flash("无效的路由编号", "error")
        return redirect(url_for('index'))
    
    # 检查路由是否存在
    if not route_exists(route_id):
        flash("路由编号不存在，无法提交问卷", "error")
        return redirect(url_for('index'))
    
    try:
        # 获取表单数据
        form_data = {}
        for key, value in request.form.items():
            form_data[key] = value
        
        # 生成时间戳和唯一文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        student_name = form_data.get('姓名', 'unknown_student')
        filename = f"{timestamp}_{student_name}_questionnaire.csv"
        
        # 将表单数据转换为DataFrame
        df = pd.DataFrame([form_data])
        
        # 保存为CSV文件到特定路由文件夹
        file_path = os.path.join('original_questionnaire', route_id, filename)
        df.to_csv(file_path, index=False)
        
        # 异步分析问卷并生成报告（后台处理）
        try:
            analysis_engine.process_questionnaire(file_path, route_id)
        except Exception as e:
            app.logger.error(f"问卷分析失败: {str(e)}")
            # 分析失败不影响用户体验，继续显示成功页面
        
        # 直接跳转到结果页面
        return redirect(url_for('questionnaire_result', route_id=route_id, student_name=student_name))
    
    except Exception as e:
        app.logger.error(f"问卷提交处理错误: {str(e)}")
        flash(f"问卷提交失败: {str(e)}", "error")
        return redirect(url_for('questionnaire', route_id=route_id))

# 问卷结果页面（带路由编号）
@app.route('/result/<route_id>/<student_name>')
def questionnaire_result(route_id, student_name):
    """显示问卷提交后的结果页面"""
    if not validate_route_id(route_id):
        flash("无效的路由编号", "error")
        return redirect(url_for('index'))
    
    # 检查路由是否存在
    if not route_exists(route_id):
        flash("路由编号不存在", "error")
        return redirect(url_for('index'))
    
    return render_template('result.html', route_id=route_id, student_name=student_name)

# 管理员登录页面
@app.route('/admin/login')
def admin_login():
    """显示管理员登录页面"""
    return render_template('admin_login.html')

# 管理员密码验证
@app.route('/admin/auth', methods=['POST'])
def admin_auth():
    """处理管理员密码验证"""
    password = request.form.get('password')
    redirect_to = request.form.get('redirect_to', 'admin_routes')
    
    if password == ADMIN_PASSWORD:
        # 密码正确，设置cookie并重定向
        response = make_response(redirect(url_for(redirect_to)))
        admin_hash = generate_password_hash(ADMIN_PASSWORD)
        response.set_cookie('admin_auth', admin_hash, max_age=60*60*24)  # 有效期24小时
        flash("登录成功", "success")
        return response
    else:
        # 密码错误
        flash("密码错误，请重试", "error")
        return redirect(url_for('admin_login'))

# 管理员路由选择页面
@app.route('/admin')
def admin_routes():
    """显示管理员路由选择页面"""
    # 检查管理员权限
    if not check_admin_auth():
        return redirect(url_for('admin_login'))
    
    # 扫描所有路由文件夹
    routes = []
    questionnaire_base_dir = 'original_questionnaire'
    if os.path.exists(questionnaire_base_dir):
        for route_id in os.listdir(questionnaire_base_dir):
            route_path = os.path.join(questionnaire_base_dir, route_id)
            if os.path.isdir(route_path):
                # 统计该路由下的问卷数量
                csv_files = [f for f in os.listdir(route_path) if f.endswith('.csv')]
                routes.append({
                    'route_id': route_id,
                    'questionnaire_count': len(csv_files)
                })
    
    routes.sort(key=lambda x: x['route_id'])
    return render_template('admin_routes.html', routes=routes)

# 管理员登出
@app.route('/admin/logout')
def admin_logout():
    """管理员登出"""
    response = make_response(redirect(url_for('index')))
    response.set_cookie('admin_auth', '', expires=0)  # 清除cookie
    flash("已成功登出", "info")
    return response

# 管理员面板（带路由编号）
@app.route('/admin/<route_id>')
def admin_panel(route_id):
    """管理员控制面板，显示特定路由的所有提交问卷和生成的报告"""
    # 检查管理员权限
    if not check_admin_auth():
        return redirect(url_for('admin_login'))
    
    if not validate_route_id(route_id):
        flash("无效的路由编号", "error")
        return redirect(url_for('admin_routes'))
    
    # 获取指定路由的所有提交问卷
    questionnaire_dir = os.path.join('original_questionnaire', route_id)
    questionnaires = []
    
    if os.path.exists(questionnaire_dir):
        files = os.listdir(questionnaire_dir)
        for file in files:
            if file.endswith('.csv'):
                # 从文件名提取信息
                parts = file.split('_')
                if len(parts) >= 3:
                    date_time = parts[0] + '_' + parts[1]
                    student_name = '_'.join(parts[2:-1])  # 处理名字中可能包含下划线的情况
                    
                    questionnaires.append({
                        'file': file,
                        'student_name': student_name,
                        'timestamp': date_time
                    })
    
    # 按时间戳排序，最新的在前面
    questionnaires.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # 获取所有生成的报告文件
    reports = []
    
    # 扫描学生报告
    student_reports_dir = os.path.join('output', route_id, 'student_reports')
    if os.path.exists(student_reports_dir):
        files = os.listdir(student_reports_dir)
        for file in files:
            if file.endswith(('.md', '.pdf')):
                # 解析文件名: timestamp_studentname_学生报告.format
                if '学生报告' in file:
                    parts = file.split('_')
                    if len(parts) >= 3:
                        timestamp = parts[0] + '_' + parts[1]
                        student_name = '_'.join(parts[2:]).replace('_学生报告.md', '').replace('_学生报告.pdf', '')
                        file_format = file.split('.')[-1]
                        
                        reports.append({
                            'file': file,
                            'student_name': student_name,
                            'timestamp': timestamp,
                            'type': '学生报告',
                            'format': file_format,
                            'category': 'student',
                            'size': os.path.getsize(os.path.join(student_reports_dir, file))
                        })
    
    # 扫描内部报告
    internal_reports_dir = os.path.join('output', route_id, 'internal_reports')
    if os.path.exists(internal_reports_dir):
        files = os.listdir(internal_reports_dir)
        for file in files:
            if file.endswith(('.md', '.pdf')):
                # 解析文件名: timestamp_studentname_内部报告.format
                if '内部报告' in file:
                    parts = file.split('_')
                    if len(parts) >= 3:
                        timestamp = parts[0] + '_' + parts[1]
                        student_name = '_'.join(parts[2:]).replace('_内部报告.md', '').replace('_内部报告.pdf', '')
                        file_format = file.split('.')[-1]
                        
                        reports.append({
                            'file': file,
                            'student_name': student_name,
                            'timestamp': timestamp,
                            'type': '内部报告',
                            'format': file_format,
                            'category': 'internal',
                            'size': os.path.getsize(os.path.join(internal_reports_dir, file))
                        })
    
    # 按时间戳排序，最新的在前面
    reports.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return render_template('admin.html', route_id=route_id, questionnaires=questionnaires, reports=reports)

# 下载CSV文件（带路由编号）
@app.route('/admin/<route_id>/download/<filename>')
def download_csv(route_id, filename):
    """下载原始问卷CSV文件"""
    # 检查管理员权限
    if not check_admin_auth():
        return redirect(url_for('admin_login'))
    
    if not validate_route_id(route_id):
        flash("无效的路由编号", "error")
        return redirect(url_for('admin_routes'))
    
    file_path = os.path.join('original_questionnaire', route_id, secure_filename(filename))
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash("文件不存在", "error")
        return redirect(url_for('admin_panel', route_id=route_id))

# 重新分析问卷（带路由编号）
@app.route('/admin/<route_id>/reanalyze/<filename>')
def reanalyze_questionnaire(route_id, filename):
    """重新分析已提交的问卷"""
    # 检查管理员权限
    if not check_admin_auth():
        return redirect(url_for('admin_login'))
    
    if not validate_route_id(route_id):
        flash("无效的路由编号", "error")
        return redirect(url_for('admin_routes'))
    
    file_path = os.path.join('original_questionnaire', route_id, secure_filename(filename))
    if os.path.exists(file_path):
        try:
            analysis_engine.process_questionnaire(file_path, route_id)
            flash("问卷重新分析成功", "success")
        except Exception as e:
            app.logger.error(f"重新分析失败: {str(e)}")
            flash(f"重新分析失败: {str(e)}", "error")
    else:
        flash("文件不存在", "error")
    
    return redirect(url_for('admin_panel', route_id=route_id))

# 下载报告文件（带路由编号）
@app.route('/admin/<route_id>/download/report/<category>/<filename>')
def download_report(route_id, category, filename):
    """下载报告文件"""
    # 检查管理员权限
    if not check_admin_auth():
        return redirect(url_for('admin_login'))
    
    if not validate_route_id(route_id):
        flash("无效的路由编号", "error")
        return redirect(url_for('admin_routes'))
    
    # 安全检查：防止路径遍历攻击
    if '..' in filename or filename.startswith('/') or '\\' in filename:
        flash("非法文件名", "error")
        return redirect(url_for('admin_panel', route_id=route_id))
    
    if category == 'student':
        file_path = os.path.join('output', route_id, 'student_reports', filename)
    elif category == 'internal':
        file_path = os.path.join('output', route_id, 'internal_reports', filename)
    else:
        flash("无效的报告类型", "error")
        return redirect(url_for('admin_panel', route_id=route_id))
    
    # 确保文件路径在预期的目录内
    expected_dir = os.path.abspath(os.path.join('output', route_id, 'student_reports' if category == 'student' else 'internal_reports'))
    actual_path = os.path.abspath(file_path)
    
    if not actual_path.startswith(expected_dir):
        flash("非法文件路径", "error")
        return redirect(url_for('admin_panel', route_id=route_id))
    
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash("文件不存在", "error")
        return redirect(url_for('admin_panel', route_id=route_id))

# 管理员生成新路由
@app.route('/admin/generate_route', methods=['POST'])
def generate_new_route():
    """管理员生成新路由"""
    # 检查管理员权限
    if not check_admin_auth():
        return jsonify({'success': False, 'error': '未授权访问'}), 401
    
    try:
        # 生成新的路由ID
        route_id = generate_route_id()
        
        # 确保路由ID不重复（虽然概率极低）
        questionnaire_base_dir = 'original_questionnaire'
        max_attempts = 10
        attempts = 0
        
        while attempts < max_attempts:
            route_path = os.path.join(questionnaire_base_dir, route_id)
            if not os.path.exists(route_path):
                break
            route_id = generate_route_id()
            attempts += 1
        
        if attempts >= max_attempts:
            return jsonify({'success': False, 'error': '生成唯一路由ID失败，请重试'}), 500
        
        # 创建路由目录
        ensure_directories(route_id)
        
        # 返回生成的路由ID
        return jsonify({
            'success': True, 
            'route_id': route_id,
            'student_url': url_for('questionnaire', route_id=route_id, _external=True),
            'admin_url': url_for('admin_panel', route_id=route_id, _external=True)
        })
        
    except Exception as e:
        app.logger.error(f"生成新路由失败: {str(e)}")
        return jsonify({'success': False, 'error': f'生成失败: {str(e)}'}), 500

# 启动应用
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 4000))
    
    # 绑定到0.0.0.0使应用可以从外部访问
    # 生产环境中应确保设置了适当的安全措施
    app.run(
        host='0.0.0.0',  # 绑定到所有网络接口，允许远程访问
        port=port,
        debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    ) 