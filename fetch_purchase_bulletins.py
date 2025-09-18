import os
import json
import requests
from datetime import datetime, timedelta
import re
from zoneinfo import ZoneInfo

def fetch_purchase_bulletins():
    url = "https://ygcg.nbcqjy.org/api/Portal/GetBulletinList"
    # 按用户提供的构造方式使用字符串作为请求体
    payload = "{\"pageIndex\": 1,\"pageSize\": 100,\"classID\": \"21\"}"
    headers = {
        'Content-Type': 'application/json;charset-utf-8'
    }

    resp = requests.post(url, headers=headers, data=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def save_json(content, savepath="purchase_bulletins.json"):
    save_dir = os.path.dirname(savepath)
    if save_dir and not os.path.exists(save_dir):
        os.makedirs(save_dir)
    with open(savepath, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)

def extract_items(data):
    """从原始返回中尽量稳妥地取出公告列表数组。"""
    if isinstance(data, dict):
        body = data.get("body") or {}
        inner = body.get("data") if isinstance(body, dict) else {}
        if isinstance(inner, dict):
            for key in ["list", "bulletinList", "items", "rows", "data"]:
                items = inner.get(key)
                if isinstance(items, list):
                    return items
        # 有些接口直接在 body 下给 list
        for key in ["list", "bulletinList", "items", "rows"]:
            items = body.get(key) if isinstance(body, dict) else None
            if isinstance(items, list):
                return items
    return []

def parse_date_to_ymd(value):
    """将日期字符串解析为 YYYY-MM-DD 格式。失败则返回 None。"""
    if not value:
        return None
    # 常见格式尝试：ISO、yyyy-mm-dd、yyyy/mm/dd、带时间
    try:
        # 兼容 '2025-09-01'、'2025-09-01 12:34:56'
        # 先仅取前10位尝试
        core = str(value)[:10]
        dt = datetime.fromisoformat(core)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        pass
    # 使用正则抓取年月日
    m = re.search(r"(?:^|[^\d])(\d{4})[-/](\d{1,2})[-/](\d{1,2})(?:[^\d]|$)", str(value))
    if m:
        try:
            year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
            return f"{year:04d}-{month:02d}-{day:02d}"
        except Exception:
            return None
    return None

def parse_to_iso_datetime(value):
    """将输入解析为标准的 YYYY-MM-DDTHH:MM:SS 字符串。
    - 允许分隔符为 '-' 或 '/'
    - 允许时间用空格或 'T' 连接
    - 若缺少分或秒，自动补零
    """
    if not value:
        return None
    s = str(value).strip()
    # 先尝试用正则拆解
    m = re.search(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})(?:[ T](\d{1,2})(?::(\d{1,2}))?(?::(\d{1,2}))?)?", s)
    if m:
        try:
            y = int(m.group(1))
            mo = int(m.group(2))
            d = int(m.group(3))
            hh = int(m.group(4)) if m.group(4) is not None else 0
            mm_ = int(m.group(5)) if m.group(5) is not None else 0
            ss = int(m.group(6)) if m.group(6) is not None else 0
            return f"{y:04d}-{mo:02d}-{d:02d}T{hh:02d}:{mm_:02d}:{ss:02d}"
        except Exception:
            pass
    # 回退：归一化分隔符后尝试 fromisoformat
    try:
        normalized = s.replace('/', '-').replace(' ', 'T')
        dt = datetime.fromisoformat(normalized)
        return dt.strftime("%Y-%m-%dT%H:%M:%S")
    except Exception:
        return None

def process_bulletins(raw_data):
    """将原始公告数据清洗为需要的字段结构。"""
    items = extract_items(raw_data)
    processed = []
    for it in items:
        if not isinstance(it, dict):
            continue
        prj_type_id = it.get("prjTypeId") or it.get("projectTypeId") or it.get("typeId")
        publish_date_raw = it.get("publishDate") or it.get("fbDate") or it.get("pubDate")
        publish_date_ymd = parse_date_to_ymd(publish_date_raw)
        # 提取 autoId 作为 bulletinId（若无则回退 id），并尽量规范为字符串
        raw_bid = it.get("autoId") if it.get("autoId") is not None else (it.get("id") if it.get("id") is not None else it.get("bulletinId"))
        bulletin_id = str(raw_bid) if raw_bid is not None else None
        prj_id = it.get("prjId") or it.get("projectId") or it.get("prjid") or it.get("PrjId")
        # 根据需求：公告的 prjUrl 固定使用 bulletinId 的链接形式
        prj_url = f"https://ygcg.nbcqjy.org/detail?bulletinId={bulletin_id}" if bulletin_id else None
        processed.append({
            "prjTypeId": prj_type_id,
            "publishDate": publish_date_ymd,  # YYYY-MM-DD 格式
            "bulletinTitle": it.get("bulletinTitle") or it.get("title") or "",
            "bulletinContent": it.get("bulletinContent") or it.get("content") or "",
            "endDate": parse_to_iso_datetime(it.get("endDate") or it.get("bjEndDate") or it.get("deadline")),
            "prjNo": it.get("prjNo") or it.get("projectNo") or it.get("code"),
            "kbDate": parse_to_iso_datetime(it.get("kbDate") or it.get("openDate") or it.get("bidOpenDate")),
            "bulletinId": bulletin_id,
            "prjId": prj_id,
            "prjUrl": prj_url,
            "prjType": "其他项目",
            "prjContent": None
        })
    return processed

def filter_recent_bulletins(items, days=3, exclude_today=True):
    """按 publishDate 只保留最近 days 天内的数据。
    - publishDate 需为 YYYY-MM-DD
    - exclude_today=True 表示不包含今天，只取 [today-days, today) 区间
    """
    # 使用北京时区获取当前日期
    today = datetime.now(ZoneInfo("Asia/Shanghai")).date()
    start = today - timedelta(days=days)
    filtered = []
    for b in items:
        pd = b.get("publishDate")
        if not pd:
            continue
        try:
            d = datetime.strptime(pd, "%Y-%m-%d").date()
        except Exception:
            continue
        if exclude_today:
            if start <= d < today:
                filtered.append(b)
        else:
            if start <= d <= today:
                filtered.append(b)
    return filtered


def main():
    try:
        data = fetch_purchase_bulletins()
        # 清洗、提取并保存到单一文件
        processed = process_bulletins(data)
        filtered = filter_recent_bulletins(processed, days=3, exclude_today=True)
        save_json(filtered, "purchase_bulletins.json")
        print(f"已保存采购公告（处理后），记录数：{len(filtered)}")
        print("输出文件：purchase_bulletins.json")
    except Exception as e:
        print(f"抓取失败: {e}")
        raise


if __name__ == "__main__":
    main()
