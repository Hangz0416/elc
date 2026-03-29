import os
import subprocess
import sys

def get_python_executable():
    """返回当前环境的Python可执行文件路径"""
    # 在虚拟环境中，sys.executable 指向正确的解释器
    # 在非虚拟环境中，它也应该是正确的
    return sys.executable

def get_script_and_dir(method: str) -> tuple[str, str]:
    """根据方法名称返回对应的脚本名和工作目录。"""
    if method in ["MSMG", "MFTG"]:
        script_dir = "src/Thermal-Gaussian-main"
        script_name = "train_MFTG.py" if method == "MFTG" else "train_MSMG.py"
    elif method == "OMMG":
        script_dir = "src/OMMG"
        script_name = "train-OMMG.py"
    else:
        raise ValueError(f"未知的重建方法: {method}")
    return script_name, script_dir

def run_reconstruction(source_path: str, output_path: str, method: str) -> tuple[str, str, list[str], list[str]]:
    """
    根据指定方法执行三维重建过程，并实时打印输出。

    此函数调用 Thermal-Gaussian-main 项目中的训练脚本来处理给定的数据集，
    并生成一个三维点云模型。它会实时将子进程的输出流式传输到控制台。
    训练成功后，它会自动调用渲染脚本生成预览图。

    Args:
        source_path (str): 包含重建所需数据（如 rgb, thermal, sparse 子目录）的源目录路径。
        output_path (str): 用于保存训练输出（包括模型）的目录路径。
        method (str): 要使用的重建方法 ('MSMG', 'MFTG', 'OMMG')。

    Returns:
        tuple[str, str, list[str], list[str]]: 包含彩色模型路径、热成像模型路径、彩色渲染图URL列表和热成像渲染图URL列表的元组。

    Raises:
        FileNotFoundError: 如果训练脚本或数据源路径不存在。
        RuntimeError: 如果重建子进程执行失败。
    """
    # 根据方法获取脚本和工作目录
    train_script_name, script_dir = get_script_and_dir(method)
    train_script_path = os.path.join(script_dir, train_script_name)

    # 渲染脚本路径固定在 Thermal-Gaussian-main 中
    if train_script_name in ["train_MFTG.py", "train_MSMG.py"]:
        render_script_path = "src/Thermal-Gaussian-main/render.py"
    elif train_script_name == "train-OMMG.py":
        render_script_path = "src/OMMG/render.py"

    # 检查所需文件和目录是否存在
    if not os.path.exists(train_script_path):
        raise FileNotFoundError(f"训练脚本未找到: {train_script_path}")
    if not os.path.exists(render_script_path):
        raise FileNotFoundError(f"渲染脚本未找到: {render_script_path}")
    if not os.path.isdir(source_path):
        raise FileNotFoundError(f"数据源路径未找到: {source_path}")

    # 获取当前环境的 Python 解释器
    python_executable = get_python_executable()

    # 构建训练命令。工作目录将是脚本所在的目录，因此脚本名称可以直接使用。
    command = [
        python_executable,
        train_script_name, # 使用脚本名，而不是完整路径
        "-s", os.path.abspath(source_path),
        "-m", os.path.abspath(output_path),
        "--no_gui" # 禁用GUI以允许后端执行并看到进度
    ]

    print(f"正在执行重建命令: {' '.join(command)}")
    print(f"工作目录: {os.path.abspath(script_dir)}")

    # 使用 Popen 启动子进程，并让其输出直接显示在当前终端
    # 这样 tqdm 进度条才能正常渲染
    process = subprocess.Popen(
        command,
        cwd=os.path.abspath(script_dir)
    )

    # 等待进程结束并获取返回码
    process.wait()

    # 检查进程是否成功完成
    if process.returncode != 0:
        # 错误信息已经直接打印到终端，这里只抛出异常
        raise RuntimeError(f"重建子进程失败，返回码: {process.returncode}。请查看上面终端的错误输出。")

    print("\n重建过程成功完成。")
    
    # --- 开始执行渲染 ---
    print("\n[INFO] 训练完成，开始执行渲染...")
    iteration_to_render = 30000

    render_script_dir = os.path.dirname(render_script_path)
    render_script_name_only = os.path.basename(render_script_path)
    
    render_command = [
        python_executable,
        render_script_name_only, # 只使用脚本名
        "-m", os.path.abspath(output_path),
        "-s", os.path.abspath(source_path),
        "--iteration", str(iteration_to_render),
        "--skip_train" # 只渲染测试视角的图像
    ]

    print(f"正在执行渲染命令: {' '.join(render_command)}")
    
    # 使用 run 来执行渲染，它的工作目录是渲染脚本所在的目录
    render_process = subprocess.run(
        render_command,
        cwd=os.path.abspath(render_script_dir),
        capture_output=True, # 捕获输出
        text=True
    )

    if render_process.returncode != 0:
        print("[ERROR] 渲染失败。")
        print(f"STDERR: {render_process.stderr}")
        # 即使渲染失败，我们仍然可以返回模型，所以这里只打印警告而不是抛出异常
    else:
        print("[INFO] 渲染成功。")
        print(f"STDOUT: {render_process.stdout}")

    # --- 收集结果路径 ---
    
    # 1. 查找彩色和热成像的模型文件路径
    color_model_path = find_model_file(output_path, iteration_to_render, "color", method)
    thermal_model_path = find_model_file(output_path, iteration_to_render, "thermal", method)

    # 2. 查找渲染的图片
    color_rendered_urls = collect_rendered_images(output_path, iteration_to_render, "rgb_test", method)
    thermal_rendered_urls = collect_rendered_images(output_path, iteration_to_render, "thermal_test", method)

    print(f"返回彩色模型文件路径: {color_model_path or '未找到'}")
    print(f"返回热成像模型文件路径: {thermal_model_path or '未找到'}")
    print(f"返回彩色渲染图片URL: {color_rendered_urls}")
    print(f"返回热成像渲染图片URL: {thermal_rendered_urls}")
    
    return color_model_path, thermal_model_path, color_rendered_urls, thermal_rendered_urls


def find_model_file(output_path: str, iteration: int, model_type: str, method: str) -> str:
    """在输出目录中查找生成的点云模型文件，适配不同方法。"""
    
    point_cloud_subdir = ""
    # OMMG方法只生成一个统一的点云，不区分color和thermal
    if method == "OMMG":
        # 对于OMMG，我们只查找主点云一次
        if model_type == "thermal":
            return "" # 避免重复查找和返回
        # 根据用户提供的文件夹结构
        point_cloud_subdir = f"point_cloud/iteration_{iteration}"
    else: # MSMG, MFTG
        point_cloud_subdir = f"point_cloud_{model_type}/iteration_{iteration}"

    model_file_path = os.path.join(
        os.path.abspath(output_path), 
        point_cloud_subdir,
        "point_cloud.ply"
    )

    if not os.path.exists(model_file_path):
        print(f"警告: 在预期路径未找到 {model_type} 模型文件: {model_file_path}")
        # 如果在预期的路径找不到文件，尝试查找最新的迭代
        point_cloud_dir = os.path.join(os.path.abspath(output_path), point_cloud_subdir)
        if os.path.isdir(point_cloud_dir):
            iterations = [d for d in os.listdir(point_cloud_dir) if d.startswith('iteration_')]
            if iterations:
                # 按迭代次数排序找到最新的
                latest_iteration_dir = max(iterations, key=lambda d: int(d.split('_')[1]))
                latest_model_path = os.path.join(point_cloud_dir, latest_iteration_dir, "point_cloud.ply")
                if os.path.exists(latest_model_path):
                    print(f"找到最新迭代的 {model_type} 模型: {latest_model_path}")
                    return latest_model_path
        return "" # 返回空字符串表示未找到

    return model_file_path

def check_and_get_existing_results(output_path: str, method: str) -> tuple | None:
    """
    检查给定输出路径中是否已存在指定方法的完整重建结果。
    如果存在，则收集并返回所有结果的路径；否则返回 None。
    """
    print(f"正在检查 '{method}' 方法的已存在结果: {output_path}")
    iteration_to_check = 30000

    if not os.path.isdir(output_path):
        return None

    color_model_path = find_model_file(output_path, iteration_to_check, "color", method)
    thermal_model_path = find_model_file(output_path, iteration_to_check, "thermal", method)

    # 核心判断：只要有一个模型文件存在，就认为结果是有效的缓存
    if color_model_path or thermal_model_path:
        print("发现有效的缓存结果。")
        color_rendered_urls = collect_rendered_images(output_path, iteration_to_check, "rgb_test", method)
        thermal_rendered_urls = collect_rendered_images(output_path, iteration_to_check, "thermal_test", method)
        
        return color_model_path, thermal_model_path, color_rendered_urls, thermal_rendered_urls
    
    print("未找到有效的缓存结果。")
    return None

def collect_rendered_images(output_path: str, iteration: int, render_type: str, method: str) -> list[str]:
    """收集指定类型的渲染图片URL，适配不同方法。"""
    
    renders_subdir = ""
    if method == "OMMG":
        # 根据OMMG的render.py脚本逻辑
        if render_type == "rgb_test":
            renders_subdir = f"test/ours_{iteration}/renders_color"
        elif render_type == "thermal_test":
            renders_subdir = f"test/ours_{iteration}/renders_thermal"
    else: # MSMG, MFTG
        renders_subdir = f"{render_type}/ours_{iteration}/renders"

    if not renders_subdir:
        return []

    rendered_image_urls = []
    renders_dir = os.path.join(output_path, renders_subdir)
    if os.path.isdir(renders_dir):
        image_files = sorted([f for f in os.listdir(renders_dir) if f.endswith(".png")])
        for img_file in image_files:
            relative_path = os.path.relpath(os.path.join(renders_dir, img_file), os.getcwd())
            # 转换为Web URL格式
            url_path = f"/{relative_path.replace(os.path.sep, '/')}"
            rendered_image_urls.append(url_path)
    return rendered_image_urls 