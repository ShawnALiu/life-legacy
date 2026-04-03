import os
import json

def main():
    print("🌟 欢迎使用 life-legacy 初始化向导")
    print("这将帮助你构建你的数字生命档案。")
    
    name = input("请输入你的名字: ")
    birth_year = input("请输入你的出生年份: ")
    
    # 创建基础数据结构
    data_dir = "./skills/data"
    os.makedirs(data_dir, exist_ok=True)
    
    # 初始化配置文件
    config = {
        "user_name": name,
        "birth_year": int(birth_year),
        "last_active_timestamp": 0, # 0 表示尚未激活
        "legacy_trigger_days": 365
    }
    
    with open(os.path.join(data_dir, "config.json"), "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
        
    print(f"✅ 初始化成功！你的数字档案已创建于 {data_dir}")
    print("请记得在 timeline.json 中填入你的人生大事记。")

if __name__ == "__main__":
    main()