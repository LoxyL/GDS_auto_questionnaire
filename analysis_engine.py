import os
import pandas as pd
import openai
import json
from datetime import datetime
import glob
from pathlib import Path
from dotenv import load_dotenv
import markdown
import weasyprint
import logging
import re

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("analysis_engine.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 初始化环境变量
load_dotenv()

# 创建输出目录
def create_directories(route_id=None):
    """创建必要的文件夹"""
    if route_id:
        # 为特定路由创建目录
        os.makedirs(f"output/{route_id}/student_reports", exist_ok=True)
        os.makedirs(f"output/{route_id}/internal_reports", exist_ok=True)
        os.makedirs(f"original_questionnaire/{route_id}", exist_ok=True)
        logger.info(f"为路由 {route_id} 创建输出目录完成")
    else:
        # 创建基础目录（向后兼容）
        os.makedirs("output/student_reports", exist_ok=True)
        os.makedirs("output/internal_reports", exist_ok=True)
        os.makedirs("original_questionnaire", exist_ok=True)
        logger.info("创建输出目录完成")

# 将问卷数据转换为易于阅读的格式
def format_questionnaire_data(df):
    """将问卷数据格式化为适合AI分析的文本"""
    formatted_data = "问卷调查内容：\n\n"
    
    for index, row in df.iterrows():
        for column in df.columns:
            if pd.notna(row[column]):
                formatted_data += f"问题: {column}\n"
                formatted_data += f"回答: {row[column]}\n\n"
    
    return formatted_data

# 直接生成报告
def generate_reports(formatted_data, student_name, api_key, base_url, model="gpt-4o"):
    """使用GPT-4o直接生成学生报告和内部报告"""
    logger.info(f"开始为{student_name}生成报告...")
    client = openai.OpenAI(api_key=api_key, base_url=base_url)
    
    prompt = f"""
    以下是一位学生填写的问卷调查。请基于这些信息生成两份报告：学生个人报告和内部营销报告。

    学生姓名：{student_name}
    
    {formatted_data}
    
    请生成两份报告：
    
    1. 学生个人报告：使用第二人称（"你"、"您"）直接对学生说话。包括性格分析、学习情况分析、学习建议和推荐产品等。格式自由，但需确保内容对学生有帮助和指导意义。
    
    2. 内部营销报告：使用第三人称（"该学生"、"他/她"）描述学生，严格按照以下格式：
    
# 内部营销报告要求：

第一部分：学生基本信息表  
- 输出为 Markdown 表格，列出以下字段：学生姓名｜性别｜所在省市｜学校类型｜年级｜户口类型｜家庭年收入区间｜目标大学及专业｜自我评估成绩水平｜MBTI 性格｜每日自主学习时长｜课外辅导方式｜家长参与度  
- 每个字段对应表格一列。

第二部分：营销建议（共约200–250字）  
请置顶，包含四小节，每节用二级标题，要求如下：  
1. 推荐产品（约200–300字）  
   - 指出首选产品类型及核心推荐理由（需结合性格与行为特征，可供选择的只有2个选择：1V1课程或计划类产品）。  
2. 沟通话术风格（约200–300字）  
   - 指定1~2种话术风格（如"理性目标型""陪伴式""情感激励型"），并给出一句示例开场白和后续话题的方向说明。  
3. 话题切入（约400–600字）  
   - 列出 2–3 个最有效的话题切入点。  
4. 价值点强调（约400–600字）  
   - 给出 3–4 个该学生最看重的价值主张。

第三部分：五维度深度分析  
对下列五个维度分别输出：  
- 结果分析（约100字）：用一段话总结该维度的核心洞察。  
- 数据来源及说明（约100–300字）：注明使用了哪些 JSON 字段（题号或字段名）支撑该结论。

五个维度依次为：  
1. 学生性格  
2. 家庭条件及教育投入  
3. 学习意愿  
4. 学习天赋  
5. 学习成绩

输出要求  
- 全文使用简体中文，语言自然流畅、逻辑严谨。  
- 必须在"数据来源及说明"中引用具体的问卷字段。  

具体的示例：
```plaintext
# 内部营销报告-代代

## 【第一部分：学生基本信息表】

| 属性         | 详情                         |
|--------------|-----------------------------|
| 学生姓名     | 代代                        |
| 性别         | 未提供                      |
| 所在省市     | 湖北                        |
| 学校类型     | 区重点高中                  |
| 年级         | 高二                        |
| 户口类型     | 城镇                        |
| 家庭年收入区间 | 未估计                      |
| 目标大学及专业 | 不清楚                     |
| 自我评估成绩水平 | 中等水平（31%-60%）       |
| MBTI 性格    | ESFP                        |
| 每日自主学习时长 | 30分钟-1小时               |
| 课外辅导方式 | 无                          |
| 家长参与度   | 很少干涉，完全自主管理       |

## 【第二部分：营销建议】

### 1. 推荐产品：
建议首推线上**1对1辅导**。

- **满足性格特点**：ESFP 类型的代代外向活泼,更喜欢与老师互动，即时反馈，单向视频课或纯规训课容易让他产生厌倦；1对1 模式可随时提问，增强节奏，更能激发学习积极性。
- **补充执行短板**：他自主学习时间有限，缺乏持续规划，一对一辅导中辅导老师可为他做"当下打卡+课后督促"，帮助他按节点完成学习任务，避免拖延。
- **提高续费意愿**：互动式教学让他感受到陪伴与成就感，学习效果更直观，家长更愿意持续投入；相较于规训课的单一内容，他可在1对1中体验到多样化教学方案，续费黏性更高。

### 2. 沟通话术风格：
代代属于 ESFP，外向且追求新鲜感，交流中应以陪伴式情感+轻松活泼为主。开场可这样说：

> 1. "代代同学，听说你平时学习节奏快，但有时候会卡在一些小难题上？没关系，我和你一起，随时帮你搞定困难，还能带你玩转各种学习小技巧，让每一次刷题都像闯关游戏一样——有问题马上陪你一起攻克！"

> **"语言要真诚、有温度，采用'我们''一起''陪伴'等词，让他感觉到不是上课，而是有人在身边督促并支持。避免过度堆砌教材式的描述，增加入一些日常生活的比喻（比如'像打游戏过关一样'），承接他的兴趣点，增强信任与使用体验预期。"**

### 3. 话题切入：
- **目标与愿景**  
  先聊聊他对"大城市之旅"的向往：

  > - "你提到希望通过学习去大城市中见识风景和机会，能具体分享一下最想体验的事吗？是想去科技展、还是想在大厦的馆深夜自习？"

  通过这种开放式提问，引导他把"见识"转化为学习动力。接着结合关联到课程："我们的1对1辅导不仅帮你提高分数，每次课后还会给你推荐大城市名校学长笔记和学习攻略，让你一步步贴近理想的未来生活。"

### 4. 学习难点与学科兴趣
针对他"理科好，物理尤佳"的优势，讨论具体痛点：
> - "你在物理哪部分最有成就感？力学、光学还是电学？有没有遇到特别头疼的题型？"

> **"让他描述真实感受后，示范如何在1对1中进行'题型拆解+公式归纳'，再给出一个小练习，让他当场体验老师讲解与互动的效果。"**

### 5. 时间管理与课外利用
由于每日自习时间仅30–60分钟，可探讨如何在碎片化时间高效学习：

> - "下午放学后到晚上自习开始之前的这段半小时，你最习惯做什么？如果把它用来背公式或刷错题，你会愿意试试我们的'5分钟提分法'吗？"

> - **"介绍课程中专门设计的'日常打卡+错题本'功能，说明每个碎片时段都能有实效，让他觉得课程设计贴合自己的生活节奏。"**

通过以上具体讨论方向，销售人员可以：
- **a. 记录关键词**：大城市、物理、碎片化时间、游戏化闯关；
- **b. 提供设计演示**：准备对应场景的教学演示或案例分享；
- **c. 动态调整话术**：随时将他的回复与产品功能一一对应，做到"听我所需，给我所想"。

### 价值点强调：
- **个性化学习计划与监督**  
  我们会根据代代的学科偏好和目标，将每周学习计划细分到每日任务，并由专属老师实时跟进完成情况；
- **灵活在线资源**  
  除1对1主课外，还可免费使用为 ESFP 设计的"学习游戏包"、互动直播答疑，让学习形式更丰富、有趣；
- **增强独立解决问题能力**  
  老师不仅讲解答案，还会教授"解题思路模板"与"逻辑拆解法"，帮助代代在面对新题时能快速上手，不再依赖别人；
- **打通升学与职业通道**  
  课程结束后，代代有机会获得校内竞赛、夏令营或名校学长一对一指导资源推荐，为未来申请名校和职业发展奠定基础。

以上四大价值点，可配合具体案例（如某学员在两个月内从年级中等提升至前10%）和功能演示，增强说服力。
```

```plaintext
## 【第三部分：五维度深度分析】

### 学生性格

**结果分析**：小潘是INFP类型，追求内心和谐，喜欢依自己的方式进行自发性学习，可能会对现实的高强度和标准化教学缺乏兴趣，需要自主和价值导向的学习环境来支持他的成长。

**数据来源及说明**：

- 使用的字段：MBTI性格、最高效学习经历
- 说明：MBTI指明了他注重内心世界和情感的特征，而回答最高效学习经历时的低效表现说明他的学习可能缺乏适合其风格的方法。

### 家庭条件及教育投入

**结果分析**：他的家庭对学业的参与度较低，但提供了课外辅导班和家教等资源，因此小潘拥有自主学习的空间，但选课的方向和效果可能会受到限制。

**数据来源及说明**：

- 使用的字段：家长对学业参与度、家庭学习支持
- 说明：数据表明，他的父母可能强调自我管理的能力建设，也为他提供了外部教育资源支持。

### 学习意愿

**结果分析**：学习意愿不够强烈，对目标大学和专业的明确度也不足，体现了一种被动和随意的学习态度，亟需重新焕发动力。

**数据来源及说明**：

- 使用的字段：目标大学及专业、学习动力来源、学习现状总结
- 说明：描述显示了他对未来不确定感和当下学习的疲倦，表明需要外界刺激来激发内在学习动机。

### 学习天赋

**结果分析**：对于文科较有天赋，但理科和数学成绩较弱，需要更多关注在这些学科上寻找方法和节奏感。

**数据来源及说明**：

- 使用的字段：优势科目类型、最高效学习经历
- 说明：优势科目类型给出了学科偏好，最高效学习经历的低效表现提示可能在理科思维能力上遇到较大挑战。

### 学习成绩

**结果分析**：目前成绩水平居于后61%-90%区间，有努力提升的意愿，但缺乏计划和方法。

**数据来源及说明**：

- 使用的字段：自我评估成绩水平、每日自主学习时长、错题处理习惯
- 说明：自评成绩水平与学习时长揭示了他所处的学业状态，答案中显现出需要在学习策略上进行调整。
```

    """
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一位专业的教育顾问和心理分析师，擅长分析学生问卷并提供个性化教育建议。在给学生的报告中，请使用第二人称；在内部报告中，请使用第三人称描述学生。请严格按照要求的格式生成内部报告，并确保无序列表和有序列表格式正确，每个列表项前后都有空行。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000
        )
        
        full_response = response.choices[0].message.content
        logger.info("报告生成完成，开始分割报告内容")
        
        # 分割两个报告
        if "内部营销报告" in full_response and "学生个人报告" in full_response:
            parts = full_response.split("内部营销报告")
            student_report = parts[0].replace("学生个人报告", "").strip()
            internal_report = "内部营销报告" + parts[1].strip()
        else:
            # 尝试其他可能的分隔方式
            markers = ["###", "---", "===", "学生个人报告", "内部营销报告", "内部报告"]
            for marker in markers:
                if full_response.count(marker) >= 2:
                    parts = full_response.split(marker)
                    if len(parts) >= 3:  # 至少有两个分隔符
                        student_report = parts[1].strip()
                        internal_report = parts[2].strip()
                        break
            else:
                # 如果没找到合适的分隔符，进行备用分割
                half_point = len(full_response) // 2
                student_report = full_response[:half_point]
                internal_report = full_response[half_point:]
                
                # 检查并修正内部报告，确保格式符合要求
                if "该学生名为" not in internal_report:
                    internal_report = f"该学生名为{student_name}，根据其问卷结果，给出以下五个维度的分析，并将营销建议附在其后：\n\n" + internal_report
        
        return student_report, internal_report
    
    except Exception as e:
        logger.error(f"报告生成失败: {e}")
        
        # 如果是端点错误，尝试使用默认端点
        if "ENDPOINT ERROR" in str(e):
            logger.info("检测到端点错误，尝试使用默认OpenAI API端点...")
            try:
                default_client = openai.OpenAI(api_key=api_key)
                response = default_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "你是一位专业的教育顾问和心理分析师，擅长分析学生问卷并提供个性化教育建议。在给学生的报告中，请使用第二人称；在内部报告中，请使用第三人称描述学生。请严格按照要求的格式生成内部报告，并确保无序列表和有序列表格式正确。"},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=4000
                )
                
                full_response = response.choices[0].message.content
                
                # 分割两个报告
                if "内部营销报告" in full_response and "学生个人报告" in full_response:
                    parts = full_response.split("内部营销报告")
                    student_report = parts[0].replace("学生个人报告", "").strip()
                    internal_report = "内部营销报告" + parts[1].strip()
                else:
                    # 备用分割方式
                    half_point = len(full_response) // 2
                    student_report = full_response[:half_point]
                    internal_report = full_response[half_point:]
                
                return student_report, internal_report
                
            except Exception as retry_e:
                logger.error(f"使用默认API端点也失败: {retry_e}")
                raise
        
        # 返回基本的报告，表示生成失败
        student_report = f"# {student_name} 个人学习分析报告\n\n报告生成失败，请稍后重试。"
        internal_report = f"# {student_name} 学生情况内部分析报告\n\n报告生成失败，请稍后重试。"
        return student_report, internal_report

# 将Markdown转换为PDF
def convert_markdown_to_pdf(markdown_content, pdf_path):
    """将Markdown内容转换为PDF并保存"""
    logger.info(f"开始转换Markdown为PDF: {pdf_path}")
    # 预处理Markdown内容，确保列表项格式正确
    lines = markdown_content.split('\n')
    processed_lines = []
    
    # 列表项标记的正则表达式
    list_marker_regex = re.compile(r'^\s*[-*+]\s+|\s*\d+\.\s+')
    
    # 记录上一行的缩进级别和列表状态
    prev_indent = 0
    in_list = False
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        # 空行处理
        if not line_stripped:
            processed_lines.append(line)
            continue
            
        # 当前行缩进
        indent_level = len(line) - len(line.lstrip())
        
        # 检查是否为列表项（无序列表或有序列表）
        is_list_item = bool(list_marker_regex.match(line_stripped))
        
        # 列表处理逻辑
        if is_list_item:
            # 如果这是新列表的开始，添加一个空行
            if not in_list:
                if processed_lines and processed_lines[-1].strip():
                    processed_lines.append('')
                in_list = True
            
            # 处理缩进变化（嵌套列表的情况）
            if in_list and indent_level > prev_indent and i > 0:
                # 确保嵌套列表前有一个额外的空行
                if processed_lines[-1].strip():
                    processed_lines.append('')
            
            processed_lines.append(line)
            prev_indent = indent_level
        else:
            # 如果离开列表，添加空行
            if in_list:
                if processed_lines and processed_lines[-1].strip():
                    processed_lines.append('')
                in_list = False
            
            processed_lines.append(line)
            prev_indent = 0
    
    processed_markdown = '\n'.join(processed_lines)
    
    # 将Markdown转换为HTML，添加扩展以支持嵌套列表
    html_content = markdown.markdown(
        processed_markdown, 
        extensions=['tables', 'fenced_code', 'nl2br', 'sane_lists', 'attr_list']
    )
    
    # 添加基本样式的HTML封装，使用支持中文的字体
    styled_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>学习分析报告</title>
        <style>
            @font-face {{
                font-family: 'WQY';
                src: local('WenQuanYi Micro Hei'), local('WenQuanYi Zen Hei');
            }}
            
            body {{
                font-family: 'WQY', 'WenQuanYi Micro Hei', 'WenQuanYi Zen Hei', Arial, sans-serif;
                line-height: 1.6;
                margin: 2cm;
            }}
            h1, h2, h3 {{
                font-family: 'WQY', 'WenQuanYi Micro Hei', 'WenQuanYi Zen Hei', Arial, sans-serif;
                color: #333;
            }}
            h1 {{
                font-size: 24pt;
                text-align: center;
                margin-bottom: 1.5cm;
            }}
            h2 {{
                font-size: 18pt;
                border-bottom: 1px solid #ddd;
                padding-bottom: 0.3cm;
                margin-top: 1cm;
            }}
            h3 {{
                font-size: 14pt;
                margin-top: 0.8cm;
            }}
            p {{
                text-align: justify;
                font-family: 'WQY', 'WenQuanYi Micro Hei', 'WenQuanYi Zen Hei', Arial, sans-serif;
            }}
            ul, ol {{
                margin-left: 1cm;
                padding-left: 1cm;
            }}
            ul ul, ol ol, ul ol, ol ul {{
                margin-left: 0;
                padding-left: 1.5cm;
            }}
            /* 多级嵌套列表的样式 */
            ul ul ul, ol ol ol, ul ul ol, ul ol ul, ol ul ul, ol ol ul, ol ul ol, ul ol ol {{
                padding-left: 2cm;
            }}
            li {{
                font-family: 'WQY', 'WenQuanYi Micro Hei', 'WenQuanYi Zen Hei', Arial, sans-serif;
                margin-bottom: 0.3cm;
                padding-left: 0.5cm;
                position: relative;
            }}
            /* 列表标记样式 */
            ul > li {{
                list-style-type: disc;
            }}
            ul > li > ul > li {{
                list-style-type: circle;
            }}
            ul > li > ul > li > ul > li {{
                list-style-type: square;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 1cm 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
                font-family: 'WQY', 'WenQuanYi Micro Hei', 'WenQuanYi Zen Hei', Arial, sans-serif;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            .footer {{
                text-align: center;
                font-size: 9pt;
                color: #777;
                margin-top: 2cm;
                font-family: 'WQY', 'WenQuanYi Micro Hei', 'WenQuanYi Zen Hei', Arial, sans-serif;
            }}
        </style>
    </head>
    <body>
        {html_content}
        <div class="footer">
            <p>此报告由AI辅助生成，仅供参考。</p>
        </div>
    </body>
    </html>
    """
    
    # 使用WeasyPrint将HTML转换为PDF
    try:
        weasyprint.HTML(string=styled_html).write_pdf(pdf_path)
        logger.info(f"PDF报告已保存到: {pdf_path}")
    except Exception as e:
        logger.error(f"生成PDF时发生错误: {e}")
        # 如果出错，保存HTML文件用于调试
        html_path = pdf_path.replace('.pdf', '_debug.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(styled_html)
        logger.info(f"已保存调试用HTML到: {html_path}")
        raise
    
    return pdf_path

# 保存报告
def save_report(content, filename, report_type, route_id=None):
    """保存报告到指定目录，同时保存MD和PDF格式"""
    if route_id:
        directory = f"output/{route_id}/{report_type}_reports"
    else:
        directory = f"output/{report_type}_reports"
    
    # 确保目录存在
    os.makedirs(directory, exist_ok=True)
    
    md_filepath = os.path.join(directory, filename)
    
    # 保存Markdown格式
    with open(md_filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    try:
        # 尝试同时保存PDF格式
        pdf_filename = filename.replace('.md', '.pdf')
        pdf_filepath = os.path.join(directory, pdf_filename)
        convert_markdown_to_pdf(content, pdf_filepath)
    except Exception as e:
        logger.error(f"PDF生成失败，但Markdown报告已保存成功: {e}")
        pdf_filepath = None
    
    return md_filepath, pdf_filepath

# 处理问卷的主函数
def process_questionnaire(questionnaire_file_path, route_id=None):
    """
    处理单个问卷文件，生成分析报告
    
    Args:
        questionnaire_file_path: 问卷CSV文件路径
        route_id: 路由编号，用于组织文件结构
        
    Returns:
        tuple: (学生报告路径, 内部报告路径, 学生PDF报告路径, 内部PDF报告路径)
    """
    # 确保目录存在
    create_directories(route_id)
    
    try:
        # 读取问卷数据
        if questionnaire_file_path.endswith('.xlsx'):
            df = pd.read_excel(questionnaire_file_path)
        else:
            df = pd.read_csv(questionnaire_file_path)
        
        # 从文件名或数据中提取学生姓名
        filename = os.path.basename(questionnaire_file_path)
        student_name = None
        
        # 尝试从DataFrame中获取姓名
        for name_column in ['姓名', '名字', '学生姓名', 'name', 'student_name']:
            if name_column in df.columns and not df[name_column].empty and pd.notna(df[name_column].iloc[0]):
                student_name = df[name_column].iloc[0]
                break
        
        # 如果在DataFrame中找不到，尝试从文件名提取
        if not student_name:
            parts = filename.split('_')
            if len(parts) >= 2:
                student_name = parts[1]  # 假设文件名格式为: timestamp_学生姓名_questionnaire.csv
            else:
                student_name = "unknown_student"
        
        # 格式化问卷数据
        formatted_data = format_questionnaire_data(df)
        
        # 获取OpenAI API配置
        base_url = os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1')
        api_key = os.environ.get('OPENAI_API_KEY')
        
        if not api_key:
            raise ValueError("未找到OPENAI_API_KEY环境变量，请在.env文件中设置API密钥")
        
        # 获取可选的模型配置
        model = os.environ.get('MODEL', 'gpt-4o')
        
        # 直接生成两份报告
        logger.info(f"正在为{student_name}生成报告...")
        student_report, internal_report = generate_reports(formatted_data, student_name, api_key, base_url, model)
        
        # 生成报告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存学生报告
        student_filename = f"{timestamp}_{student_name}_学生报告.md"
        student_report_path, student_pdf_path = save_report(student_report, student_filename, "student", route_id)
        
        # 保存内部报告
        internal_filename = f"{timestamp}_{student_name}_内部报告.md"
        internal_report_path, internal_pdf_path = save_report(internal_report, internal_filename, "internal", route_id)
        
        logger.info(f"报告生成完成!")
        logger.info(f"学生报告已保存到: {student_report_path} (MD格式)")
        logger.info(f"学生报告已保存到: {student_pdf_path} (PDF格式)")
        logger.info(f"内部报告已保存到: {internal_report_path} (MD格式)")
        logger.info(f"内部报告已保存到: {internal_pdf_path} (PDF格式)")
        
        return student_report_path, internal_report_path, student_pdf_path, internal_pdf_path
        
    except Exception as e:
        logger.error(f"问卷处理出错: {e}")
        import traceback
        traceback.print_exc()
        raise Exception(f"问卷处理失败: {str(e)}")

# 批量处理问卷
def batch_process_questionnaires(directory="original_questionnaire", pattern="*.csv", route_id=None):
    """批量处理目录中的所有问卷文件"""
    if route_id:
        # 处理特定路由的问卷
        directory = os.path.join(directory, route_id)
    
    files = glob.glob(os.path.join(directory, pattern))
    results = []
    
    logger.info(f"开始批量处理问卷，共找到{len(files)}个文件")
    
    for file in files:
        try:
            student_report, internal_report, student_pdf, internal_pdf = process_questionnaire(file, route_id)
            results.append({
                "file": file,
                "success": True,
                "student_report": student_report,
                "internal_report": internal_report,
                "student_pdf": student_pdf,
                "internal_pdf": internal_pdf
            })
        except Exception as e:
            logger.error(f"处理问卷{file}失败: {e}")
            results.append({
                "file": file,
                "success": False,
                "error": str(e)
            })
    
    # 生成批处理结果报告
    success_count = sum(1 for result in results if result['success'])
    failure_count = len(results) - success_count
    
    summary = (f"问卷处理完成报告\n"
               f"处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
               f"路由编号: {route_id if route_id else '默认'}\n"
               f"总计问卷: {len(results)}\n"
               f"成功处理: {success_count}\n"
               f"处理失败: {failure_count}\n\n"
               f"详细结果:\n")
    
    for result in results:
        if result['success']:
            summary += f"✓ {os.path.basename(result['file'])} - 成功\n"
        else:
            summary += f"✗ {os.path.basename(result['file'])} - 失败: {result['error']}\n"
    
    # 保存处理报告
    if route_id:
        report_dir = f"output/{route_id}"
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, f"batch_processing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    else:
        report_path = os.path.join("output", f"batch_processing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(summary)
    
    logger.info(f"批量处理完成，结果已保存到{report_path}")
    return results

# 如果直接运行此脚本
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='问卷自动处理工具')
    parser.add_argument('--file', help='单个问卷文件路径')
    parser.add_argument('--dir', default='original_questionnaire', help='批量处理的问卷目录')
    parser.add_argument('--pattern', default='*.csv', help='文件匹配模式，如*.csv或*.xlsx')
    parser.add_argument('--route', help='路由编号，用于组织文件结构')
    args = parser.parse_args()
    
    # 确保环境变量已加载
    if not os.environ.get('OPENAI_API_KEY'):
        print("错误：未找到OPENAI_API_KEY环境变量")
        print("请确保已创建.env文件并设置必要的环境变量")
        example_env = """
        # OpenAI API配置
        OPENAI_API_KEY=你的OpenAI密钥
        OPENAI_BASE_URL=https://api.openai.com/v1
        MODEL=gpt-4o
        """
        print(f"参考.env文件内容:\n{example_env}")
        exit(1)
    
    # 处理命令行参数
    if args.file:
        # 处理单个文件
        try:
            process_questionnaire(args.file, args.route)
            print(f"文件处理完成: {args.file}")
        except Exception as e:
            print(f"处理失败: {e}")
    else:
        # 批量处理
        batch_process_questionnaires(args.dir, args.pattern, args.route) 