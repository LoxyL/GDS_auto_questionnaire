import os
import pandas as pd
import openai
import json
from datetime import datetime
import glob
from pathlib import Path
from dotenv import load_dotenv

# 创建输出目录
def create_directories():
    """创建必要的文件夹"""
    os.makedirs("output/student_reports", exist_ok=True)
    os.makedirs("output/internal_reports", exist_ok=True)

# 读取问卷数据
def read_questionnaire_data():
    """从input文件夹读取最新的问卷数据文件"""
    input_dir = "input"
    files = glob.glob(f"{input_dir}/*.xlsx") + glob.glob(f"{input_dir}/*.csv")
    
    if not files:
        raise FileNotFoundError(f"在{input_dir}文件夹中找不到Excel或CSV文件")
    
    # 获取最新修改的文件
    latest_file = max(files, key=os.path.getmtime)
    
    # 根据文件类型读取数据
    if latest_file.endswith('.xlsx'):
        df = pd.read_excel(latest_file)
    else:
        df = pd.read_csv(latest_file)
    
    return df, os.path.basename(latest_file)

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

# 调用GPT-4o进行分析
def analyze_with_gpt4o(formatted_data, api_key, base_url, model="gpt-4o"):
    """使用GPT-4o分析问卷数据"""
    client = openai.OpenAI(api_key=api_key, base_url=base_url)
    
    analysis_prompt = f"""
    以下是一位学生填写的问卷调查。请帮我分析这个学生的情况。

    {formatted_data}

    请根据以上信息，分析并推断出以下内容：
    
    1. 性格分析：推断学生的MBTI性格类型，并给出理由。
    2. 购买意愿：分析学生购买教育产品的可能性和意愿，给出理由。
    3. 学习情况：
       - 当前学习水平和可能的分数区间
       - 目标或能考取的学校类型
       - 可能存在的学习问题
       - 学习态度和习惯评估
    4. 家庭/经济情况分析
    5. 其他重要观察
    
    请确保每一项分析都有具体的理由支持，直接引用问卷中的回答作为依据。
    
    另外，对于additional_observations字段，请提供针对性的学习建议，使用第二人称（"你"、"您"）直接对学生说话，例如"你应该尝试..."而不是"学生应该尝试..."。
    
    以JSON格式返回分析结果，格式如下：
    ```json
    {{
        "personality": {{
            "mbti": "具体的MBTI类型",
            "explanation": "分析理由，包括问卷中支持这个结论的具体回答"
        }},
        "purchase_intention": {{
            "level": "高/中/低",
            "explanation": "分析理由，引用问卷内容"
        }},
        "academic_status": {{
            "current_level": "当前学习水平评估",
            "score_range": "可能的分数区间",
            "target_schools": "可能考取的学校类型",
            "learning_issues": ["可能存在的学习问题1", "问题2"...],
            "learning_attitude": "学习态度评价",
            "learning_habits": "学习习惯评价",
            "explanation": "分析理由，引用问卷内容"
        }},
        "family_status": {{
            "economic_level": "经济情况评估",
            "family_support": "家庭对学习的支持程度",
            "explanation": "分析理由，引用问卷内容"
        }},
        "additional_observations": ["对学生的建议1（使用第二人称，如'你可以...'）", "建议2..."...],
        "recommended_products": ["推荐产品1", "产品2"...],
        "product_recommendation_reason": "推荐原因（使用第二人称）"
    }}
    ```
    """
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一位专业的教育顾问和心理分析师，擅长分析学生问卷并提供个性化教育建议。在给学生的建议中，请使用第二人称（'你'、'您'）直接对学生说话，而不是使用第三人称。"},
                {"role": "user", "content": analysis_prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        analysis_result = json.loads(response.choices[0].message.content)
        return analysis_result
    
    except Exception as e:
        print(f"GPT-4o API调用失败: {e}")
        # 返回一个基本的结构，表示分析失败
        return {
            "error": f"分析失败: {str(e)}",
            "raw_data": formatted_data
        }

# 生成学生报告
def generate_student_report(analysis, student_name):
    """生成面向学生的MD格式报告"""
    report = f"""# {student_name} 个人学习分析报告

## 整体情况

我们基于您提供的问卷内容，对您的学习情况和性格特点进行了分析，希望能为您提供有价值的参考。

## 性格分析

根据您的回答，我们推测您的性格可能偏向 **{analysis['personality']['mbti']}** 类型。

{analysis['personality']['explanation']}

## 学习情况分析

### 当前学习水平
{analysis['academic_status']['current_level']}

### 可能存在的学习问题
"""
    
    for issue in analysis['academic_status']['learning_issues']:
        report += f"- {issue}\n"
    
    report += f"""
### 学习态度与习惯
{analysis['academic_status']['learning_attitude']}

{analysis['academic_status']['learning_habits']}

## 学习建议

基于我们的分析，我们为您提供以下学习建议：

"""

    # 根据分析结果生成个性化学习建议
    if analysis.get('additional_observations'):
        for observation in analysis['additional_observations']:
            report += f"- {observation}\n"
    
    report += f"""
## 推荐产品

根据您的情况，我们推荐您考虑以下产品：

"""
    if analysis.get('recommended_products'):
        for product in analysis['recommended_products']:
            report += f"- {product}\n"
    
    report += f"""
推荐理由：{analysis.get('product_recommendation_reason', '基于您的学习风格和需求')}

---

*此报告由AI辅助生成，仅供参考。如需更详细的指导，请联系我们的教育顾问。*

报告生成日期：{datetime.now().strftime('%Y年%m月%d日')}
"""
    
    return report

# 生成内部报告
def generate_internal_report(analysis, student_name):
    """生成面向内部的MD格式报告"""
    report = f"""# {student_name} 学生情况内部分析报告

## 基本信息

- 学生姓名: {student_name}
- 报告日期: {datetime.now().strftime('%Y年%m月%d日')}

## 详细分析

### 1. 性格分析 (MBTI: {analysis['personality']['mbti']})

{analysis['personality']['explanation']}

### 2. 购买意愿分析

**意愿等级**: {analysis['purchase_intention']['level']}

**分析依据**: 
{analysis['purchase_intention']['explanation']}

### 3. 学习情况

- **当前水平**: {analysis['academic_status']['current_level']}
- **分数区间**: {analysis['academic_status']['score_range']}
- **目标学校类型**: {analysis['academic_status']['target_schools']}

**学习问题**:
"""
    
    for issue in analysis['academic_status']['learning_issues']:
        report += f"- {issue}\n"
    
    report += f"""
**学习态度**: {analysis['academic_status']['learning_attitude']}

**学习习惯**: {analysis['academic_status']['learning_habits']}

**分析依据**: 
{analysis['academic_status']['explanation']}

### 4. 家庭/经济情况

- **经济水平**: {analysis['family_status']['economic_level']}
- **家庭支持**: {analysis['family_status']['family_support']}

**分析依据**:
{analysis['family_status']['explanation']}

### 5. 其他重要观察
"""
    
    if analysis.get('additional_observations'):
        for observation in analysis['additional_observations']:
            report += f"- {observation}\n"
    
    report += f"""
## 产品推荐

基于以上分析，推荐以下产品：

"""
    if analysis.get('recommended_products'):
        for product in analysis['recommended_products']:
            report += f"- {product}\n"
    
    report += f"""
**推荐理由**: {analysis.get('product_recommendation_reason', '无具体理由提供')}

## 跟进建议

根据学生情况，建议以下跟进方式：
1. 针对性解决学生在{", ".join(analysis['academic_status']['learning_issues'][:2])}等方面的问题
2. 重点推广适合该学生{analysis['personality']['mbti']}性格特点的产品特性
3. 考虑该生家庭经济情况，合理设计价格策略

---

*本报告仅供内部使用，请勿向学生或家长展示完整内容*
"""
    
    return report

# 保存报告
def save_report(content, filename, report_type):
    """保存报告到指定目录"""
    directory = f"output/{report_type}_reports"
    filepath = os.path.join(directory, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath

# 主函数
def main():
    # 加载.env文件中的环境变量
    load_dotenv()
    
    # 1. 创建必要的目录结构
    create_directories()
    
    try:
        # 2. 读取问卷数据
        df, filename = read_questionnaire_data()
        
        # 提取学生姓名，如果没有特定的名字列，使用文件名作为学生标识
        student_name = None
        for name_column in ['姓名', '名字', '学生姓名', 'name', 'student_name']:
            if name_column in df.columns and not df[name_column].empty and pd.notna(df[name_column].iloc[0]):
                student_name = df[name_column].iloc[0]
                break
        
        if not student_name:
            # 从文件名中提取可能的学生名
            base_filename = os.path.splitext(filename)[0]
            student_name = base_filename.split('_')[-1] if '_' in base_filename else base_filename
        
        # 3. 格式化问卷数据
        formatted_data = format_questionnaire_data(df)
        
        # 4. 获取OpenAI API密钥
        base_url = os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1')
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            print("警告: 未找到OPENAI_API_KEY环境变量")
            print("请确保您在.env文件中设置了API密钥或通过环境变量设置")
            api_key = input("或者在此处输入您的OpenAI API密钥: ").strip()
            if not api_key:
                raise ValueError("需要OpenAI API密钥才能继续")
        
        # 获取可选的模型配置
        model = os.environ.get('MODEL', 'gpt-4o')
        
        # 5. 使用GPT-4o分析问卷数据
        print(f"正在分析{student_name}的问卷数据...")
        analysis_result = analyze_with_gpt4o(formatted_data, api_key, base_url, model)
        
        if 'error' in analysis_result:
            print(f"分析失败: {analysis_result['error']}")
            return
        
        # 6. 生成报告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 学生报告
        student_report = generate_student_report(analysis_result, student_name)
        student_filename = f"{timestamp}_{student_name}_学生报告.md"
        student_report_path = save_report(student_report, student_filename, "student")
        
        # 内部报告
        internal_report = generate_internal_report(analysis_result, student_name)
        internal_filename = f"{timestamp}_{student_name}_内部报告.md"
        internal_report_path = save_report(internal_report, internal_filename, "internal")
        
        print(f"分析完成!")
        print(f"学生报告已保存到: {student_report_path}")
        print(f"内部报告已保存到: {internal_report_path}")
        
        # 可选：保存原始分析结果
        analysis_path = os.path.join("output", f"{timestamp}_{student_name}_分析结果.json")
        with open(analysis_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2)
        
        print(f"原始分析数据已保存到: {analysis_path}")
        
    except Exception as e:
        print(f"程序执行出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 