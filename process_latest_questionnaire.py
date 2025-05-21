#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import glob
import argparse
from datetime import datetime
from pathlib import Path

# 导入分析引擎模块
import analysis_engine

def get_latest_questionnaire(directory="original_questionnaire"):
    """获取目录中最新的问卷文件"""
    files = glob.glob(os.path.join(directory, "*.csv"))
    if not files:
        return None
    
    # 按文件修改时间排序，获取最新的文件
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]

def process_specific_questionnaire(file_path):
    """处理指定的问卷文件"""
    print(f"正在处理问卷: {file_path}")
    
    try:
        # 使用分析引擎处理问卷
        student_md, internal_md, student_pdf, internal_pdf = analysis_engine.process_questionnaire(file_path)
        
        print("\n处理成功！")
        print(f"学生报告 (MD格式): {student_md}")
        print(f"学生报告 (PDF格式): {student_pdf}")
        print(f"内部报告 (MD格式): {internal_md}")
        print(f"内部报告 (PDF格式): {internal_pdf}")
        
        return True
    except Exception as e:
        print(f"处理失败: {str(e)}")
        return False

def batch_process_all_questionnaires(directory="original_questionnaire", pattern="*.csv"):
    """批量处理所有问卷文件"""
    print(f"正在批量处理 {directory} 目录中的所有 {pattern} 文件...")
    
    # 使用分析引擎批量处理
    results = analysis_engine.batch_process_questionnaires(directory, pattern)
    
    # 打印处理结果
    success_count = sum(1 for r in results if r['success'])
    fail_count = len(results) - success_count
    
    print(f"\n批量处理完成!")
    print(f"成功: {success_count} 个文件")
    print(f"失败: {fail_count} 个文件")
    
    if fail_count > 0:
        print("\n失败的文件:")
        for r in results:
            if not r['success']:
                print(f"- {r['file']}: {r.get('error', '未知错误')}")
    
    return results

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="处理问卷数据并生成MD和PDF格式的报告")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-f", "--file", help="指定要处理的问卷文件路径")
    group.add_argument("-l", "--latest", action="store_true", help="处理最新的问卷文件")
    group.add_argument("-a", "--all", action="store_true", help="处理所有问卷文件")
    
    args = parser.parse_args()
    
    if args.file:
        # 处理指定文件
        if not os.path.exists(args.file):
            print(f"错误: 文件 {args.file} 不存在")
            return 1
        
        process_specific_questionnaire(args.file)
    
    elif args.latest:
        # 处理最新文件
        latest_file = get_latest_questionnaire()
        if not latest_file:
            print("错误: 未找到任何问卷文件")
            return 1
        
        print(f"找到最新问卷文件: {latest_file}")
        process_specific_questionnaire(latest_file)
    
    elif args.all:
        # 批量处理所有文件
        batch_process_all_questionnaires()
    
    else:
        # 未指定任何选项，显示帮助信息
        parser.print_help()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 