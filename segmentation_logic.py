import os
import subprocess
import sys
from glob import glob

def get_python_executable():
    """返回当前环境的Python可执行文件路径"""
    return sys.executable

def _run_command(command: list[str], cwd: str, error_message: str):
    """通用命令执行函数"""
    print(f"工作目录: {os.path.abspath(cwd)}")
    print(f"正在执行命令: {' '.join(command)}")
    try:
        process = subprocess.run(
            command,
            cwd=os.path.abspath(cwd),
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8' # 明确编码
        )
        print(f"[INFO] 子进程成功完成。")
        print(f"STDOUT: {process.stdout}")
        if process.stderr:
            print(f"STDERR: {process.stderr}")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {error_message}，返回码: {e.returncode}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        raise RuntimeError(f"{error_message}。请查看后端日志获取详细信息。")

def _run_bash_command(script_path_relative_to_cwd: str, args: list[str], cwd: str):
    """
    通用bash脚本执行函数，支持实时流式输出。
    :param script_path_relative_to_cwd: 要执行的脚本路径，相对于 cwd。
    :param args: 脚本的参数列表。
    :param cwd: 命令的执行目录 (Working Directory)。
    """
    command = ["bash", script_path_relative_to_cwd] + args
    
    print(f"工作目录: {os.path.abspath(cwd)}")
    print(f"正在执行命令: {' '.join(command)}")
    
    # 使用 Popen 以实时流式传输输出，这对于tqdm等进度条至关重要
    process = subprocess.Popen(
        command,
        cwd=os.path.abspath(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # 将 stderr 重定向到 stdout 以捕获tqdm的输出
        text=True,
        encoding='utf-8',
        bufsize=1,  # 行缓冲
    )

    # 实时读取并打印输出
    if process.stdout:
        for line in iter(process.stdout.readline, ''):
            # 使用 sys.stdout.write 和 flush 来正确处理像 tqdm 这样的动态行更新
            sys.stdout.write(line)
            sys.stdout.flush()

    # 等待子进程结束
    process.wait()

    # 检查最终的返回码
    if process.returncode != 0:
        error_message = f"脚本 '{os.path.basename(script_path_relative_to_cwd)}' 执行失败"
        # 错误信息已经实时打印，这里只在最后总结并抛出异常
        print(f"\n[ERROR] {error_message}，返回码: {process.returncode}")
        raise RuntimeError(f"{error_message}。请查看上面终端的错误输出。")
    
    print(f"\n[INFO] 脚本 '{os.path.basename(script_path_relative_to_cwd)}' 成功完成。")

def check_and_get_segmentation_results(output_path: str) -> list[dict[str, str]] | None:
    """
    检查分割结果是否存在，如果存在则直接返回 gt_objects_color 和 gt 图像的 URL 对。
    """
    # 查找 gt_objects_color 目录
    gt_color_dir_pattern = os.path.join(output_path, "*", "ours_*", "gt_objects_color")
    
    potential_dirs = glob(gt_color_dir_pattern)
    if not potential_dirs:
        print(f"在 '{output_path}' 中未找到缓存的 'gt_objects_color' 结果。")
        return None
    
    latest_gt_color_dir = max(potential_dirs, key=os.path.getmtime)
    print(f"发现缓存的真实分割结果: {latest_gt_color_dir}")
    
    # 推断出对应的 gt 目录
    latest_gt_dir = latest_gt_color_dir.replace("gt_objects_color", "gt")
    if not os.path.isdir(latest_gt_dir):
        print(f"警告: 找到了 gt_objects_color 目录，但未找到对应的 gt 目录: {latest_gt_dir}")
        return None

    gt_color_files = sorted([f for f in os.listdir(latest_gt_color_dir) if f.endswith(".png")])
    if not gt_color_files:
        return None

    # 创建 URL 对
    result_pairs = []
    for img_file in gt_color_files[:5]: # 只处理前5张
        gt_color_path = os.path.join(latest_gt_color_dir, img_file)
        gt_path = os.path.join(latest_gt_dir, img_file)

        # 确保对应的gt文件也存在
        if os.path.exists(gt_path):
            gt_color_url = f"/{os.path.relpath(gt_color_path, os.getcwd()).replace(os.path.sep, '/')}"
            gt_url = f"/{os.path.relpath(gt_path, os.getcwd()).replace(os.path.sep, '/')}"
            
            result_pairs.append({
                "gt_color_url": gt_color_url,
                "gt_url": gt_url
            })
    
    return result_pairs

def run_segmentation(scene_name: str, scale: int = 1):
    """
    执行完整的场景分割流程：准备数据 -> 训练 -> 渲染。
    如果最终结果已存在，则跳过所有步骤直接返回。
    """
    source_dir = os.path.abspath(f"static/reconstruction_data/RGBT-Scenes/{scene_name}")
    output_dir = os.path.abspath(f"static/segmentation/{scene_name}")
    gaussian_grouping_dir = "src/gaussian-grouping"
    
    # --- 0. 缓存检查 ---
    cached_results = check_and_get_segmentation_results(output_dir)
    if cached_results:
        print(f"场景 '{scene_name}' 的分割结果已缓存，直接返回。")
        return cached_results

    # --- 1. 准备伪标签 (Masks) ---
    mask_dir = os.path.join(source_dir, "object_mask")
    if os.path.exists(mask_dir) and len(os.listdir(mask_dir)) > 0:
        print(f"场景 '{scene_name}' 的Mask已存在，跳过生成步骤。")
    else:
        print(f"正在为场景 '{scene_name}' 生成Mask...")
        prepare_script = "script/prepare_pseudo_label.sh"
        _run_bash_command(prepare_script, [source_dir, str(scale)], cwd=gaussian_grouping_dir)

    # --- 2. 训练并渲染模型 ---
    print(f"正在训练和渲染场景 '{scene_name}' 的分割模型...")
    train_script = "script/train.sh"
    _run_bash_command(train_script, [scene_name, str(scale)], cwd=gaussian_grouping_dir)

    # --- 3. 收集并返回结果 ---
    final_results = check_and_get_segmentation_results(output_dir)
    if not final_results:
        raise RuntimeError("分割流程执行完毕，但未在预期位置找到渲染结果。")
        
    return final_results 