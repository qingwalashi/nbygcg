import requests
import json
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def fetch_opening_projects():
    url = "https://ygcg.nbcqjy.org/api/Portal/GetOpenList"

    # 构造请求参数
    payload = "{\"pageIndex\": 1,\"pageSize\": 200}"
    headers = {
        'Content-Type': 'application/json;charset-utf-8'
    }

    # 发送POST请求
    response = requests.post(url, headers=headers, data=payload)
    response_data = response.json()

    # 使用北京时区计算今天与未来三天的日期
    beijing_tz = ZoneInfo("Asia/Shanghai")
    beijing_now = datetime.now(beijing_tz)
    today = beijing_now.date()
    future_date = today + timedelta(days=3)

    # 提取符合条件的项目
    filtered_projects = []
    for project in response_data["body"]["data"]["projectList"]:
        # 解析开标时间：若无时区则按北京时区解释；若有时区则转换到北京时区
        kb_raw = project["kbDate"]
        dt = datetime.fromisoformat(kb_raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=beijing_tz)
        else:
            dt = dt.astimezone(beijing_tz)
        kb_date = dt.date()
        if today <= kb_date <= future_date:
            filtered_projects.append({
                "kbDate": dt.strftime("%Y-%m-%d"),
                "prjName": project["prjName"],
                "bulletinId": project["bulletinId"],
                "prjType": "其他项目"
            })

    # 按开标日期升序排序
    filtered_projects.sort(key=lambda x: x["kbDate"])

    return {
        "today": today.strftime("%Y-%m-%d"),
        "future_date": future_date.strftime("%Y-%m-%d"),
        "projects": filtered_projects
    }


def save_to_json(data, savepath="opening_projects.json"):
    # 确保保存路径的目录存在
    save_dir = os.path.dirname(savepath)
    if save_dir and not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # 将 JSON 数据保存到指定路径
    with open(savepath, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def main():
    # 获取数据
    data = fetch_opening_projects()

    # 保存到JSON文件
    save_to_json(data)

    print(f"数据已保存到 opening_projects.json")
    print(f"今日日期: {data['today']}")
    print(f"未来日期: {data['future_date']}")
    print(f"找到 {len(data['projects'])} 个项目")


if __name__ == "__main__":
    main()
