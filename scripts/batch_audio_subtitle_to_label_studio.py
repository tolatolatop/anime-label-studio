import os
import re
import argparse
from pathlib import Path
from dotenv import load_dotenv
from label_studio_sdk.client import LabelStudio

# 复用字幕解析函数


def parse_time(time_str):
    h, m, s = time_str.split(':')
    return float(h) * 3600 + float(m) * 60 + float(s)


def parse_subtitle_line(line):
    pattern = r'Dialogue: \d+,(\d+:\d+:\d+\.\d+),(\d+:\d+:\d+\.\d+),([^,]+),,.*?,,(.*)'
    match = re.match(pattern, line)
    if match:
        start_time, end_time, style, text = match.groups()
        text = re.sub(r'\{[^}]*\}', '', text)
        return {
            'start': parse_time(start_time),
            'end': parse_time(end_time),
            'text': text.strip()
        }
    return None


def read_subtitle_file(file_path, language=None):
    subtitles = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('Dialogue:'):
                if language is None or language in line:
                    subtitle = parse_subtitle_line(line)
                    if subtitle:
                        subtitles.append(subtitle)
    return subtitles


def create_annotation_result(subtitles):
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
                'channel': 0,
            }
        }
        results.append(result)
    return results


def get_audio_file_path(audio_file: Path):
    local_storage_path = os.environ['LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT']
    relative_path = audio_file.relative_to(local_storage_path)
    uri = f'/data/local-files/?d={relative_path}'
    return uri


def main():
    parser = argparse.ArgumentParser(description='批量上传音频和字幕到Label Studio')
    parser.add_argument('--project-id', type=int,
                        required=True, help='Label Studio项目ID')
    parser.add_argument('--audio-dir', required=True, help='音频文件目录')
    parser.add_argument('--subtitle-dir', required=True, help='字幕文件目录')
    parser.add_argument('--language', default='Dial_JP', help='字幕语言代码，可选')
    parser.add_argument('--env', default='.env.prod',
                        help='环境变量文件，默认.env.prod')
    args = parser.parse_args()

    load_dotenv(args.env)
    load_dotenv('C:/Users/47123/AppData/Local/label-studio/label-studio/.env')
    ls = LabelStudio(
        base_url=os.environ['LABEL_STUDIO_URL'],
        api_key=os.environ['LABEL_STUDIO_TOKEN'],
    )

    audio_dir = Path(args.audio_dir)
    subtitle_dir = Path(args.subtitle_dir)

    audio_files = list(audio_dir.glob('*.wav'))
    print(f"共找到{len(audio_files)}个音频文件")

    tasks = []
    audio_to_subs = {}
    for audio_file in audio_files:
        audio_name = audio_file.stem
        # 匹配所有 audio_name_*.sub
        sub_files = list(subtitle_dir.glob(f'{audio_name}_*.sub'))
        if not sub_files:
            print(f"警告: 未找到音频 {audio_file.name} 对应的字幕文件")
            continue
        audio_to_subs[audio_file] = sub_files

    for audio_file, sub_files in audio_to_subs.items():
        # 这里只取第一个字幕文件，如果有多个可自行扩展
        sub_file = sub_files[0]
        subtitles = read_subtitle_file(sub_file, args.language)
        # 构造任务数据
        # 这里假设音频文件可通过本地路径访问，实际部署时建议用URL或挂载到Label Studio可访问的路径
        task_data = {
            'audio': get_audio_file_path(audio_file)
        }
        tasks.append({'data': task_data, 'subtitles': subtitles,
                     'audio_file': audio_file, 'sub_file': sub_file})

    # 批量导入任务
    import_tasks = [{'audio': t['data']['audio']} for t in tasks]
    print(f"准备导入{len(import_tasks)}个任务到项目{args.project_id}")
    task_ids = []
    for t in import_tasks:
        task = ls.tasks.create(data=t, project=args.project_id)
        task_ids.append(task.id)
        print(f"已创建任务 {task.id}")
    print(f"已创建{len(task_ids)}个任务")

    # 上传annotation
    for t, task_id in zip(tasks, task_ids):
        results = create_annotation_result(t['subtitles'])
        if not results:
            print(f"警告: {t['audio_file'].name} 没有可用字幕，跳过标注上传")
            continue
        ls.annotations.create(id=task_id, result=results)
        print(f"音频 {t['audio_file'].name} 的字幕已作为标注上传到任务 {task_id}")

    print("全部任务和字幕标注已完成！")


if __name__ == '__main__':
    main()
