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
    """加载开标项目数据（opening_projects.json -> projects 列表）"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(current_dir, file_path)
    with open(full_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data['projects']


def filter_tomorrow_projects(projects: List[Dict]) -> Dict[str, List[Dict]]:
    """筛选开标时间为明天的项目（按项目类型分组）"""
    target_types = [
        "信息化建设类项目",
        "信息化软硬件采购类项目"
    ]
    grouped: Dict[str, List[Dict]] = {pt: [] for pt in target_types}
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    for project in projects:
        if project.get('prjType') in target_types and project.get('kbDate') == tomorrow:
            grouped[project['prjType']].append(project)
    return grouped


def load_purchase_bulletins(file_path: str = 'purchase_bulletins.json') -> List[Dict]:
    """加载采购公告列表（顶层为数组）"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(current_dir, file_path)
    with open(full_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if isinstance(data, list):
            return data
        return []


def parse_iso_to_display(dt_str: str) -> str:
    """将 ISO 日期时间字符串转换为 'YYYY-MM-DD HH:MM'，失败返回空串"""
    if not dt_str:
        return ""
    try:
        # 兼容 'YYYY-MM-DDTHH:MM:SS' 或 'YYYY-MM-DD HH:MM:SS'
        normalized = dt_str.replace(' ', 'T')
        dt = datetime.fromisoformat(normalized)
        return dt.strftime('%Y-%m-%d %H:%M')
    except Exception:
        # 若仅有日期
        try:
            d = datetime.strptime(dt_str[:10], '%Y-%m-%d')
            return d.strftime('%Y-%m-%d 00:00')
        except Exception:
            return ""


def filter_yesterday_bulletins(bulletins: List[Dict]) -> Dict[str, List[Dict]]:
    """筛选昨日新增的采购公告（按项目类型分组）"""
    target_types = [
        "信息化建设类项目",
        "信息化软硬件采购类项目"
    ]
    grouped: Dict[str, List[Dict]] = {pt: [] for pt in target_types}
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    for b in bulletins:
        prj_type = b.get('prjType')
        pub_date = b.get('publishDate')
        if prj_type in target_types and pub_date == yesterday:
            grouped[prj_type].append(b)
    return grouped


def generate_push_content(yesterday_bulletins: Dict[str, List[Dict]], tomorrow_projects: Dict[str, List[Dict]]) -> str:
    """生成合并后的推送内容：昨日采购公告 + 明日开标项目"""
    lines: List[str] = []
    # 标题
    lines.append("## 阳光采购每日摘要")

    # 昨日新增信息化采购公告
    lines.append("\n### 昨日新增信息化采购公告")
    has_yesterday = any(items for items in yesterday_bulletins.values())
    if not has_yesterday:
        lines.append("- 昨日无新增采购公告")
    else:
        for pt, items in yesterday_bulletins.items():
            if not items:
                continue
            lines.append(f"#### {pt}")
            for it in items:
                title = it.get('bulletinTitle') or it.get('title') or '未命名项目'
                kb_display = parse_iso_to_display(it.get('kbDate') or '')
                prj_id = it.get('prjId')
                url = (
                    f"https://ygcg.nbcqjy.org/detail?type=1&prjId={urllib.parse.quote(prj_id)}"
                    if prj_id else f"https://ygcg.nbcqjy.org/detail?bulletinId={it.get('bulletinId')}"
                )
                if kb_display:
                    lines.append(f"- [{title}]({url})（开标：{kb_display}）")
                else:
                    lines.append(f"- [{title}]({url})")
                # 追加采购内容 prjContent（若存在），为避免过长，进行适度截断并以引用展示
                prj_content = (it.get('prjContent') or '').strip()
                if prj_content:
                    one_line = ' '.join(prj_content.split())  # 压缩换行与多余空格
                    if len(one_line) > 500:
                        one_line = one_line[:500].rstrip() + '……'
                    lines.append(f"  > {one_line}")
            lines.append("")

    # 明日信息化开标项目
    lines.append("")
    lines.append("### 明日信息化开标项目")
    has_tomorrow = any(items for items in tomorrow_projects.values())
    if not has_tomorrow:
        lines.append("- 明日无开标项目")
    else:
        for pt, items in tomorrow_projects.items():
            if not items:
                continue
            lines.append(f"#### {pt}")
            for project in items:
                prj_id = project.get('prjId')
                project_url = (
                    f"https://ygcg.nbcqjy.org/detail?type=1&prjId={urllib.parse.quote(prj_id)}"
                    if prj_id else f"https://ygcg.nbcqjy.org/detail?bulletinId={project.get('bulletinId')}"
                )
                lines.append(f"- [{project['prjName']}]({project_url})")
                # 追加采购内容 prjContent（若存在），为避免过长，进行适度截断并以引用展示
                prj_content = (project.get('prjContent') or '').strip()
                if prj_content:
                    one_line = ' '.join(prj_content.split())  # 压缩换行与多余空格
                    if len(one_line) > 500:
                        one_line = one_line[:500].rstrip() + '……'
                    lines.append(f"  > {one_line}")
            lines.append("")

    return "\n".join(lines)


def generate_sign(timestamp: int, secret: str) -> str:
    string_to_sign = '{}\n{}'.format(timestamp, secret)
    secret_enc = secret.encode('utf-8')
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code).decode('utf-8'))
    return sign


def send_dingtalk_notification(content: str):
    """发送钉钉群推送通知"""
    load_dotenv()
    webhook_url = os.getenv('DINGTALK_WEBHOOK_URL')
    access_token = os.getenv('DINGTALK_ACCESS_TOKEN')
    secret = os.getenv('DINGTALK_SECRET')
    if webhook_url and access_token:
        try:
            webhook = f"{webhook_url}?access_token={access_token}"
            if secret:
                timestamp = str(round(time.time() * 1000))
                sign = generate_sign(timestamp, secret)
                webhook += f'&timestamp={timestamp}&sign={sign}'
            headers = {
                'Content-Type': 'application/json; charset=utf-8'
            }
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": "阳光采购每日摘要",
                    "text": content
                }
            }
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
    # 明日开标项目
    projects = load_projects('opening_projects.json')
    tomorrow_projects = filter_tomorrow_projects(projects)

    # 昨日新增采购公告
    try:
        bulletins = load_purchase_bulletins('purchase_bulletins.json')
    except FileNotFoundError:
        bulletins = []
    yesterday_bulletins = filter_yesterday_bulletins(bulletins)

    # 生成并发送推送
    push_content = generate_push_content(yesterday_bulletins, tomorrow_projects)
    print(push_content)
    send_dingtalk_notification(push_content)


if __name__ == "__main__":
    main()
