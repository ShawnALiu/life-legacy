import os
import json
import sys
from datetime import datetime
from typing import List, Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv

from skills.core.memory_manager import MemoryManager
from skills.core.mode_switch import get_current_mode, update_activity, CONFIG_FILE

load_dotenv()

DATA_DIR = os.path.join(os.path.dirname(__file__), "skills", "data")
CORE_DIR = os.path.join(os.path.dirname(__file__), "skills", "core")
MAX_HISTORY = 20


class DigitalTwin:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4")
        self.memory_manager = MemoryManager(DATA_DIR)
        self.config = self._load_config()
        self.conversation_history: List[Dict] = []

    def _load_config(self) -> dict:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _build_system_prompt(self) -> str:
        system_prompt_path = os.path.join(CORE_DIR, "system_prompt.md")
        with open(system_prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()

        birth_year = self.config.get("birth_year", 1990)
        current_year = datetime.now().year
        age = current_year - birth_year

        mode = get_current_mode()
        mode_display = "Living Mode" if mode == "LIVING" else "Legacy Mode"

        prompt = prompt_template.replace("{{user_name}}", self.config.get("user_name", "User"))
        prompt = prompt.replace("{{current_mode}}", mode_display)
        prompt = prompt.replace("{{current_date}}", datetime.now().strftime("%Y-%m-%d"))
        prompt = prompt.replace("{{calculated_age}}", str(age))

        values_path = os.path.join(DATA_DIR, "values.md")
        if os.path.exists(values_path):
            with open(values_path, "r", encoding="utf-8") as f:
                prompt += "\n\n## Personal Values\n" + f.read()

        relationships_path = os.path.join(DATA_DIR, "relationships.md")
        if os.path.exists(relationships_path):
            with open(relationships_path, "r", encoding="utf-8") as f:
                prompt += "\n\n## Relationship Graph\n" + f.read()

        return prompt

    def chat(self, user_message: str, interactor_name: Optional[str] = None) -> str:
        update_activity()

        memory_context = self.memory_manager.search_memory(user_message)

        system_prompt = self._build_system_prompt()

        if interactor_name:
            system_prompt += f"\n\n## Current Interactor\n你正在与 **{interactor_name}** 对话。根据 `relationships.md` 调整称呼和语气。"

        messages = [{"role": "system", "content": system_prompt}]

        for msg in self.conversation_history[-MAX_HISTORY:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": user_message})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.8,
            stream=False,
        )

        assistant_reply = response.choices[0].message.content

        self.conversation_history.append({"role": "user", "content": user_message})
        self.conversation_history.append({"role": "assistant", "content": assistant_reply})

        return assistant_reply

    def chat_stream(self, user_message: str, interactor_name: Optional[str] = None):
        update_activity()

        memory_context = self.memory_manager.search_memory(user_message)

        system_prompt = self._build_system_prompt()

        if interactor_name:
            system_prompt += f"\n\n## Current Interactor\n你正在与 **{interactor_name}** 对话。根据 `relationships.md` 调整称呼和语气。"

        messages = [{"role": "system", "content": system_prompt}]

        for msg in self.conversation_history[-MAX_HISTORY:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": user_message})

        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.8,
            stream=True,
        )

        full_reply = ""
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_reply += content
                yield content

        self.conversation_history.append({"role": "user", "content": user_message})
        self.conversation_history.append({"role": "assistant", "content": full_reply})

    def get_status(self) -> dict:
        birth_year = self.config.get("birth_year", 1990)
        current_year = datetime.now().year
        mode = get_current_mode()
        
        # Check for avatar
        avatar = self.config.get("avatar", "")
        if avatar:
            avatar_url = f"/avatars/{avatar}"
        else:
            avatar_url = ""
        
        return {
            "user_name": self.config.get("user_name", "Unknown"),
            "age": current_year - birth_year,
            "mode": mode,
            "mode_display": "Living Mode" if mode == "LIVING" else "Legacy Mode",
            "conversation_count": len(self.conversation_history) // 2,
            "avatar": avatar_url,
        }


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("错误: 请设置 OPENAI_API_KEY 环境变量")
        print("方法: cp .env.example .env 并填入你的 API Key")
        sys.exit(1)

    twin = DigitalTwin()
    status = twin.get_status()
    print(f"\n🌟 欢迎回来, {status['user_name']}!")
    print(f"   模式: {status['mode_display']} | 年龄: {status['age']}")
    print("   输入 /quit 退出, /status 查看状态\n")

    while True:
        try:
            user_input = input("你: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n再见!")
            break

        if not user_input:
            continue
        if user_input.lower() == "/quit":
            print("再见!")
            break
        if user_input.lower() == "/status":
            status = twin.get_status()
            print(f"   模式: {status['mode_display']} | 年龄: {status['age']} | 对话轮数: {status['conversation_count']}")
            continue

        reply = twin.chat(user_input)
        print(f"\n{twin.config.get('user_name', 'AI')}: {reply}\n")
