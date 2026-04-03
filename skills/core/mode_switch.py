import os
import json
from datetime import datetime

CONFIG_FILE = "./skills/data/config.json"

def get_current_mode() -> str:
    """
    获取当前运行模式
    返回: "LIVING" 或 "LEGACY"
    """
    if not os.path.exists(CONFIG_FILE):
        return "LIVING" # 默认为生前模式

    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        config = json.load(f)
        
    # 检查是否触发“身后”条件
    # 例如：设置了“最后活跃时间”且当前时间超过该时间 + 宽限期
    last_active = config.get('last_active_timestamp', 0)
    legacy_trigger_days = config.get('legacy_trigger_days', 365) # 默认1年无活动转为身后模式
    
    current_time = datetime.now().timestamp()
    
    if current_time - last_active > (legacy_trigger_days * 86400):
        return "LEGACY"
    
    return "LIVING"

def update_activity():
    """更新最后活跃时间"""
    if not os.path.exists(CONFIG_FILE):
        config = {"last_active_timestamp": datetime.now().timestamp()}
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f)