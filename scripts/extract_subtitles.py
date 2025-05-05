import os
import subprocess
import argparse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv('.env.prod')


def extract_subtitles(mkv_path, output_dir):
    """
    使用mkvextract从MKV文件中提取字幕
    """
    mkv_path = Path(mkv_path)
    output_dir = Path(output_dir)

    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)

    # 使用mkvinfo检查字幕轨道
    cmd_info = ['mkvinfo', str(mkv_path)]
    try:
        info = subprocess.check_output(cmd_info, stderr=subprocess.STDOUT)
        info = info.decode('utf-8')
    except subprocess.CalledProcessError as e:
        print(f"无法获取MKV文件信息: {mkv_path}\n错误: {e.output}")
        return
    except Exception as e:
        print("其他问题", e)
        return

    # 查找所有字幕轨道
    subtitle_tracks = []
    current_track = None
    for line in info.split('\n'):
        line = line.strip()
        if '+ 轨道编号:' in line:
            current_track = line.split(':')[1].strip().split()[0]
            current_track = int(current_track) - 1
            current_track = str(current_track)
        elif current_track and '轨道类型: 字幕' in line:
            subtitle_tracks.append(current_track)

    if not subtitle_tracks:
        print(f"未找到字幕轨道: {mkv_path}", info)
        return

    # 为每个字幕轨道提取字幕
    for track in subtitle_tracks:
        # 获取字幕语言
        cmd_lang = ['mkvinfo', str(mkv_path)]
        lang = 'und'  # 默认未知语言
        try:
            info = subprocess.check_output(
                cmd_lang, stderr=subprocess.STDOUT, text=True)
            for line in info.split('\n'):
                line = line.strip()
                if f'轨道号: {track}' in line:
                    # 查找语言
                    if '语言:' in line:
                        lang = line.split('语言:')[1].strip().split()[0].lower()
                    break
        except:
            pass

        # 构建输出文件名
        output_name = f"{mkv_path.stem}_sub{track}_{lang}.sub"
        output_path = output_dir / output_name

        # 使用mkvextract提取字幕
        cmd_extract = ['mkvextract', 'tracks', str(
            mkv_path), f"{track}:{output_path}"]
        try:
            subprocess.run(cmd_extract, check=True)
            print(f"提取字幕成功: {output_path}")
        except subprocess.CalledProcessError as e:
            print(f"提取字幕失败: {mkv_path} 轨道 {track}\n错误: {e}")


def process_directory(input_dir, output_dir):
    """
    处理目录下的所有MKV文件
    """
    input_dir = Path(input_dir)
    if not input_dir.is_dir():
        print(f"错误: 输入目录不存在: {input_dir}")
        return

    for item in input_dir.glob('**/*.mkv'):
        extract_subtitles(item, output_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='从MKV文件中提取字幕')
    parser.add_argument('input_dir', help='包含MKV文件的输入目录')
    parser.add_argument('output_dir', help='输出字幕文件的目录')

    args = parser.parse_args()

    # 检查mkvextract是否可用
    try:
        subprocess.run(['mkvextract', '--version'], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        print("错误: mkvextract未安装或不在PATH中。请安装MKVToolNix。")
        exit(1)

    process_directory(args.input_dir, args.output_dir)
