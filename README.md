# 阳光采购平台数据获取工具

这个项目是一个自动化工具，用于从阳光采购平台获取未来三天的招标信息，并使用 AI 模型对项目进行分类。

## 功能特点

- 自动获取未来三天的招标信息
- 使用 AI 模型对项目进行智能分类
- 数据以 JSON 格式保存
- 支持自动定时执行
- 数据按开标日期排序
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
├── fetch_bidding.py      # 数据获取程序
├── classify_projects.py  # 项目分类程序
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

1. 首先获取数据：
```bash
python fetch_bidding.py
```

2. 然后对项目进行分类：
```bash
python classify_projects.py
```

### 自动运行（GitHub Actions）

项目配置了 GitHub Actions，每天下午 18:00 自动执行数据获取和分类任务。你也可以在 GitHub 仓库的 Actions 页面手动触发执行。

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

#### 本地开发配置

1. 创建环境变量文件：
```bash
# 在项目根目录创建 .env 文件
touch .env
```

2. 编辑 .env 文件，添加以下配置：
```env
# API 配置
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.siliconflow.cn/v1

# 可选：设置日志级别
LOG_LEVEL=INFO
```

3. 确保 .env 文件已被 .gitignore 忽略：
```bash
# 检查 .gitignore 是否包含 .env
cat .gitignore | grep .env
```

4. 本地测试运行：
```bash
# 获取数据
python fetch_bidding.py

# 分类项目
python classify_projects.py
```

注意：
- .env 文件包含敏感信息，永远不要提交到版本控制系统
- 如果需要在不同环境使用不同的配置，可以创建多个 .env 文件：
  - .env.development - 开发环境配置
  - .env.testing - 测试环境配置
  - .env.production - 生产环境配置
- 确保团队成员都知道需要创建自己的 .env 文件

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
            "bulletinId": "公告ID",
            "prjType": "项目类型"
        }
    ]
}
```

## 注意事项

- 确保有稳定的网络连接
- 需要 Python 3.x 环境
- 需要安装 requirements.txt 中列出的依赖包
- API key 请妥善保管，不要直接提交到代码中
- 本地开发时建议使用 .env 文件管理环境变量