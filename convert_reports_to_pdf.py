#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import glob
import argparse
from pathlib import Path

# 导入分析引擎中的转换函数
from analysis_engine import convert_markdown_to_pdf

def convert_single_file(md_file_path):
    """将单个Markdown文件转换为PDF"""
    print(f"正在处理文件: {md_file_path}")
    
    # 确保文件存在并且是Markdown文件
    if not os.path.exists(md_file_path):
        print(f"错误: 文件 '{md_file_path}' 不存在")
        return False
    
    if not md_file_path.lower().endswith('.md'):
        print(f"错误: 文件 '{md_file_path}' 不是Markdown文件")
        return False
    
    # 生成PDF输出路径
    pdf_path = md_file_path.replace('.md', '.pdf')
    
    try:
        # 读取Markdown内容
        with open(md_file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # 转换为PDF
        print(f"正在转换为PDF...")
        convert_markdown_to_pdf(md_content, pdf_path)
        print(f"转换完成: {pdf_path}")
        return True
    
    except Exception as e:
        print(f"转换失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def batch_convert_directory(directory, recursive=False):
    """批量转换目录中的所有Markdown文件"""
    # 使用递归标志决定是否递归搜索子目录
    pattern = os.path.join(directory, '**', '*.md') if recursive else os.path.join(directory, '*.md')
    
    # 获取所有Markdown文件
    files = list(glob.glob(pattern, recursive=recursive))
    
    if not files:
        print(f"在目录 '{directory}' 中未找到Markdown文件")
        return False
    
    print(f"找到 {len(files)} 个Markdown文件需要转换...")
    
    success_count = 0
    fail_count = 0
    
    for file_path in files:
        if convert_single_file(file_path):
            success_count += 1
        else:
            fail_count += 1
    
    print(f"\n批量转换完成!")
    print(f"成功: {success_count} 个文件")
    print(f"失败: {fail_count} 个文件")
    
    return success_count > 0

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="将Markdown报告转换为PDF格式")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-f", "--file", help="指定要转换的Markdown文件路径")
    group.add_argument("-d", "--directory", help="指定要批量处理的目录")
    
    parser.add_argument("-r", "--recursive", action="store_true", help="如果指定了目录，是否递归处理子目录")
    
    args = parser.parse_args()
    
    if args.file:
        # 处理单个文件
        return 0 if convert_single_file(args.file) else 1
    
    elif args.directory:
        # 批量处理目录
        if not os.path.isdir(args.directory):
            print(f"错误: '{args.directory}' 不是有效的目录")
            return 1
        
        return 0 if batch_convert_directory(args.directory, args.recursive) else 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 