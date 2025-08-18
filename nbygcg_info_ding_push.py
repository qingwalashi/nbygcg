import json
from datetime import datetime, timedelta
import hashlib
import hmac
import base64
from typing import List, Dict
import os
from dotenv import load_dotenv
import requests
import urllib.parse
import time


def load_projects(file_path: str) -> List[Dict]:
    """加载项目数据"""
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 构建完整的文件路径
    full_path = os.path.join(current_dir, file_path)
    
    with open(full_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data['projects']


def filter_tomorrow_projects(projects: List[Dict]) -> Dict[str, List[Dict]]:
    """筛选开标时间为明天的项目"""
    target_types = [
        "信息化建设类项目",
        "信息化软硬件采购类项目"
    ]
    
    filtered_projects = {pt: [] for pt in target_types}
    
    # 计算明天的日期
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    for project in projects:
        if project['prjType'] in target_types and project['kbDate'] == tomorrow:
            filtered_projects[project['prjType']].append(project)
    
    return filtered_projects


def generate_push_content(filtered_projects: Dict[str, List[Dict]]) -> str:
    """生成推送内容"""
    content = []
    
    # 添加标题
    content.append("## 阳光采购明日开标信息")
    
    has_projects = any(projects for projects in filtered_projects.values())
    
    if not has_projects:
        content.append("明日无开标项目")
        return "\n".join(content)
    
    for pt, projects in filtered_projects.items():
        if projects:  # 只显示有项目类型的项目
            content.append(f"### {pt}")
            for project in projects:
                # 为每个项目构建跳转链接
                project_url = f"https://ygcg.nbcqjy.org/detail?bulletinId={project['bulletinId']}"
                content.append(f"- [{project['prjName']}]({project_url})")
            content.append("")
    
    return "\n".join(content)


def generate_sign(timestamp: int, secret: str) -> str:
    """生成钉钉加签"""
    string_to_sign = '{}\n{}'.format(timestamp, secret)
    secret_enc = secret.encode('utf-8')
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code).decode('utf-8'))
    return sign


def send_dingtalk_notification(content: str):
    """发送钉钉群推送通知"""
    # 加载环境变量
    load_dotenv()
    
    # 获取钉钉群的 webhook 地址组件和加签信息
    webhook_url = os.getenv('DINGTALK_WEBHOOK_URL')
    access_token = os.getenv('DINGTALK_ACCESS_TOKEN')
    secret = os.getenv('DINGTALK_SECRET')
    
    # 发送钉钉推送
    if webhook_url and access_token:
        try:
            # 构建完整 webhook 地址
            webhook = f"{webhook_url}?access_token={access_token}"
            
            # 如果配置了密钥，则添加签名参数
            if secret:
                # 生成时间戳和签名
                timestamp = str(round(time.time() * 1000))  # 注意：必须是字符串类型
                sign = generate_sign(timestamp, secret)
                webhook += f'&timestamp={timestamp}&sign={sign}'
            
            # 钉钉 API 请求头
            headers = {
                'Content-Type': 'application/json; charset=utf-8'
            }
            # 设置推送参数
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": "阳光采购明日开标信息",
                    "text": content
                }
            }
            
            # 发送POST请求
            response = requests.post(webhook, headers=headers, json=data)
            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    print("钉钉推送成功")
                else:
                    print(f"钉钉推送失败: {result.get('errmsg')}")
            else:
                print(f"钉钉推送失败: HTTP {response.status_code}")
        except Exception as e:
            print(f"钉钉推送异常: {str(e)}")
    else:
        print("警告: 未找到钉钉群webhook配置环境变量，跳过钉钉推送")


def main():
    # 加载项目数据
    projects = load_projects('date_prj.json')
    
    # 筛选明天开标的项目
    filtered_projects = filter_tomorrow_projects(projects)
    
    # 生成推送内容
    push_content = generate_push_content(filtered_projects)
    
    # 打印结果
    print(push_content)
    
    # 发送推送
    send_dingtalk_notification(push_content)


if __name__ == "__main__":
    main()