import os
import json
import time
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from werkzeug.utils import secure_filename
import pandas as pd

# 导入问卷分析和报告生成功能
import analysis_engine

# 初始化Flask应用
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_change_in_production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上传文件大小为16MB

# 确保必要的目录存在
def ensure_directories():
    """创建必要的目录结构"""
    directories = [
        'original_questionnaire',
        'output/student_reports',
        'output/internal_reports',
        'templates',
        'static/css',
        'static/js',
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

# 初始化目录
ensure_directories()

# 主页
@app.route('/')
def index():
    """显示问卷填写页面"""
    return render_template('questionnaire.html')

# 问卷提交处理
@app.route('/submit', methods=['POST'])
def submit_questionnaire():
    """处理提交的问卷数据"""
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
        
        # 保存为CSV文件
        file_path = os.path.join('original_questionnaire', filename)
        df.to_csv(file_path, index=False)
        
        # 分析问卷并生成报告
        try:
            student_report_path, internal_report_path = analysis_engine.process_questionnaire(file_path)
            
            # 成功后重定向到结果页面
            return redirect(url_for('questionnaire_result', student_name=student_name, timestamp=timestamp))
        
        except Exception as e:
            app.logger.error(f"问卷分析失败: {str(e)}")
            flash(f"问卷已提交但分析失败: {str(e)}", "error")
            return redirect(url_for('index'))
    
    except Exception as e:
        app.logger.error(f"问卷提交处理错误: {str(e)}")
        flash(f"问卷提交失败: {str(e)}", "error")
        return redirect(url_for('index'))

# 查看学生报告
@app.route('/report/student/<timestamp>_<student_name>')
def view_student_report(timestamp, student_name):
    """显示学生报告"""
    # 查找最匹配的报告文件
    report_dir = 'output/student_reports'
    report_files = os.listdir(report_dir)
    matching_files = [f for f in report_files if f.startswith(f"{timestamp}_{student_name}")]
    
    if not matching_files:
        flash("未找到相关报告", "error")
        return redirect(url_for('index'))
    
    # 获取最新的报告文件
    report_file = sorted(matching_files)[-1]
    report_path = os.path.join(report_dir, report_file)
    
    # 读取报告内容
    with open(report_path, 'r', encoding='utf-8') as f:
        report_content = f.read()
    
    return render_template('student_report.html', 
                           student_name=student_name,
                           report_content=report_content,
                           timestamp=timestamp)

# 查看内部报告（需要管理员访问）
@app.route('/admin/report/internal/<timestamp>_<student_name>')
def view_internal_report(timestamp, student_name):
    """显示内部报告（仅限管理员）"""
    # 在实际项目中应添加管理员验证
    # if not is_admin():
    #     flash("无权访问此页面", "error")
    #     return redirect(url_for('index'))
    
    # 查找最匹配的报告文件
    report_dir = 'output/internal_reports'
    report_files = os.listdir(report_dir)
    matching_files = [f for f in report_files if f.startswith(f"{timestamp}_{student_name}")]
    
    if not matching_files:
        flash("未找到相关报告", "error")
        return redirect(url_for('index'))
    
    # 获取最新的报告文件
    report_file = sorted(matching_files)[-1]
    report_path = os.path.join(report_dir, report_file)
    
    # 读取报告内容
    with open(report_path, 'r', encoding='utf-8') as f:
        report_content = f.read()
    
    return render_template('internal_report.html', 
                           student_name=student_name,
                           report_content=report_content,
                           timestamp=timestamp)

# 问卷结果页面
@app.route('/result/<student_name>/<timestamp>')
def questionnaire_result(student_name, timestamp):
    """显示问卷提交后的结果页面"""
    return render_template('result.html', 
                           student_name=student_name,
                           timestamp=timestamp)

# 管理员面板
@app.route('/admin')
def admin_panel():
    """管理员控制面板，显示所有提交的问卷"""
    # 在实际项目中应添加管理员验证
    # if not is_admin():
    #     flash("无权访问此页面", "error")
    #     return redirect(url_for('index'))
    
    # 获取所有提交的问卷
    questionnaire_dir = 'original_questionnaire'
    questionnaires = []
    
    if os.path.exists(questionnaire_dir):
        files = os.listdir(questionnaire_dir)
        for file in files:
            if file.endswith('.csv'):
                # 从文件名提取信息
                parts = file.split('_')
                if len(parts) >= 3:
                    date_time = parts[0]
                    student_name = '_'.join(parts[1:-1])  # 处理名字中可能包含下划线的情况
                    
                    # 检查是否已生成报告
                    student_report_exists = any(f.startswith(f"{date_time}_{student_name}") for f in os.listdir('output/student_reports'))
                    internal_report_exists = any(f.startswith(f"{date_time}_{student_name}") for f in os.listdir('output/internal_reports'))
                    
                    questionnaires.append({
                        'file': file,
                        'student_name': student_name,
                        'timestamp': date_time,
                        'student_report_exists': student_report_exists,
                        'internal_report_exists': internal_report_exists
                    })
    
    # 按时间戳排序，最新的在前面
    questionnaires.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return render_template('admin.html', questionnaires=questionnaires)

# 下载CSV文件
@app.route('/admin/download/<filename>')
def download_csv(filename):
    """下载原始问卷CSV文件"""
    # 在实际项目中应添加管理员验证
    # if not is_admin():
    #     flash("无权访问此资源", "error")
    #     return redirect(url_for('index'))
    
    file_path = os.path.join('original_questionnaire', secure_filename(filename))
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash("文件不存在", "error")
        return redirect(url_for('admin_panel'))

# 重新分析问卷
@app.route('/admin/reanalyze/<filename>')
def reanalyze_questionnaire(filename):
    """重新分析已提交的问卷"""
    # 在实际项目中应添加管理员验证
    # if not is_admin():
    #     flash("无权执行此操作", "error")
    #     return redirect(url_for('index'))
    
    file_path = os.path.join('original_questionnaire', secure_filename(filename))
    if os.path.exists(file_path):
        try:
            student_report_path, internal_report_path = analysis_engine.process_questionnaire(file_path)
            flash("问卷重新分析成功", "success")
        except Exception as e:
            app.logger.error(f"重新分析失败: {str(e)}")
            flash(f"重新分析失败: {str(e)}", "error")
    else:
        flash("文件不存在", "error")
    
    return redirect(url_for('admin_panel'))

# 启动应用
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 433))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true') 