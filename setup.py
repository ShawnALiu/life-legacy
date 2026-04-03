import os
import json
import sys
from datetime import datetime


def main():
    print("🌟 欢迎使用 life-legacy 初始化向导")
    print("这将帮助你构建你的数字生命档案。\n")

    name = input("请输入你的名字: ").strip()
    if not name:
        print("名字不能为空。")
        sys.exit(1)

    birth_year_str = input("请输入你的出生年份 (如 1990): ").strip()
    try:
        birth_year = int(birth_year_str)
    except ValueError:
        print("年份格式不正确，使用默认值 1990。")
        birth_year = 1990

    hometown = input("请输入你的家乡 (如 杭州): ").strip()

    data_dir = os.path.join(os.path.dirname(__file__), "skills", "data")
    os.makedirs(data_dir, exist_ok=True)

    config = {
        "user_name": name,
        "birth_year": birth_year,
        "hometown": hometown,
        "last_active_timestamp": 0,
        "legacy_trigger_days": 365,
    }

    config_path = os.path.join(data_dir, "config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

    timeline_path = os.path.join(data_dir, "timeline.json")
    if not os.path.exists(timeline_path) or os.path.getsize(timeline_path) == 0:
        timeline = {
            "meta": {
                "name": name,
                "birth_year": birth_year,
                "hometown": hometown,
            },
            "milestones": [],
        }
        with open(timeline_path, "w", encoding="utf-8") as f:
            json.dump(timeline, f, indent=4, ensure_ascii=False)
        print(f"\n📝 已创建空的 timeline.json，请添加你的人生大事记。")
    else:
        print(f"\n📝 timeline.json 已存在，跳过创建。")

    os.makedirs(os.path.join(data_dir, "diaries"), exist_ok=True)
    os.makedirs(os.path.join(data_dir, "chats"), exist_ok=True)
    os.makedirs(os.path.join(data_dir, "photos"), exist_ok=True)

    print(f"\n✅ 初始化成功！你的数字档案已创建于 {data_dir}")
    print(f"   用户: {name} | 出生: {birth_year} | 家乡: {hometown}")
    print("\n📂 目录结构:")
    print(f"   skills/data/diaries/   - 存放日记文件 (.md 或 .txt)")
    print(f"   skills/data/chats/     - 存放聊天记录 (.json)")
    print(f"   skills/data/photos/    - 存放照片描述文件 (.txt)")
    print(f"   skills/data/timeline.json - 人生大事记")
    print("\n🚀 启动方式:")
    print("   CLI:  python main.py")
    print("   Web:  uvicorn web.app:app --port 8000")


if __name__ == "__main__":
    main()
