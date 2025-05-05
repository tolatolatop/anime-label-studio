#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import argparse
from pathlib import Path

def extract_audio(input_dir: str, output_dir: str, output_format: str = 'wav'):
    """
    从指定目录的视频文件中提取音频
    
    Args:
        input_dir: 输入视频目录
        output_dir: 输出音频目录
        output_format: 输出音频格式（默认为wav）
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 支持的视频格式
    video_extensions = ('.mp4', '.avi', '.mkv', '.mov', '.wmv')
    
    # 支持的音频格式及其对应的编码器
    audio_codecs = {
        'wav': 'pcm_s16le',  # WAV格式使用PCM编码
        'mp3': 'libmp3lame',  # MP3格式
        'aac': 'aac',        # AAC格式
        'flac': 'flac'       # FLAC格式
    }
    
    if output_format not in audio_codecs:
        raise ValueError(f'不支持的音频格式: {output_format}。支持的格式: {", ".join(audio_codecs.keys())}')
    
    # 遍历输入目录中的所有文件
    for file in os.listdir(input_dir):
        if file.lower().endswith(video_extensions):
            input_path = os.path.join(input_dir, file)
            # 将视频文件名转换为音频文件名（替换扩展名）
            output_filename = os.path.splitext(file)[0] + f'.{output_format}'
            output_path = os.path.join(output_dir, output_filename)
            
            # 构建ffmpeg命令
            command = [
                'ffmpeg',
                '-i', input_path,
                '-vn',  # 不处理视频
                '-acodec', audio_codecs[output_format],  # 使用指定的音频编码器
                '-y',  # 覆盖已存在的文件
            ]
            
            # 为MP3格式添加质量参数
            if output_format == 'mp3':
                command.extend(['-q:a', '2'])  # 设置音频质量（2是较高质量）
            
            command.append(output_path)
            
            try:
                print(f'正在处理: {file}')
                # 执行ffmpeg命令
                subprocess.run(command, check=True, capture_output=True)
                print(f'完成: {output_filename}')
            except subprocess.CalledProcessError as e:
                print(f'处理 {file} 时出错: {str(e)}')
            except Exception as e:
                print(f'发生错误: {str(e)}')

def main():
    parser = argparse.ArgumentParser(description='从视频文件中提取音频')
    parser.add_argument('input_dir', help='输入视频目录路径')
    parser.add_argument('output_dir', help='输出音频目录路径')
    parser.add_argument('-f', '--format', default='wav',
                      choices=['wav', 'mp3', 'aac', 'flac'],
                      help='输出音频格式 (默认: wav)')
    
    args = parser.parse_args()
    
    # 检查ffmpeg是否可用
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print('错误: 未找到ffmpeg。请确保ffmpeg已安装并添加到系统PATH中。')
        return
    
    try:
        extract_audio(args.input_dir, args.output_dir, args.format)
    except ValueError as e:
        print(f'错误: {str(e)}')

if __name__ == '__main__':
    main() 