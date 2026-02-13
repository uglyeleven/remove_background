import os
import json
import requests
import time

# 配置
COMFY_URL = "http://127.0.0.1:8188"
WORKFLOW_JSON = r'E:\ComfyUI\ComfyUI-aki-v2\ComfyUI\user\default\workflows\removebackground_workflow_api.json'  # 你的 API JSON 文件路径

input_base = r"E:\ComfyUI\ComfyUI-aki-v2\ComfyUI\input\work\products"
output_base = r"E:\ComfyUI\ComfyUI-aki-v2\ComfyUI\input\work\output"

# 图片扩展名（根据你的图片类型调整）
IMAGE_EXTS = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']

# 函数：获取文件夹内图片数量
def get_num_images(folder_path):
    if not os.path.exists(folder_path):
        return 0
    files = os.listdir(folder_path)
    return len([f for f in files if os.path.isfile(os.path.join(folder_path, f)) and os.path.splitext(f)[1].lower() in IMAGE_EXTS])

with open(WORKFLOW_JSON, 'r', encoding='utf-8') as f:
    base_workflow = json.load(f)

for subfolder in os.listdir(input_base):
    sub_path = os.path.join(input_base, subfolder)
    if not os.path.isdir(sub_path):
        continue

    num_images = get_num_images(sub_path)
    if num_images == 0:
        print(f"跳过空文件夹: {subfolder}")
        continue

    print(f"处理文件夹: {subfolder} (共 {num_images} 张图片)")

    # 创建对应输出文件夹
    out_dir = os.path.join(output_base, subfolder).replace("\\", "/")
    os.makedirs(out_dir, exist_ok=True)

    # 逐张图片处理
    for i in range(num_images):
        print(f"  处理第 {i+1}/{num_images} 张")

        # 深拷贝工作流
        workflow = json.loads(json.dumps(base_workflow))

        # 修改 Load Image Batch (节点 54) 的路径和 index
        if "54" in workflow:
            workflow["54"]["inputs"]["path"] = sub_path.replace("\\", "/")
            workflow["54"]["inputs"]["index"] = i  # 动态改 index

        # 修改 Image Save (节点 55) 的输出路径
        if "55" in workflow:
            workflow["55"]["inputs"]["output_path"] = out_dir

        # 发送到 ComfyUI API
        payload = {"prompt": workflow}
        try:
            response = requests.post(f"{COMFY_URL}/prompt", json=payload, timeout=30)
            response.raise_for_status()
            prompt_id = response.json()["prompt_id"]
            print(f"    任务提交成功: {prompt_id}")

            # 等待完成（轮询 history）
            completed = False
            for _ in range(300):  # 最多等 25 分钟
                history_resp = requests.get(f"{COMFY_URL}/history/{prompt_id}")
                if history_resp.status_code == 200 and prompt_id in history_resp.json():
                    print(f"    完成第 {i+1} 张")
                    completed = True
                    break
                time.sleep(5)

            if not completed:
                print(f"    超时: 第 {i+1} 张 - 请检查 ComfyUI")

        except Exception as e:
            print(f"    处理第 {i+1} 张失败: {str(e)}")

print("所有文件夹处理完毕！")