import json
from typing import List, Dict
import os
from dotenv import load_dotenv
import requests


def load_projects(file_path: str) -> List[Dict]:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(current_dir, file_path)
    with open(full_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data['projects']


def filter_and_sort_projects(projects: List[Dict]) -> Dict[str, List[Dict]]:
    target_types = [
        "信息化建设类项目",
        "信息化服务类项目",
        "信息化软硬件采购类项目"
    ]
    filtered_projects = {pt: [] for pt in target_types}
    for project in projects:
        if project['prjType'] in target_types:
            filtered_projects[project['prjType']].append(project)
    for pt in target_types:
        filtered_projects[pt].sort(key=lambda x: x['kbDate'])
    return filtered_projects


def generate_markdown(filtered_projects: Dict[str, List[Dict]]) -> str:
    markdown = []
    markdown.append("# 阳光采购近期开标信息（信息化项目）\n")
    for pt, projects in filtered_projects.items():
        markdown.append(f"## {pt}\n")
        for i, project in enumerate(projects, 1):
            markdown.append(f"{i}. {project['prjName']} ({project['kbDate']})")
        markdown.append("")
    markdown.append("\n[查看更多](https://nbygcg.qingwalashi.cn/)")
    return "\n".join(markdown)


def generate_push_content(filtered_projects: Dict[str, List[Dict]]) -> str:
    content = []
    for pt, projects in filtered_projects.items():
        content.append(f"{pt}:")
        for project in projects:
            content.append(f"- {project['prjName']} ({project['kbDate']})")
        content.append("")
    content.append("查看更多: https://nbygcg.qingwalashi.cn/")
    return "\n".join(content)


def send_push_notification(content: str):
    load_dotenv()
    bark_key = os.getenv('BARK_KEY')
    if bark_key:
        try:
            bark_url = "https://api.day.app/push"
            headers = {
                'Content-Type': 'application/json; charset=utf-8'
            }
            data = {
                "body": content,
                "title": "阳光采购近期开标信息",
                "device_key": bark_key,
                "sound": "minuet",
                "icon": "https://blog.qingwalashi.cn/favicon.ico",
                "group": "阳光采购",
            }
            response = requests.post(bark_url, headers=headers, json=data)
            if response.status_code == 200:
                print("Bark推送成功")
            else:
                print(f"Bark推送失败: HTTP {response.status_code}")
        except Exception as e:
            print(f"Bark推送失败: {str(e)}")
    else:
        print("警告: 未找到BARK_KEY环境变量，跳过Bark推送")


def main():
    projects = load_projects('opening_projects.json')
    filtered_projects = filter_and_sort_projects(projects)
    markdown_output = generate_markdown(filtered_projects)
    push_content = generate_push_content(filtered_projects)
    print(markdown_output)
    send_push_notification(push_content)


if __name__ == "__main__":
    main()
