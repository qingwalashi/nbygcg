import json
from openai import OpenAI
import time
import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

def load_projects():
    try:
        with open('opening_projects.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print("Error: opening_projects.json not found")
        return None

def classify_project(client, project_name):
    prompt = f"""请根据以下项目名称，判断它属于以下哪一类项目：
- 信息化建设类项目
- 信息化服务类项目
- 信息化软硬件采购类项目
- 工程类项目
- 其他项目

项目名称：{project_name}

请只返回JSON格式的答案，格式为：{{"prjType": "项目类型"}}"""

    try:
        response = client.chat.completions.create(
            # model="Qwen/Qwen3-32B",
            model="Qwen/Qwen2.5-72B-Instruct",
            # model="Qwen/Qwen3-8B", #siliconflow 免费模型，准确率不够高
            messages=[
                {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error classifying project: {e}")
        return {"prjType": "其他项目"}

def update_projects(original_data, classifications):
    for project in original_data["projects"]:
        bulletin_id = project["bulletinId"]
        if bulletin_id in classifications:
            project["prjType"] = classifications[bulletin_id]

def save_projects(data):
    with open('opening_projects.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

# ========== 新增：采购公告（purchase_bulletins.json）读写 ==========
def load_purchase_bulletins():
    try:
        with open('purchase_bulletins.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print("Error: purchase_bulletins.json not found")
        return None

def save_purchase_bulletins(data):
    with open('purchase_bulletins.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def main():
    # 从环境变量获取API配置
    api_key = os.getenv('OPENAI_API_KEY')
    base_url = os.getenv('OPENAI_BASE_URL', 'https://api.siliconflow.cn/v1')

    if not api_key:
        print("Error: OPENAI_API_KEY environment variable is not set")
        print("Please create a .env file with your API key or set the environment variable")
        return

    # 初始化OpenAI客户端
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )

    # ================= 处理开标项目（opening_projects.json） =================
    # 说明：
    # - 输入文件：opening_projects.json
    # - 数据结构：{"projects": [{"prjName": str, "bulletinId": str, "prjType": str, ...}, ...]}
    # - 分类依据：对每个项目的 prjName 进行大模型分类（classify_project）
    # - 输出效果：将分类结果写入对应项目对象的 prjType 字段
    # - 容错与降级：
    #   * 若文件缺失或解析失败：跳过该段处理，不影响后续采购公告处理
    #   * 若单次 API 调用异常：返回 {"prjType": "其他项目"} 作为回退
    # - 限频处理：每次请求后 sleep(1) 以降低触发限频的概率
    data = load_projects()
    if data:
        classifications = {}
        for project in data["projects"]:
            print(f"\n正在分类开标项目: {project['prjName']}")
            result = classify_project(client, project['prjName'])
            classifications[project['bulletinId']] = result['prjType']
            print(f"分类结果: {result['prjType']}")
            time.sleep(1)
        update_projects(data, classifications)
        save_projects(data)
        print("开标项目分类完成并已更新到 opening_projects.json")
    else:
        print("跳过开标项目分类：opening_projects.json 不存在或读取失败")

    # ================= 处理采购公告（purchase_bulletins.json） =================
    # 说明：
    # - 输入文件：purchase_bulletins.json
    # - 数据结构：[ {"bulletinTitle": str, "prjType": str, ...}, ... ]（顶层为数组）
    # - 分类依据：对每条公告的 bulletinTitle 进行大模型分类（classify_project）
    # - 输出效果：将分类结果写入每条公告对象的 prjType 字段
    # - 容错与降级：
    #   * 若文件缺失或解析失败：跳过该段处理
    #   * 若某条公告无标题：跳过该条
    #   * 若单次 API 调用异常：将 prjType 置为“其他项目”
    # - 限频处理：每次请求后 sleep(1) 以降低触发限频的概率
    purchase_data = load_purchase_bulletins()
    if purchase_data:
        for bulletin in purchase_data:
            title = bulletin.get('bulletinTitle') or ''
            if not title:
                continue
            print(f"\n正在分类采购公告: {title}")
            result = classify_project(client, title)
            bulletin['prjType'] = result.get('prjType', '其他项目')
            print(f"分类结果: {bulletin['prjType']}")
            time.sleep(1)
        save_purchase_bulletins(purchase_data)
        print("采购公告分类完成并已更新到 purchase_bulletins.json")
    else:
        print("跳过采购公告分类：purchase_bulletins.json 不存在或读取失败")

if __name__ == "__main__":
    main()