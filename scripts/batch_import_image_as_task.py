import os
import argparse
import requests
from glob import glob
from dotenv import load_dotenv
from label_studio_sdk.client import LabelStudio

# 配置 Label Studio API
LABEL_STUDIO_URL = os.environ.get('LABEL_STUDIO_URL', 'http://localhost:8080')
API_TOKEN = os.environ.get('LABEL_STUDIO_API_TOKEN', 'YOUR_API_TOKEN')

HEADERS = {
    'Authorization': f'Token {API_TOKEN}'
}


def upload_image_to_label_studio(project_id, image_path):
    """
    上传单张图片到 label-studio 作为任务
    """
    with open(image_path, 'rb') as f:
        files = {'file': (os.path.basename(image_path),
                          f, 'application/octet-stream')}
        response = requests.post(
            f'{LABEL_STUDIO_URL}/api/projects/{project_id}/import',
            headers=HEADERS,
            files=files
        )
    if response.status_code == 201:
        print(f"成功上传: {image_path}")
    else:
        print(
            f"上传失败: {image_path}, 状态码: {response.status_code}, 响应: {response.text}")


def get_image_file_path(image_file):
    """
    将本地图片路径转换为Label Studio可访问的本地文件URL
    """
    local_storage_path = os.environ['LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT']
    relative_path = os.path.relpath(image_file, local_storage_path)
    uri = f'/data/local-files/?d={relative_path}'
    return uri


def main():
    parser = argparse.ArgumentParser(description='批量导入图片到 Label Studio 项目')
    parser.add_argument('--project-id', required=True,
                        help='Label Studio 项目ID')
    parser.add_argument('--src-dir', required=True, help='图片所在目录')
    parser.add_argument('--env', default='.env.prod',
                        help='环境变量文件，默认.env.prod')
    args = parser.parse_args()

    load_dotenv(args.env)
    ls = LabelStudio(
        base_url=os.environ['LABEL_STUDIO_URL'],
        api_key=os.environ['LABEL_STUDIO_TOKEN'],
    )

    # 支持的图片格式
    exts = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.gif']
    image_files = []
    for ext in exts:
        image_files.extend(glob(os.path.join(args.src_dir, ext)))

    if not image_files:
        print('未找到任何图片文件')
        return

    print(f'共找到 {len(image_files)} 张图片，开始上传...')
    for img_path in image_files:
        image_url = get_image_file_path(img_path)
        task_data = {'ocr': image_url}
        task = ls.tasks.create(data=task_data, project=args.project_id)
        print(f"已创建任务 {task.id}，图片: {img_path}")

    print('全部上传完成！')


if __name__ == '__main__':
    main()
