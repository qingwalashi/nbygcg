# 阳光采购平台数据获取工具

这个项目是一个自动化工具，用于从阳光采购平台获取未来三天的招标信息与最新采购公告，并使用 AI 模型对项目进行分类；同时提供本地前端看板（`index.html`）用于可视化查看与筛选，并支持钉钉/Bark 推送。

## 功能特点

- 自动获取未来三天的招标信息
- 自动获取最近的采购公告（并标准化关键字段）
- 使用 AI 模型对项目进行智能分类
- 智能抽取“项目采购内容”摘要到 `prjContent` 字段（来自公告正文或开标接口详情）
- 提供本地前端看板：近期开标、最新公告，支持搜索/类型/日期筛选、详情弹窗
- 数据以 JSON 保存，便于二次加工
- 支持 GitHub Actions 定时自动执行
- 数据按开标日期排序
- 支持推送：
  - 钉钉群 Markdown 推送（昨日信息化采购公告 + 明日信息化开标）
  - Bark 推送（信息化项目汇总）
- 项目分类包括：
  - 信息化建设类项目
  - 信息化服务类项目
  - 信息化软硬件采购类项目
  - 工程类项目
  - 其他项目

## 项目结构

```
.
├── .github/workflows/    # GitHub Actions 工作流配置
├── fetch_opening_projects.py      # 获取近期开标数据
├── fetch_purchase_bulletins.py    # 获取最新采购公告（清洗为数组）
├── classify_projects.py  # 项目分类程序
├── extract_procurement_content.py # 从正文抽取“项目采购内容”摘要到 prjContent
├── clear_prj_content.py           # 将两个 JSON 中的 prjContent 批量置空（清理工具）
├── nbygcg_info_ding_push.py       # 钉钉推送（昨日公告 + 明日开标 摘要）
├── bark_push_opening_projects.py  # Bark 推送（信息化项目汇总，可选）
├── nbygcg_info_bark_push.py       # Bark 推送（同上，另一实现）
├── index.html                     # 本地可视化看板（近期开标 / 最新公告，支持搜索筛选与弹窗）
├── requirements.txt      # 项目依赖
├── opening_projects.json          # 生成的招标数据
└── purchase_bulletins.json        # 生成的采购公告数据
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

1. 首先获取数据：
```bash
python fetch_opening_projects.py
python fetch_purchase_bulletins.py
```

2. 然后对项目/公告进行分类（会更新两个 JSON 中的 `prjType` 字段）：
```bash
python classify_projects.py
```

3. 可选：抽取“项目采购内容”（将摘要写入两个 JSON 的 `prjContent` 字段，仅对信息化类项目执行）：
```bash
python extract_procurement_content.py
```

4. 本地查看前端看板（推荐使用本地 HTTP 服务，以便浏览器能加载 JSON 文件）：
```bash
# 在项目根目录启动简易服务（默认 8000 端口）
python -m http.server 8000
# 浏览器打开
# http://localhost:8000/index.html
```

5. 可选：推送到钉钉 / Bark（需先配置环境变量，见下文“环境变量”）
```bash
# 钉钉（昨日信息化采购公告 + 明日信息化开标摘要）
python nbygcg_info_ding_push.py

# Bark（信息化项目清单汇总）
python bark_push_opening_projects.py
```

### 一键流程（抓取 → 分类 → 抽取 → 推送）
```bash
python fetch_opening_projects.py && \
python fetch_purchase_bulletins.py && \
python classify_projects.py && \
python extract_procurement_content.py && \
python nbygcg_info_ding_push.py
```

### 自动运行（GitHub Actions）

项目配置了 GitHub Actions，每天定时自动执行：
- 抓取近期开标与最新采购公告
- 运行分类脚本并更新 `opening_projects.json`、`purchase_bulletins.json`
- 抽取“项目采购内容”并写入 `prjContent`
- 提交改动并进行钉钉推送（开标信息）
你也可以在 GitHub 仓库的 Actions 页面手动触发执行。

#### 配置 GitHub Actions Secrets

在使用 GitHub Actions 之前，需要配置以下 secrets：

1. 打开你的 GitHub 仓库
2. 点击 "Settings" 标签
3. 在左侧菜单中找到 "Secrets and variables" -> "Actions"
4. 点击 "New repository secret"
5. 添加以下 secrets：

   - 名称：`OPENAI_API_KEY`
     值：从 https://cloud.siliconflow.cn/account/ak 获取的 API key
     
   - 名称：`OPENAI_BASE_URL`
     值：`https://api.siliconflow.cn/v1`

   - 名称：`OPENAI_MODEL`（可选，默认 `Qwen/Qwen2.5-72B-Instruct`）

   - 名称：`DINGTALK_WEBHOOK_URL`（用于钉钉推送开标信息）
   - 名称：`DINGTALK_ACCESS_TOKEN`
   - 名称：`DINGTALK_SECRET`

## 环境变量

为使分类与推送脚本工作，需要以下环境变量（建议放在项目根目录 `.env` 文件中）：

```env
# 大模型分类/抽取（SiliconFlow 兼容 OpenAI SDK）
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.siliconflow.cn/v1
OPENAI_MODEL=Qwen/Qwen2.5-72B-Instruct

# 钉钉推送（至少需要以下两个）
DINGTALK_WEBHOOK_URL=https://oapi.dingtalk.com/robot/send
DINGTALK_ACCESS_TOKEN=your_access_token
# 可选：安全加签
DINGTALK_SECRET=your_sign_secret

# Bark 推送（可选）
BARK_KEY=your_bark_device_key
```

> `.env` 文件仅用于本地开发，切勿提交到仓库。

#### 本地开发配置

1. 创建环境变量文件：
```bash
# 在项目根目录创建 .env 文件
touch .env
```

2. 编辑 .env 文件，添加以下配置：
参考上文“环境变量”示例.

3. 确保 .env 文件已被 .gitignore 忽略：
```bash
# 检查 .gitignore 是否包含 .env
cat .gitignore | grep .env
```

4. 本地测试运行：
```bash
# 获取数据
python fetch_opening_projects.py
python fetch_purchase_bulletins.py

# 分类项目/公告
python classify_projects.py

# （可选）抽取项目采购内容
python extract_procurement_content.py
```

注意：
- .env 文件包含敏感信息，永远不要提交到版本控制系统
- 如果需要在不同环境使用不同的配置，可以创建多个 .env 文件：
  - .env.development - 开发环境配置
  - .env.testing - 测试环境配置
  - .env.production - 生产环境配置
- 确保团队成员都知道需要创建自己的 .env 文件

## 前端看板（`index.html`）

- 入口：在仓库根目录通过本地 HTTP 服务访问 `http://localhost:8000/index.html`
- 菜单：左侧切换“近期开标”和“最新公告”两大视图
- 筛选：支持“搜索关键字”“项目类型”“发布日期/截止时间/开标日期”筛选
- 详情：公告卡片可打开“查看详情/采购内容”弹窗，支持复制
- 原文：每个条目提供“查看原文”跳转到阳光采购平台

## 输出数据格式

生成的 `opening_projects.json` 文件格式如下：

```json
{
    "today": "YYYY-MM-DD",
    "future_date": "YYYY-MM-DD",
    "projects": [
        {
            "kbDate": "YYYY-MM-DD",
            "prjName": "项目名称",
            "bulletinId": "公告ID",
            "prjId": "项目ID（可能存在）",
            "prjNo": "项目编号（可能存在）",
            "prjUrl": "详情地址（基于 prjId 或 bulletinId 生成）",
            "prjType": "项目类型",
            "prjContent": "项目采购内容摘要（可选，执行抽取后写入）"
        }
    ]
}
```

生成的 `purchase_bulletins.json` 文件格式如下（数组）：

```json
[
  {
    "prjTypeId": "02",
    "publishDate": "YYYY-MM-DD",
    "bulletinTitle": "公告标题",
    "bulletinContent": "公告HTML内容（可能较长）",
    "endDate": "YYYY-MM-DDTHH:MM:SS",
    "prjNo": "项目编号",
    "kbDate": "YYYY-MM-DDTHH:MM:SS",
    "bulletinId": "原站点的 autoId/id/bulletinId（字符串化）",
    "prjId": "项目ID（可能存在）",
    "prjUrl": "详情地址（固定使用 bulletinId 链接）",
    "prjType": "项目类型（分类后写入）",
    "prjContent": "项目采购内容摘要（可选，执行抽取后写入）"
  }
]
```

## 注意事项

- 确保有稳定的网络连接
- 需要 Python 3.x 环境
- 需要安装 requirements.txt 中列出的依赖包
- API key 请妥善保管，不要直接提交到代码中
- 本地开发时建议使用 .env 文件管理环境变量
- 如直接双击打开 `index.html` 读取本地 JSON 可能受浏览器 CORS/本地策略限制，请使用 `python -m http.server` 启动本地服务

## 实用工具

- 清理 `prjContent` 字段：
  - 将两个 JSON 中已有的 `prjContent` 批量置空（便于重新抽取）
  - 示例：
    ```bash
    # 同时清理两个文件
    python clear_prj_content.py

    # 指定文件名
    python clear_prj_content.py --openings opening_projects.json --bulletins purchase_bulletins.json

    # 只清理其中一个
    python clear_prj_content.py --only openings
    python clear_prj_content.py --only bulletins
    ```