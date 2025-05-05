import os
import re
import argparse
from datetime import datetime
from dotenv import load_dotenv
from label_studio_sdk.label_interface import LabelInterface
from label_studio_sdk.client import LabelStudio

def parse_time(time_str):
    """将时间字符串转换为秒数"""
    h, m, s = time_str.split(':')
    return float(h) * 3600 + float(m) * 60 + float(s)

def parse_subtitle_line(line):
    """解析字幕行，返回开始时间、结束时间和文本"""
    pattern = r'Dialogue: \d+,(\d+:\d+:\d+\.\d+),(\d+:\d+:\d+\.\d+),([^,]+),,.*?,,(.*)'
    match = re.match(pattern, line)
    if match:
        start_time, end_time, style, text = match.groups()
        # 移除文本中的样式标签
        text = re.sub(r'\{[^}]*\}', '', text)
        return {
            'start': parse_time(start_time),
            'end': parse_time(end_time),
            'text': text.strip()
        }
    return None

def read_subtitle_file(file_path, language='IN_CH_EP13-CHS'):
    """读取字幕文件并返回指定语言的字幕"""
    subtitles = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('Dialogue:') and language in line:
                subtitle = parse_subtitle_line(line)
                if subtitle:
                    subtitles.append(subtitle)
    return subtitles

def create_label_studio_annotation(subtitles, task_id):
    """创建 Label Studio 标注"""
    load_dotenv('.env.prod')
    
    ls = LabelStudio(
        base_url=os.environ['LABEL_STUDIO_URL'],
        api_key=os.environ['LABEL_STUDIO_TOKEN'],
    )
    
    # 为每个字幕创建时间戳标注
    results = []
    for subtitle in subtitles:
        result = {
            'from_name': 'transcription',
            'to_name': 'audio',
            'type': 'textarea',
            'value': {
                'start': subtitle['start'],
                'end': subtitle['end'],
                'text': [subtitle['text']],
                "channel": 0,
            }
        }
        results.append(result)
    ls.annotations.create(id=task_id, result=results)

def main():
    # 设置命令行参数
    parser = argparse.ArgumentParser(description='将字幕文件导入到 Label Studio')
    parser.add_argument('sub_file', help='字幕文件路径')
    parser.add_argument('lang', help='字幕语言代码 (例如: IN_CH_EP13-CHS, IN_JP_EP13)')
    parser.add_argument('--task-id', type=int, help='Label Studio 任务 ID (不提供则仅打印字幕信息)')
    
    args = parser.parse_args()
    
    # 读取字幕
    subtitles = read_subtitle_file(args.sub_file, args.lang)
    
    # 打印字幕时间信息
    print(f"找到 {len(subtitles)} 条字幕:")
    for sub in subtitles:
        print(f"时间: {sub['start']:.2f}s - {sub['end']:.2f}s")
        print(f"文本: {sub['text']}")
        print("-" * 50)
    
    # 如果提供了 task_id，则导入到 Label Studio
    if args.task_id:
        create_label_studio_annotation(subtitles, args.task_id)
        print("字幕已成功导入到 Label Studio")
    else:
        print("未提供 task_id，仅打印字幕信息")

if __name__ == "__main__":
    main() 