# 学生问卷分析与报告生成系统 (Web版)

这个系统是一个完整的Web应用，可以部署在服务器上，实现问卷的在线填写、自动分析和报告生成。系统可以根据学生填写的问卷，利用GPT-4o生成个性化的学习分析报告，包括面向学生的报告和面向内部使用的详细分析报告。

## 功能特点

- 提供在线问卷填写界面
- 自动处理提交的问卷数据
- 使用GPT-4o分析学生情况
- 推断学生的MBTI性格类型
- 评估学生的学习状况和潜在问题
- 分析购买教育产品的意愿
- 评估家庭支持和经济状况
- 生成个性化学习建议
- 后台自动生成两种不同的报告（学生版和内部版）
- 管理面板查看和管理所有问卷及报告
- 支持将报告转换为PDF格式
- 批量处理问卷分析功能
- 管理员可直接下载生成的报告文件

## 环境要求

- Python 3.6+
- Flask 2.0+
- OpenAI API密钥

## 安装依赖

```bash
pip install -r requirements.txt
```

## 快速开始

1. 克隆项目
   ```bash
   git clone <仓库地址>
   cd GDS_auto_questionnaire
   ```

2. 设置OpenAI API密钥
   创建`.env`文件并添加：
   ```
   OPENAI_API_KEY=your_api_key_here
   MODEL=gpt-4o  # 可选，默认为gpt-4o
   FLASK_DEBUG=True  # 开发环境设置
   SECRET_KEY=your_secret_key  # Flask会话密钥
   ADMIN_PASSWORD=your_admin_password  # 管理员密码，默认为admin123
   ```

3. 启动Web服务器
   ```bash
   # 开发环境
   python app.py
   
   # 生产环境
   gunicorn app:app -b 0.0.0.0:5000 -w 4
   ```

4. 访问问卷系统
   - 问卷填写: http://localhost:5000/
   - 管理员面板: http://localhost:5000/admin（需要密码）

## 项目结构

```
GDS_auto_questionnaire/
├── app.py                           # Flask应用主程序
├── analysis_engine.py               # 问卷分析引擎
├── analyze_questionnaire.py         # 单个问卷分析脚本
├── process_latest_questionnaire.py  # 处理最新问卷脚本
├── email_sender.py                  # 邮件发送功能
├── report_sender.py                 # 报告发送功能
├── convert_reports_to_pdf.py        # 报告转PDF功能
├── requirements.txt                 # 依赖列表
├── .env                            # 环境变量配置
├── .gitignore                      # Git忽略文件
├── README.md                       # 项目说明文档
├── analysis_engine.log             # 分析引擎日志
├── email_sender.log                # 邮件发送日志
├── original_questionnaire/         # 原始问卷数据
│   └── *.csv                       # CSV格式的问卷数据文件
├── output/                         # 生成的报告
│   ├── student_reports/            # 学生版报告
│   └── internal_reports/           # 内部版报告
├── static/                         # 静态资源
│   ├── css/                        # CSS样式
│   │   └── style.css               # 主样式文件
│   └── js/                         # JavaScript脚本
│       └── form-validation.js      # 表单验证脚本
├── templates/                      # HTML模板
│   ├── questionnaire.html          # 问卷页面
│   ├── result.html                 # 提交成功页面
│   └── admin.html                  # 管理员面板
├── __pycache__/                    # Python缓存文件
└── venv/                           # 虚拟环境目录
```

## 使用指南

### 学生使用流程

1. 访问系统首页填写问卷
2. 提交问卷后查看提交成功页面
3. 系统后台自动分析并生成报告

### 管理员使用流程

1. 访问管理员面板 (http://localhost:5000/admin)
2. 输入管理员密码进行身份验证
3. 查看所有提交的问卷
4. 查看所有生成的报告文件列表
5. 直接点击下载学生报告或内部报告（支持MD和PDF格式）
6. 下载原始问卷数据
7. 必要时重新分析问卷
8. 完成后可以登出系统

### 批量处理和自动化

系统提供多个脚本用于批量处理和自动化操作：

- `analyze_questionnaire.py`: 分析单个问卷文件
- `process_latest_questionnaire.py`: 自动处理最新提交的问卷
- `email_sender.py`: 发送邮件功能
- `report_sender.py`: 自动发送分析报告
- `convert_reports_to_pdf.py`: 将HTML报告转换为PDF格式

## 问卷内容

问卷包含以下几个部分：
- 基本信息（姓名、年龄、性别、年级等）
- 学习情况（擅长科目、薄弱科目、成绩情况等）
- 性格与自我认知
- 学习习惯与挑战
- 家庭支持与教育投入
- 其他信息

## 报告内容

### 学生报告

学生报告包括：
- 性格分析
- 学习情况评估
- 存在的学习问题
- 学习态度与习惯分析
- 个性化学习建议
- 推荐产品

### 内部报告

内部报告包括：
- 详细的性格分析
- 购买意愿评估
- 学习状况详细分析
- 家庭和经济情况
- 产品推荐和理由
- 跟进建议

## 自定义与扩展

- 修改`templates/questionnaire.html`可以自定义问卷问题
- 调整`analysis_engine.py`中的分析逻辑和提示词
- 编辑报告模板以适应不同的需求
- 使用`convert_reports_to_pdf.py`自定义PDF报告格式
- 通过管理员面板直接管理和下载所有报告文件

## 安全配置

### 管理员密码设置

系统默认管理员密码为 `admin123`。**生产环境中必须修改此密码！**

设置方法：
1. 通过环境变量：
   ```bash
   export ADMIN_PASSWORD=your_secure_password
   ```

2. 在 `.env` 文件中：
   ```
   ADMIN_PASSWORD=your_secure_password
   ```

### 访问控制

- 管理员面板受密码保护
- 登录状态通过加密的cookie维持，有效期24小时
- 所有管理员功能（下载、重新分析等）都需要身份验证
- 提供安全的登出功能

## 注意事项

- 确保服务器安全配置，特别是管理员面板已具备密码保护
- **生产环境中务必修改默认管理员密码**
- API调用可能产生费用，请注意控制使用频率
- 分析结果仅供参考，不应替代专业教育顾问的建议
- 为保护隐私，建议使用HTTPS协议并实施适当的数据保护措施
- PDF转换功能可能需要额外的系统依赖
- 管理员面板提供直接的报告文件下载功能，无需邮件发送
- 管理员登录状态会在24小时后自动过期

## 自定义与扩展

- 修改`templates/questionnaire.html`可以自定义问卷问题
- 调整`analysis_engine.py`中的分析逻辑和提示词
- 编辑报告模板以适应不同的需求
- 使用`convert_reports_to_pdf.py`自定义PDF报告格式
- 通过管理员面板直接管理和下载所有报告文件 