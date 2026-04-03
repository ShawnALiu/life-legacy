import os
import json
import glob
from typing import List, Dict, Optional
from datetime import datetime


class MemoryManager:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.timeline_path = os.path.join(data_dir, "timeline.json")
        self.relationships_path = os.path.join(data_dir, "relationships.md")
        self.values_path = os.path.join(data_dir, "values.md")
        self.diaries_dir = os.path.join(data_dir, "diaries")
        self.chats_dir = os.path.join(data_dir, "chats")
        self.photos_dir = os.path.join(data_dir, "photos")
        self._memory_cache: Optional[List[Dict]] = None

    def _load_json_file(self, path: str) -> Optional[Dict]:
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_text_file(self, path: str) -> str:
        if not os.path.exists(path):
            return ""
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()

    def load_timeline(self) -> Dict:
        data = self._load_json_file(self.timeline_path)
        return data if data else {"meta": {}, "milestones": []}

    def load_relationships(self) -> str:
        return self._load_text_file(self.relationships_path)

    def load_values(self) -> str:
        return self._load_text_file(self.values_path)

    def load_diaries(self) -> List[Dict]:
        if not os.path.exists(self.diaries_dir):
            return []
        diaries = []
        for filepath in sorted(glob.glob(os.path.join(self.diaries_dir, "*.md")) +
                               glob.glob(os.path.join(self.diaries_dir, "*.txt"))):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            filename = os.path.basename(filepath)
            date_str = filename.replace(".md", "").replace(".txt", "")
            diaries.append({"date": date_str, "content": content, "source": filepath})
        return diaries

    def load_chats(self) -> List[Dict]:
        if not os.path.exists(self.chats_dir):
            return []
        chats = []
        for filepath in sorted(glob.glob(os.path.join(self.chats_dir, "*.json"))):
            data = self._load_json_file(filepath)
            if data and "messages" in data:
                chats.extend(data["messages"])
            elif data:
                chats.append({"content": json.dumps(data, ensure_ascii=False), "source": filepath})
        return chats

    def load_photo_descriptions(self) -> List[Dict]:
        if not os.path.exists(self.photos_dir):
            return []
        photos = []
        for filepath in sorted(glob.glob(os.path.join(self.photos_dir, "*.txt")) +
                               glob.glob(os.path.join(self.photos_dir, "*.md"))):
            with open(filepath, "r", encoding="utf-8") as f:
                description = f.read().strip()
            filename = os.path.basename(filepath).replace(".txt", "").replace(".md", "")
            photos.append({"filename": filename, "description": description})
        return photos

    def get_all_memories(self) -> List[Dict]:
        if self._memory_cache is not None:
            return self._memory_cache

        memories = []
        timeline = self.load_timeline()
        for milestone in timeline.get("milestones", []):
            memories.append({
                "type": "milestone",
                "year": milestone.get("year", ""),
                "content": milestone.get("event", ""),
                "feeling": milestone.get("feeling", ""),
                "tags": milestone.get("tags", []),
                "text": f"{milestone.get('year', '')} {milestone.get('event', '')} {milestone.get('feeling', '')}",
            })

        for diary in self.load_diaries():
            memories.append({
                "type": "diary",
                "date": diary.get("date", ""),
                "content": diary.get("content", ""),
                "text": f"{diary.get('date', '')} {diary.get('content', '')}",
            })

        for chat in self.load_chats():
            memories.append({
                "type": "chat",
                "content": chat.get("content", ""),
                "text": chat.get("content", ""),
            })

        for photo in self.load_photo_descriptions():
            memories.append({
                "type": "photo",
                "filename": photo.get("filename", ""),
                "description": photo.get("description", ""),
                "text": f"{photo.get('filename', '')} {photo.get('description', '')}",
            })

        self._memory_cache = memories
        return memories

    def search_memory(self, query: str, top_k: int = 5) -> str:
        memories = self.get_all_memories()
        if not memories:
            return "暂无记忆记录。"

        query_lower = query.lower()
        query_words = [w for w in query_lower.split() if len(w) > 1]

        scored = []
        for memory in memories:
            text = memory.get("text", "").lower()
            score = 0
            for word in query_words:
                if word in text:
                    score += text.count(word)
            if score > 0:
                scored.append((score, memory))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = scored[:top_k]

        if not results:
            return "未找到相关记忆，请尝试其他话题。"

        formatted = []
        for score, memory in results:
            mtype = memory.get("type", "")
            if mtype == "milestone":
                formatted.append(
                    f"[{memory['year']}] {memory['content']} (感受: {memory['feeling']})"
                )
            elif mtype == "diary":
                formatted.append(
                    f"[日记 {memory['date']}] {memory['content'][:200]}"
                )
            elif mtype == "chat":
                formatted.append(
                    f"[聊天记录] {memory['content'][:200]}"
                )
            elif mtype == "photo":
                formatted.append(
                    f"[照片 {memory['filename']}] {memory['description']}"
                )

        return "\n\n".join(formatted)

    def add_milestone(self, year: int, event: str, feeling: str = "", tags: Optional[List[str]] = None):
        timeline = self.load_timeline()
        timeline["milestones"].append({
            "year": year,
            "event": event,
            "feeling": feeling,
            "tags": tags or [],
        })
        with open(self.timeline_path, "w", encoding="utf-8") as f:
            json.dump(timeline, f, indent=4, ensure_ascii=False)
        self._memory_cache = None

    def clear_cache(self):
        self._memory_cache = None
