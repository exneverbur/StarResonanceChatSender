import pyautogui
import pyperclip
import time
import re
import os
import random

# ================== 文件定义 ==================
CONFIG_FILE = "config.txt"
ORIGINAL_FILE = "file.txt"
TEMP_FILE = "file_temp.txt"

# 默认配置（仅在配置文件缺失时使用）
DEFAULT_CONFIG = {
    'max_length': 60,
    'initial_wait': 5,
    'base_interval': 3,
    'random_extra_min': 0.5,
    'random_extra_max': 2.0,
    'break_punctuation': '，。！？；：… '  # 注意结尾空格表示在空格处分段
}

def load_config():
    """加载配置文件，若不存在则生成默认文件"""
    if not os.path.exists(CONFIG_FILE):
        print("未找到配置文件，正在生成默认 config.txt...")
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            f.write('# 聊天发送器配置文件\n')
            f.write('# 请勿删除行首的 "参数名="\n\n')
            f.write(f'# 每段最大字符数（建议 40-80）\n')
            f.write(f'max_length={DEFAULT_CONFIG["max_length"]}\n\n')
            f.write(f'# 启动后等待时间（秒）\n')
            f.write(f'initial_wait={DEFAULT_CONFIG["initial_wait"]}\n\n')
            f.write(f'# 基础发送间隔（秒）\n')
            f.write(f'base_interval={DEFAULT_CONFIG["base_interval"]}\n\n')
            f.write(f'# 额外随机延迟：最小,最大（单位：秒）\n')
            f.write(f'random_extra_min={DEFAULT_CONFIG["random_extra_min"]}\n')
            f.write(f'random_extra_max={DEFAULT_CONFIG["random_extra_max"]}\n\n')
            f.write(f'# 分段断点符号（程序会优先在这些符号后断开）\n')
            f.write(f'# 支持中文、英文标点，空格表示句子结束\n')
            f.write(f'break_punctuation={DEFAULT_CONFIG["break_punctuation"]}\n')
        print(f"已生成默认配置文件：{CONFIG_FILE}")

    config = DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if key in config:
                        if key in ['max_length', 'initial_wait', 'base_interval']:
                            config[key] = int(value)
                        elif key in ['random_extra_min', 'random_extra_max']:
                            config[key] = float(value)
                        elif key == 'break_punctuation':
                            config[key] = value
    except Exception as e:
        print(f"读取配置文件失败，使用默认设置：{e}")

    return config


def ensure_temp_file():
    """确保临时副本存在，基于原始文件创建"""
    if not os.path.exists(ORIGINAL_FILE):
        print(f"错误：原始文件不存在：{ORIGINAL_FILE}")
        print(f"请在同一目录下创建 {ORIGINAL_FILE} 并写入文本。")
        return False

    if not os.path.exists(TEMP_FILE):
        with open(ORIGINAL_FILE, 'r', encoding='utf-8') as src:
            content = src.read()
        with open(TEMP_FILE, 'w', encoding='utf-8') as dst:
            dst.write(content)
        print(f"已创建临时副本：{TEMP_FILE}")
    return True


def read_and_smart_split(file_path, max_length=80, break_punct='，。！？；：… '):
    """智能分段：优先在指定标点符号后断开"""
    if not os.path.exists(file_path):
        return []

    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # 统一空白字符
    text = re.sub(r'\s+', ' ', text).strip()
    if not text:
        return []

    segments = []
    while text:
        if len(text) <= max_length:
            segments.append(text)
            break

        # 尝试在 max_length 附近找断点
        cut_point = max_length
        found = False
        # 从 max_length 向前最多 20 个字符查找
        start = max(max_length - 20, 0)
        for i in range(max_length, start - 1, -1):
            if i < len(text) and text[i] in break_punct:
                cut_point = i + 1
                found = True
                break

        if not found:
            cut_point = max_length  # 兜底：强制截断

        segment = text[:cut_point].strip()
        if segment:
            segments.append(segment)
        text = text[cut_point:].strip()

    return segments


def remove_sent_segment_from_temp(sent_segment):
    """从临时文件中删除已发送的段落"""
    if not os.path.exists(TEMP_FILE):
        return

    with open(TEMP_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    cleaned_content = re.sub(r'\s+', ' ', content).strip()
    cleaned_segment = re.sub(r'\s+', ' ', sent_segment).strip()

    if cleaned_content.startswith(cleaned_segment):
        new_content = cleaned_content[len(cleaned_segment):].strip()
        with open(TEMP_FILE, 'w', encoding='utf-8') as f:
            f.write(new_content)


def send_segments(config, segments):
    """发送所有段落"""
    print(f"共 {len(segments)} 段待发送。")
    print(f"请在 {config['initial_wait']} 秒内点击目标输入框...")
    time.sleep(config['initial_wait'])

    for i, seg in enumerate(segments, 1):
        print(f"发送第 {i}/{len(segments)} 段: {seg[:30]}...")

        # 复制并粘贴
        pyperclip.copy(seg)
        pyautogui.hotkey('ctrl', 'v')  # Windows
        pyautogui.press('enter')

        # 删除已发送内容
        remove_sent_segment_from_temp(seg)

        # 计算延迟
        if i < len(segments):
            extra_delay = random.uniform(config['random_extra_min'], config['random_extra_max'])
            total_delay = config['base_interval'] + extra_delay
            print(f"等待 {total_delay:.1f} 秒后发送下一段...")
            time.sleep(total_delay)
        else:
            print("所有文本已发送完毕。")

    # 清理空的 temp 文件
    if os.path.exists(TEMP_FILE):
        with open(TEMP_FILE, 'r', encoding='utf-8') as f:
            if not f.read().strip():
                os.remove(TEMP_FILE)
                print("临时副本已清空并删除。")


# ============ 主程序入口 ============
if __name__ == "__main__":
    print("聊天发送器启动中...")

    # 加载配置
    config = load_config()

    # 确保临时文件存在
    if not ensure_temp_file():
        input("按回车键退出...")
        exit()

    # 智能分段
    segments = read_and_smart_split(
        TEMP_FILE,
        max_length=config['max_length'],
        break_punct=config['break_punctuation']
    )

    if not segments:
        print("临时文件无内容可发送。")
        input("按回车键退出...")
        exit()

    # 发送段落
    try:
        send_segments(config, segments)
    except KeyboardInterrupt:
        print("\n发送已中断。")
        print(f"剩余内容保留在：{TEMP_FILE}")
    except Exception as e:
        print(f"运行出错：{e}")
