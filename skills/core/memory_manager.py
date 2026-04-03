import os
import json
from typing import List, Dict

class MemoryManager:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.timeline_path = os.path.join(data_dir, "timeline.json")
        # 在实际工程中，这里应初始化向量数据库客户端 (如 Chroma, FAISS)
        
    def load_timeline(self) -> List[Dict]:
        """加载人生大事记"""
        if not os.path.exists(self.timeline_path):
            return []
        with open(self.timeline_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def search_memory(self, query: str, top_k: int = 3) -> str:
        """
        检索相关记忆
        这里是一个模拟实现，实际应使用 RAG 技术
        """
        # 简单的关键词匹配示例
        timeline = self.load_timeline()
        results = []
        for event in timeline:
            if query in event.get('event', '') or query in event.get('feeling', ''):
                results.append(f"- [{event['year']}] {event['event']} (Feeling: {event['feeling']})")
        
        return "\n".join(results[:top_k]) if results else "未找到具体记忆，请尝试询问其他话题。"

# 使用示例
# manager = MemoryManager("./skills/data")
# print(manager.search_memory("创业"))