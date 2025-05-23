# 阳光采购平台数据获取工具

这个项目是一个自动化工具，用于从阳光采购平台获取未来三天的招标信息。

## 功能特点

- 自动获取未来三天的招标信息
- 数据以JSON格式保存
- 支持自动定时执行
- 数据按开标日期排序

## 项目结构

```
.
├── .github/workflows/    # GitHub Actions 工作流配置
├── fetch_bidding.py      # 主程序
├── requirements.txt      # 项目依赖
└── date_prj.json        # 生成的招标数据
```

## 安装

1. 克隆仓库：
```bash
git clone [your-repository-url]
cd [repository-name]
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

## 使用方法

### 手动运行

直接执行 Python 脚本：
```bash
python fetch_bidding.py
```

### 自动运行

项目配置了 GitHub Actions，每天下午 18:00 自动执行数据获取任务。你也可以在 GitHub 仓库的 Actions 页面手动触发执行。

## 输出数据格式

生成的 `date_prj.json` 文件格式如下：

```json
{
    "today": "YYYY-MM-DD",
    "future_date": "YYYY-MM-DD",
    "projects": [
        {
            "kbDate": "YYYY-MM-DD",
            "prjName": "项目名称",
            "bulletinId": "公告ID"
        }
    ]
}
```

## 注意事项

- 确保有稳定的网络连接
- 需要 Python 3.x 环境
- 需要安装 requests 库