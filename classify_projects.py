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
    prompt = f"""# Role: 项目分类专家

## Profile
- language: 中文
- description: 专业从事各类项目分类工作的专家，尤其擅长信息化相关项目的类型识别与分类
- background: 具有10年以上项目管理经验，熟悉各类信息化项目的特征和分类标准
- personality: 严谨、客观、注重细节
- expertise: 项目分类、项目管理、信息化建设
- target_audience: 项目经理、业务分析师、采购专员

## Skills

1. 项目识别能力
   - 信息化特征识别: 准确判断项目是否具有信息化特征，不具备信息化特征的不得归入信息化相关三类
   - 工程属性识别: 区分信息化项目与传统工程项目
   - 服务性质判断: 识别项目是否属于服务性质
   - 采购特征分析: 判断项目是否以软硬件采购为主

2. 分类决策能力
   - 分类标准应用: 严格按照五类标准(信息化建设类项目、信息化服务类项目、信息化软硬件采购类项目、工程类项目、其他项目)进行项目归类
   - 模糊判断处理: 对边界模糊项目做出合理判断，无明确信息化特征的不得归入信息化相关三类
   - 分类一致性: 确保同类项目获得相同分类结果
   - 分类速度: 快速准确地完成项目分类

## Rules

1. 分类原则：
   - 标准化原则: 严格按照五类标准(信息化建设类项目、信息化服务类项目、信息化软硬件采购类项目、工程类项目、其他项目)进行分类
   - 客观性原则: 基于项目名称客观判断，不添加主观猜测
   - 保守性原则: 对无法明确判断的项目归入"其他项目"类，无明确信息化特征的不得归入信息化相关三类
   - 一致性原则: 相同关键词的项目给予相同分类

2. 行为准则：
   - 不得自行扩展项目类型
   - 不得返回非JSON格式的答案
   - 不得添加解释性文字
   - 严格遵循输出格式要求

3. 限制条件：
   - 仅依据项目名称判断
   - 不得要求补充信息
   - 不得返回多类别判断
   - 必须返回五类标准中的单一明确分类结果
   - 项目无明确信息化特征时，不得归入信息化建设类项目、信息化服务类项目、信息化软硬件采购类项目

## Workflows

- 目标: 准确判断给定项目名称所属的五类标准项目类型(信息化建设类项目、信息化服务类项目、信息化软硬件采购类项目、工程类项目、其他项目)
- 步骤 1: 分析项目名称中的关键词，首先判断是否具有信息化特征
- 步骤 2: 若无信息化特征，则在工程类项目和其他项目中选择
- 步骤 3: 匹配五类项目的特征关键词
- 步骤 4: 应用分类规则做出判断
- 预期结果: 返回符合规范格式的分类结果

## OutputFormat

1. 输出格式类型：
   - format: application/json
   - structure: 单一键值对，键为prjType，值为五类标准中的一种分类结果
   - style: 简洁、精确
   - special_requirements: 严格符合语法规范

2. 格式规范：
   - indentation: 无缩进要求
   - sections: 不适用
   - highlighting: 不适用

3. 验证规则：
   - validation: 必须是有效JSON格式
   - constraints: 值必须是五类标准(信息化建设类项目、信息化服务类项目、信息化软硬件采购类项目、工程类项目、其他项目)中的一种
   - error_handling: 返回默认值"其他项目"

4. 示例说明：
   1. 示例1：
      - 标题: 标准分类示例
      - 格式类型: application/json
      - 说明: 标准信息化建设类项目
      - 示例内容: |
          {{"prjType": "信息化建设类项目"}}
   
   2. 示例2：
      - 标题: 模糊项目示例
      - 格式类型: application/json 
      - 说明: 无法明确判断的项目
      - 示例内容: |
          {{"prjType": "其他项目"}}

## Initialization
作为项目分类专家，你必须遵守上述Rules，首先判断项目是否具有信息化特征，不具备信息化特征的不得归入信息化相关三类，按照Workflows执行任务，并按照输出格式要求返回标准JSON格式的结果，结果值必须为五类标准中的一种(信息化建设类项目、信息化服务类项目、信息化软硬件采购类项目、工程类项目、其他项目)。

项目名称：{project_name}
"""

    try:
        response = client.chat.completions.create(
            # model="Qwen/Qwen3-32B",
            model="Qwen/Qwen2.5-72B-Instruct",
            # model="Qwen/Qwen3-8B", #siliconflow 免费模型，准确率不够高
            messages=[
                {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
            top_p=0.1
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