import os
import sys
import json
import glob
from pathlib import Path
from typing import Optional
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from fastapi import FastAPI, Query, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel

from main import DigitalTwin
from utils.photo_analyzer import analyze_photo

app = FastAPI(title="Life Legacy - Digital Twin")
twin = DigitalTwin()

STATIC_DIR = BASE_DIR / "web" / "static"
DATA_DIR = BASE_DIR / "skills" / "data"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

AVATARS_DIR = DATA_DIR / "avatars"
if AVATARS_DIR.exists():
    app.mount("/avatars", StaticFiles(directory=str(AVATARS_DIR)), name="avatars")
else:
    AVATARS_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/avatars", StaticFiles(directory=str(AVATARS_DIR)), name="avatars")


# ============================================================
# Pages
# ============================================================
# Pydantic Models
# ============================================================

class Milestone(BaseModel):
    year: int
    event: str
    feeling: str = ""
    tags: list[str] = []


class TimelineUpdate(BaseModel):
    meta: dict
    milestones: list[Milestone]


class ChatRecord(BaseModel):
    filename: str
    messages: list[dict]


class PhotoDescription(BaseModel):
    filename: str
    description: str


# ============================================================
# Pages
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def index():
    with open(STATIC_DIR / "index.html", "r", encoding="utf-8") as f:
        return f.read()


# ============================================================
# Status
# ============================================================

@app.get("/api/status")
async def status():
    return twin.get_status()


# ============================================================
# Avatar API
# ============================================================

@app.post("/api/avatar")
async def upload_avatar(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    
    avatar_dir = DATA_DIR / "avatars"
    os.makedirs(avatar_dir, exist_ok=True)
    
    ext = os.path.splitext(file.filename)[1].lower() if file.filename else ".jpg"
    if ext not in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
        ext = ".jpg"
    
    filename = f"avatar{ext}"
    filepath = avatar_dir / filename
    
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)
    
    # Update config
    config_path = DATA_DIR / "config.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        config = {}
    
    config["avatar"] = filename
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    
    # Reload twin config
    twin.config = twin._load_config()
    
    return {"filename": filename, "url": f"/avatars/{filename}"}


# ============================================================
# Chat
# ============================================================

@app.get("/api/chat/stream")
async def chat_stream(message: str = Query(...), interactor: Optional[str] = Query(None)):
    return EventSourceResponse(twin.chat_stream(message, interactor))


# ============================================================
# Timeline API
# ============================================================

@app.get("/api/timeline")
async def get_timeline():
    path = DATA_DIR / "timeline.json"
    if not path.exists():
        return {"meta": {}, "milestones": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.post("/api/timeline")
async def update_timeline(data: TimelineUpdate):
    path = DATA_DIR / "timeline.json"
    payload = {
        "meta": data.meta,
        "milestones": [m.model_dump() for m in data.milestones],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4, ensure_ascii=False)
    twin.memory_manager.clear_cache()
    return {"status": "ok"}


# ============================================================
# Values API
# ============================================================

@app.get("/api/values")
async def get_values():
    path = DATA_DIR / "values.md"
    if not path.exists():
        return {"content": ""}
    with open(path, "r", encoding="utf-8") as f:
        return {"content": f.read()}


@app.post("/api/values")
async def update_values(content: dict):
    path = DATA_DIR / "values.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.get("content", ""))
    return {"status": "ok"}


# ============================================================
# Relationships API
# ============================================================

@app.get("/api/relationships")
async def get_relationships():
    path = DATA_DIR / "relationships.md"
    if not path.exists():
        return {"content": ""}
    with open(path, "r", encoding="utf-8") as f:
        return {"content": f.read()}


@app.post("/api/relationships")
async def update_relationships(content: dict):
    path = DATA_DIR / "relationships.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.get("content", ""))
    return {"status": "ok"}


# ============================================================
# Diaries API
# ============================================================

class DiaryEntry(BaseModel):
    title: str
    date: str
    body: str
    overwrite: bool = False


@app.get("/api/diaries")
async def get_diaries():
    diaries_dir = DATA_DIR / "diaries"
    if not diaries_dir.exists():
        return []
    result = []
    for filepath in sorted(glob.glob(str(diaries_dir / "*.json"))):
        fp = Path(filepath)
        with open(fp, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        title = data.get("title", fp.stem)
        date_str = data.get("date", fp.stem)
        body = data.get("body", "")
        
        result.append({
            "filename": fp.name,
            "title": title,
            "date": date_str,
            "body": body,
            "preview": body[:100] + ("..." if len(body) > 100 else ""),
            "sort_key": date_str if date_str else fp.stat().st_mtime,
            "size": len(body),
            "modified": datetime.fromtimestamp(fp.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
        })
    
    # Sort by date descending
    result.sort(key=lambda x: x["sort_key"], reverse=True)
    return result


@app.get("/api/diaries/{filename}")
async def get_diary(filename: str):
    path = DATA_DIR / "diaries" / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Diary not found")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.post("/api/diaries")
async def save_diary(entry: DiaryEntry):
    if not entry.title or not entry.date or not entry.body:
        raise HTTPException(status_code=400, detail="标题、日期和正文为必填项")
    
    diaries_dir = DATA_DIR / "diaries"
    os.makedirs(diaries_dir, exist_ok=True)
    
    filename = f"{entry.date}.json"
    filepath = diaries_dir / filename
    
    if filepath.exists() and not entry.overwrite:
        return {"exists": True, "filename": filename, "message": f"日期 {entry.date} 的日记已存在，是否覆盖？"}
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump({
            "title": entry.title,
            "date": entry.date,
            "body": entry.body,
        }, f, indent=4, ensure_ascii=False)
    
    return {"status": "ok", "filename": filename}


@app.delete("/api/diaries/{filename}")
async def delete_diary(filename: str):
    path = DATA_DIR / "diaries" / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Diary not found")
    path.unlink()
    return {"status": "ok"}


# ============================================================
# Chats API
# ============================================================

@app.get("/api/chats")
async def get_chats():
    chats_dir = DATA_DIR / "chats"
    if not chats_dir.exists():
        return []
    result = []
    for filepath in sorted(glob.glob(str(chats_dir / "*.json"))):
        fp = Path(filepath)
        with open(fp, "r", encoding="utf-8") as f:
            data = json.load(f)
        messages = data.get("messages", [])
        result.append({
            "filename": fp.name,
            "message_count": len(messages),
            "modified": datetime.fromtimestamp(fp.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
        })
    return result


@app.get("/api/chats/{filename}")
async def get_chat(filename: str):
    path = DATA_DIR / "chats" / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Chat record not found")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {"filename": filename, "messages": data.get("messages", [])}


@app.post("/api/chats")
async def save_chat(record: ChatRecord):
    path = DATA_DIR / "chats" / record.filename
    os.makedirs(path.parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"messages": record.messages}, f, indent=4, ensure_ascii=False)
    return {"status": "ok"}


@app.delete("/api/chats/{filename}")
async def delete_chat(filename: str):
    path = DATA_DIR / "chats" / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Chat record not found")
    path.unlink()
    return {"status": "ok"}


# ============================================================
# Photos API
# ============================================================

@app.get("/api/photos")
async def get_photos():
    photos_dir = DATA_DIR / "photos"
    if not photos_dir.exists():
        return []
    result = []
    for filepath in sorted(glob.glob(str(photos_dir / "*.txt")) + glob.glob(str(photos_dir / "*.md"))):
        fp = Path(filepath)
        with open(fp, "r", encoding="utf-8") as f:
            description = f.read().strip()
        result.append({
            "filename": fp.stem,
            "description": description,
            "modified": datetime.fromtimestamp(fp.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
        })
    return result


@app.get("/api/photos/{filename}")
async def get_photo(filename: str):
    base = filename.replace(".txt", "").replace(".md", "")
    path = DATA_DIR / "photos" / f"{base}.txt"
    if not path.exists():
        path = DATA_DIR / "photos" / f"{base}.md"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Photo description not found")
    with open(path, "r", encoding="utf-8") as f:
        return {"filename": path.name, "description": f.read().strip()}


@app.post("/api/photos")
async def save_photo_description_api(data: PhotoDescription):
    path = DATA_DIR / "photos" / f"{data.filename}.txt"
    os.makedirs(path.parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(data.description)
    twin.memory_manager.clear_cache()
    return {"status": "ok"}


@app.delete("/api/photos/{filename}")
async def delete_photo(filename: str):
    base = filename.replace(".txt", "").replace(".md", "")
    path = DATA_DIR / "photos" / f"{base}.txt"
    if not path.exists():
        path = DATA_DIR / "photos" / f"{base}.md"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Photo description not found")
    path.unlink()
    twin.memory_manager.clear_cache()
    return {"status": "ok"}


@app.post("/api/photos/analyze")
async def analyze_uploaded_photo(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        description = analyze_photo(tmp_path)
        os.unlink(tmp_path)

        photo_name = file.filename.rsplit(".", 1)[0] if file.filename else "unknown"
        photo_desc_path = DATA_DIR / "photos" / f"{photo_name}.txt"
        os.makedirs(photo_desc_path.parent, exist_ok=True)
        with open(photo_desc_path, "w", encoding="utf-8") as f:
            f.write(description)
        twin.memory_manager.clear_cache()

        return {"filename": photo_name, "description": description}
    except Exception as e:
        os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# AI Insights API
# ============================================================

@app.post("/api/insights/extract")
async def extract_insights():
    """使用 AI 从时间线中提取经验教训和关系"""
    from openai import OpenAI
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    timeline = await get_timeline()
    milestones = timeline.get("milestones", [])
    
    if not milestones:
        return {"lessons": [], "relationships": []}
    
    prompt = f"""请分析以下人生大事记，提取：
1. 经验教训（从事件中总结出的智慧）
2. 重要人物关系（出现的人物及其关系）

人生大事记：
{json.dumps(milestones, ensure_ascii=False, indent=2)}

请以 JSON 格式返回：
{{
    "lessons": [
        {{"year": 年份, "event": 原始事件, "lesson": 经验教训}}
    ],
    "relationships": [
        {{"name": 人物姓名, "role": 角色/关系, "since": 首次出现的年份}}
    ]
}}

只返回 JSON，不要其他内容。"""

    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        
        result_text = response.choices[0].message.content
        result_text = result_text.strip().strip("```json").strip("```").strip()
        return json.loads(result_text)
    except Exception as e:
        return {"error": str(e), "lessons": [], "relationships": []}
