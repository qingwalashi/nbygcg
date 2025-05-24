import json
from openai import OpenAI
import time
import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

def load_projects():
    try:
        with open('date_prj.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print("Error: date_prj.json not found")
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
            model="Qwen/Qwen3-8B",
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
    with open('date_prj.json', 'w', encoding='utf-8') as file:
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

    # 加载项目数据
    data = load_projects()
    if not data:
        return

    # 存储分类结果
    classifications = {}
    
    # 对每个项目进行分类
    for project in data["projects"]:
        print(f"\n正在分类项目: {project['prjName']}")
        result = classify_project(client, project['prjName'])
        classifications[project['bulletinId']] = result['prjType']
        print(f"分类结果: {result['prjType']}")
        # 添加延时以避免API限制
        time.sleep(1)

    # 更新项目数据
    update_projects(data, classifications)
    
    # 保存更新后的数据
    save_projects(data)
    print("项目分类完成并已更新到date_prj.json")

if __name__ == "__main__":
    main() 