#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from dotenv import load_dotenv
import analysis_engine

def main():
    """
    直接使用analysis_engine模块处理问卷数据
    用法: python analyze_questionnaire.py <问卷文件路径>
    """
    # 加载环境变量（确保API密钥可用）
    load_dotenv()
    
    if len(sys.argv) < 2:
        print("用法: python analyze_questionnaire.py <问卷文件路径>")
        print("示例: python analyze_questionnaire.py original_questionnaire/20230101_学生姓名_questionnaire.csv")
        return 1
    
    # 获取问卷文件路径
    questionnaire_path = sys.argv[1]
    
    if not os.path.exists(questionnaire_path):
        print(f"错误: 文件 '{questionnaire_path}' 不存在")
        return 1
    
    print(f"正在处理问卷: {questionnaire_path}")
    print("开始分析...")
    
    try:
        # 使用analysis_engine直接处理问卷
        student_md, internal_md, student_pdf, internal_pdf = analysis_engine.process_questionnaire(questionnaire_path)
        
        print("\n分析和报告生成成功!")
        print(f"学生报告 (MD格式): {student_md}")
        print(f"学生报告 (PDF格式): {student_pdf}")
        print(f"内部报告 (MD格式): {internal_md}")
        print(f"内部报告 (PDF格式): {internal_pdf}")
        
        return 0
    
    except Exception as e:
        print(f"处理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 