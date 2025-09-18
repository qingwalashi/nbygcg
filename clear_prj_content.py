# -*- coding: utf-8 -*-
"""
清空 opening_projects.json 与 purchase_bulletins.json 中各条目的 prjContent 字段（置为 null）。

用法示例：
  python clear_prj_content.py
  python clear_prj_content.py --openings opening_projects.json --bulletins purchase_bulletins.json
  python clear_prj_content.py --only openings
  python clear_prj_content.py --only bulletins
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[WARN] 文件不存在: {path}")
        return None
    except json.JSONDecodeError as e:
        print(f"[ERROR] 解析 JSON 失败: {path} -> {e}")
        return None
    except Exception as e:
        print(f"[ERROR] 读取失败: {path} -> {e}")
        return None


essential_keys = ("prjContent",)


def clear_openings(path: Path) -> int:
    data = load_json(path)
    if not isinstance(data, dict):
        print(f"[WARN] 非预期结构(应为 dict): {path}")
        return 0
    items = data.get("projects")
    if not isinstance(items, list):
        print(f"[WARN] 未找到 'projects' 列表: {path}")
        return 0
    changed = 0
    for item in items:
        if isinstance(item, dict):
            if item.get("prjContent") is not None:
                item["prjContent"] = None
                changed += 1
    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"[INFO] 已保存: {path}，置空 {changed} 条 prjContent")
    except Exception as e:
        print(f"[ERROR] 保存失败: {path} -> {e}")
    return changed


def clear_bulletins(path: Path) -> int:
    data = load_json(path)
    if not isinstance(data, list):
        print(f"[WARN] 非预期结构(应为 list): {path}")
        return 0
    changed = 0
    for item in data:
        if isinstance(item, dict):
            if item.get("prjContent") is not None:
                item["prjContent"] = None
                changed += 1
    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"[INFO] 已保存: {path}，置空 {changed} 条 prjContent")
    except Exception as e:
        print(f"[ERROR] 保存失败: {path} -> {e}")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description="清空两个 JSON 中的 prjContent 字段")
    parser.add_argument("--openings", default="opening_projects.json", help="开标项目 JSON 路径")
    parser.add_argument("--bulletins", default="purchase_bulletins.json", help="采购公告 JSON 路径")
    parser.add_argument("--only", choices=["openings", "bulletins", "both"], default="both", help="只处理哪个文件，默认 both")
    args = parser.parse_args()

    openings_path = Path(args.openings)
    bulletins_path = Path(args.bulletins)

    total_changed = 0
    if args.only in ("openings", "both"):
        total_changed += clear_openings(openings_path)
    if args.only in ("bulletins", "both"):
        total_changed += clear_bulletins(bulletins_path)

    print(f"[SUMMARY] 共置空 {total_changed} 条 prjContent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
