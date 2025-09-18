import json
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量 (.env)
load_dotenv()

ACCEPT_TYPES = {"信息化建设类项目", "信息化软硬件采购类项目"}
DEFAULT_TIMEOUT = 20
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


def read_opening_projects(path: str = "opening_projects.json") -> Optional[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[WARN] 文件不存在: {path}")
        return None
    except Exception as e:
        print(f"[ERROR] 读取 {path} 失败: {e}")
        return None


def read_purchase_bulletins(path: str = "purchase_bulletins.json") -> Optional[List[Dict[str, Any]]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[WARN] 文件不存在: {path}")
        return None
    except Exception as e:
        print(f"[ERROR] 读取 {path} 失败: {e}")
        return None


def save_json(content: Any, path: str) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False, indent=4)
        print(f"[INFO] 已保存: {path}")
    except Exception as e:
        print(f"[ERROR] 保存 {path} 失败: {e}")


# 基础 HTML 清洗：移除脚本、样式、标签，仅保留纯文本
TAG_RE = re.compile(r"<[^>]+>")
SCRIPT_STYLE_RE = re.compile(r"<\s*(script|style)[^>]*>.*?<\s*/\s*\1\s*>", re.I | re.S)
WHITESPACE_RE = re.compile(r"[ \t\r\f\v]+")


def html_to_text(html: str) -> str:
    if not html:
        return ""
    # 去掉 script/style
    html = SCRIPT_STYLE_RE.sub(" ", html)
    # 去掉标签
    text = TAG_RE.sub(" ", html)
    # HTML 实体简单还原
    try:
        import html as html_lib
        text = html_lib.unescape(text)
    except Exception:
        pass
    # 规范空白
    text = WHITESPACE_RE.sub(" ", text)
    text = re.sub(r"\n+", "\n", text)
    return text.strip()


def fetch_page_text(url: str, timeout: int = DEFAULT_TIMEOUT) -> Optional[str]:
    if not url:
        return None
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or resp.encoding or "utf-8"
        return html_to_text(resp.text)
    except Exception as e:
        print(f"[WARN] 请求失败: {url} -> {e}")
        return None


# LLM 提取“项目采购内容”
EXTRACT_PROMPT_TEMPLATE = (
    """
你是一名信息化项目采购要点抽取助手。请从下方给出的网页正文文本中，抽取“项目采购内容”的关键信息（例如软硬件清单、设备/系统名称、数量或范围、主要模块、交付内容等）。

要求：
- 只基于给定文本，不要编造
- 用中文，简洁、结构化表达
- 内容控制在 80~200 字以内，能覆盖主要采购点
- 输出 JSON，格式为：{{"prjContent": "..."}}

网页正文文本（可能包含无关内容，需甄别）：
"""
)


class LLMExtractor:
    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        model = os.getenv("OPENAI_MODEL", "Qwen/Qwen2.5-72B-Instruct")
        if not api_key:
            raise RuntimeError("未设置 OPENAI_API_KEY 环境变量")
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def extract(self, text: str, title: Optional[str] = None) -> Optional[str]:
        if not text or len(text) < 30:
            return None
        user_content = EXTRACT_PROMPT_TEMPLATE + (f"\n标题：{title}\n" if title else "") + "\n" + text[:8000]
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                    {"role": "user", "content": user_content},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
                top_p=0.1,
            )
            raw = resp.choices[0].message.content
            data = json.loads(raw)
            content = data.get("prjContent")
            if isinstance(content, str) and content.strip():
                return content.strip()
            return None
        except Exception as e:
            print(f"[WARN] LLM 抽取失败: {e}")
            return None


def need_process(prj_type: Optional[str], prj_content: Any) -> bool:
    if prj_type not in ACCEPT_TYPES:
        return False
    if prj_content is None:
        return True
    if isinstance(prj_content, str) and not prj_content.strip():
        return True
    return False


def process_opening_projects(extractor: LLMExtractor, path: str = "opening_projects.json", rate_sleep: float = 1.0) -> Tuple[int, int]:
    data = read_opening_projects(path)
    if not data or not isinstance(data, dict):
        return (0, 0)
    items = data.get("projects") or []
    total, updated = 0, 0
    for item in items:
        prj_type = item.get("prjType")
        if not need_process(prj_type, item.get("prjContent")):
            continue
        url = item.get("prjUrl")
        title = item.get("prjName")
        total += 1
        print(f"[OPENING] 抓取: {title} -> {url}")
        text = fetch_page_text(url)
        if not text:
            print("[OPENING] 抓取失败，跳过")
            continue
        content = extractor.extract(text, title=title)
        if content:
            item["prjContent"] = content
            updated += 1
            print("[OPENING] 已更新 prjContent")
        else:
            print("[OPENING] 未能从正文抽取到有效内容")
        time.sleep(rate_sleep)
    # 保存
    save_json(data, path)
    return (total, updated)


def process_purchase_bulletins(extractor: LLMExtractor, path: str = "purchase_bulletins.json", rate_sleep: float = 1.0) -> Tuple[int, int]:
    data = read_purchase_bulletins(path)
    if not data or not isinstance(data, list):
        return (0, 0)
    total, updated = 0, 0
    for item in data:
        prj_type = item.get("prjType")
        if not need_process(prj_type, item.get("prjContent")):
            continue
        url = item.get("prjUrl")
        title = item.get("bulletinTitle") or item.get("title")
        total += 1
        print(f"[BULLETIN] 抓取: {title} -> {url}")
        text = fetch_page_text(url)
        if not text:
            print("[BULLETIN] 抓取失败，尝试从 bulletinContent 提取")
            # 退路：有些文件本身就包含 HTML 内容字段
            html = item.get("bulletinContent")
            text = html_to_text(html) if isinstance(html, str) else None
            if not text:
                print("[BULLETIN] 无可用正文，跳过")
                continue
        content = extractor.extract(text, title=title)
        if content:
            item["prjContent"] = content
            updated += 1
            print("[BULLETIN] 已更新 prjContent")
        else:
            print("[BULLETIN] 未能从正文抽取到有效内容")
        time.sleep(rate_sleep)
    # 保存
    save_json(data, path)
    return (total, updated)


def main():
    # 初始化 LLM 提取器
    try:
        extractor = LLMExtractor()
    except Exception as e:
        print(f"[ERROR] 模型初始化失败：{e}")
        return

    # 处理 opening_projects.json
    o_total, o_updated = process_opening_projects(extractor)
    print(f"[SUMMARY] 开标项目待处理: {o_total}，已更新: {o_updated}")

    # 处理 purchase_bulletins.json
    b_total, b_updated = process_purchase_bulletins(extractor)
    print(f"[SUMMARY] 采购公告待处理: {b_total}，已更新: {b_updated}")


if __name__ == "__main__":
    main()
