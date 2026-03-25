import os
import torch
from torchvision import transforms
from PIL import Image
import numpy as np
import cv2
import uuid
import re # 导入正则表达式模块
from skimage.metrics import structural_similarity as ssim

# 从 EAEFNet 项目中导入模型定义
from src.EAEFNet.EAEFNet_ImageFusion_Only.EAEFNet_ImageFusion import FA_encoder_IDAM

# --- 全局变量，用于缓存模型 ---
device = None
fusion_model = None

def setup_fusion_model(weights_path="src/EAEFNet/checkpoints/idam_resnet152/EAEFNet.pth"):
    """
    加载并初始化 EAEFNet 融合模型。
    此函数应该在FastAPI应用启动时调用一次。
    """
    global device, fusion_model
    
    if fusion_model is not None:
        print("模型已经加载。")
        return

    print("正在加载 EAEFNet 图像融合模型...")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # 1. 加载 EAEFNet/IDAM 模型
    # 使用 50 层的 ResNet，因为这在许多研究中是常见基线
    fusion_model = FA_encoder_IDAM(num_resnet_layers=50).to(device)
    
    # 2. 加载预训练权重
    if not os.path.exists(weights_path):
        # 由于我们知道权重文件当前缺失，这里只打印警告而不抛出错误
        print(f"警告: 找不到预训练权重文件: {weights_path}")
        print("模型将以随机权重运行。请将 'EAEFNet.pth' 放入 'src/EAEFNet/checkpoints/idam_resnet152' 目录。")
    else:
        checkpoint = torch.load(weights_path, map_location=device)
        # 从检查点加载模型状态
        # 有些检查点会将模型保存在 'model_state_dict'键下
        # 添加 strict=False 来忽略不匹配的键
        fusion_model.load_state_dict(
            checkpoint.get('model_state_dict', checkpoint), 
            strict=False
        )
        print(f"成功加载模型权重: {weights_path}")

    fusion_model.eval()
    
    print(f"模型加载完成，运行在设备: {device}")


def run_fusion(rgb_paths: list[str], thermal_paths: list[str], text_prompt: str, scene_name: str, original_rgb_filenames: list[str]):
    """
    对一批图像执行融合，并将其直接保存到三维重建数据目录中。
    注意：此模型不使用文本提示，'text_prompt' 参数将被忽略。

    :param rgb_paths: 可见光图像的路径列表。
    :param thermal_paths: 红外图像的路径列表。
    :param text_prompt: 文本引导 (在此模型中被忽略)。
    :param scene_name: 用户定义的场景名称, 用于定位到 '.../RGBT-Scenes/{scene_name}/msx' 目录。
    :param original_rgb_filenames: 原始上传的RGB文件名列表，用于命名输出文件。
    :return: 包含融合后图像信息的字典列表。
    """
    if fusion_model is None:
        raise RuntimeError("模型未初始化。请先调用 setup_fusion_model()。")

    print(f"开始 EAEFNet 批量融合任务，并将结果存入场景 '{scene_name}' 的msx文件夹。")

    # 新：根据场景名称直接定位到三维重建数据目录
    save_dir = os.path.join("static", "reconstruction_data", "RGBT-Scenes", scene_name, "msx")
    
    # 检查基础场景目录是否存在，以防用户选择了无效的场景
    base_scene_path = os.path.dirname(save_dir) # 获取 .../{scene_name}/ 目录
    if not os.path.isdir(base_scene_path):
        raise FileNotFoundError(f"指定的重建场景目录不存在: {base_scene_path}。请确保场景名称正确，并且该场景已存在于 'static/reconstruction_data/RGBT-Scenes/' 中。")

    os.makedirs(save_dir, exist_ok=True)

    with torch.no_grad():
        # 1. 定义图像变换
        image_size = (480, 640)
        transform = transforms.Compose([
            transforms.Resize(image_size),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

        # 2. 读取所有图像，并准备批处理张量
        rgb_tensors = []
        thermal_tensors = []
        original_pils = []  # 保存原始PIL图像，用于后续调整尺寸和融合

        for rgb_path, thermal_path in zip(rgb_paths, thermal_paths):
            rgb_pil = Image.open(rgb_path).convert("RGB")
            thermal_pil = Image.open(thermal_path).convert("RGB")
            
            # 预处理并暂存
            rgb_tensors.append(transform(rgb_pil))
            thermal_tensors.append(transform(thermal_pil))
            original_pils.append((rgb_pil, thermal_pil))

        # 将张量列表堆叠成一个批处理张量
        rgb_batch = torch.stack(rgb_tensors).to(device)
        thermal_batch = torch.stack(thermal_tensors).to(device)

        # 3. 执行模型推理 (一次性处理整个批次)
        fused_features_batch = fusion_model(rgb_batch, thermal_batch)
        
        # 4. 后处理 - 遍历批次中的每个结果
        best_features_batch = fused_features_batch[3] # 形状: (B, C, H, W)
        
        results = []
        for i in range(len(rgb_paths)):
            # a. 为第i张图像提取注意力图
            best_feature = best_features_batch[i] # 形状: (C, H, W)
            attention_map = torch.mean(best_feature, dim=0).cpu().numpy()
            attention_map = (attention_map - attention_map.min()) / (attention_map.max() - attention_map.min())

            # b. 调整尺寸并进行加权融合
            rgb_pil, thermal_pil = original_pils[i]
            original_size_pil = rgb_pil.size # (W, H)
            attention_map_resized = cv2.resize(attention_map, original_size_pil)
            
            rgb_array = np.array(rgb_pil)
            thermal_array = np.array(thermal_pil) # 获取对应的热成像图
            
            attention_weight = np.expand_dims(attention_map_resized, axis=2)
            fused_image_np = (rgb_array * attention_weight + thermal_array * (1 - attention_weight)).astype(np.uint8)

            # c. 保存图像 (新的命名和路径逻辑)
            original_filename = original_rgb_filenames[i]
            
            # 检查并转换扩展名为.jpg，以保持文件夹内格式统一
            base_name, _ = os.path.splitext(original_filename)
            output_filename_jpg = f"{base_name}.jpg"

            output_path = os.path.join(save_dir, output_filename_jpg)
            
            # 使用Pillow保存为JPEG格式
            Image.fromarray(fused_image_np).save(output_path, 'JPEG')
            
            web_path = f"/{output_path.replace(os.path.sep, '/')}"

            # d. 计算新指标
            ag = calculate_ag(fused_image_np)
            sd = calculate_sd(fused_image_np)
            # VIF通常需要将融合图像与源图像进行比较，这里我们与RGB图比较
            vif = calculate_vif(fused_image_np, rgb_array)

            # e. 收集结果
            results.append({
                "original_filename": original_filename,
                "fused_image": web_path,
                "metrics": { "ag": ag, "sd": sd, "vif": vif }
            })

        print(f"批量融合完成，成功处理 {len(results)} 张图像。")
        return results


# --- 辅助函数与指标计算 ---

def calculate_ag(image_np):
    """计算平均梯度 (Average Gradient)"""
    if image_np.ndim == 3:
        image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
    
    height, width = image_np.shape
    gradient_x = np.diff(image_np, axis=1)
    gradient_y = np.diff(image_np, axis=0)
    
    ag = np.sqrt((np.sum(gradient_x**2) + np.sum(gradient_y**2)) / ((height-1)*(width-1)))
    return round(ag, 4)


def calculate_sd(image_np):
    """计算标准差 (Standard Deviation)"""
    if image_np.ndim == 3:
        image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
    return round(np.std(image_np), 4)

# VIF的实现比较复杂，这里我们使用一个简化的占位符函数。
# 在实际研究中，通常会使用一个成熟的库或已发表的论文中的实现。
def calculate_vif(image1_np, image2_np):
    """计算视觉信息保真度 (Visual Information Fidelity) - 简化版"""
    # 这是一个非常简化的版本，仅用于演示。
    # 真实的VIF计算要复杂得多，涉及多尺度分析和高斯混合模型。
    if image1_np.ndim == 3:
        image1_np = cv2.cvtColor(image1_np, cv2.COLOR_RGB2GRAY)
    if image2_np.ndim == 3:
        image2_np = cv2.cvtColor(image2_np, cv2.COLOR_RGB2GRAY)
        
    # 使用结构相似性(SSIM)作为VIF的近似值
    vif_approx = ssim(image1_np, image2_np, data_range=image1_np.max() - image1_np.min())
    return round(vif_approx, 4)


# 不再需要 tensor_to_numpy 和 save_image，因为融合逻辑已定制
# def tensor_to_numpy...
# def save_image...

def get_text_prompt(prompt_key: str, custom_text: str = None) -> str:
    """ 
    此函数保留是为了API兼容性，但其输出在新模型中不被使用。
    """
    if custom_text:
        return custom_text

    prompts = {
        "default": "This is the infrared and visible light image fusion task.",
        "low_light": "In the context of infrared-visible image fusion, visible images are susceptible to extremely low light degradation.",
        # ... (其他提示可以保留或删除)
    }
    return prompts.get(prompt_key, prompts["default"]) 