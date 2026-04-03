import os
import base64
from typing import Optional
from openai import OpenAI


def analyze_photo(
    image_path: str,
    api_key: Optional[str] = None,
    model: str = "gpt-4o",
    prompt: Optional[str] = None,
) -> str:
    """
    分析照片内容，返回描述性文本。

    使用 OpenAI Vision API (GPT-4o) 分析照片，结果可用于：
    - 自动添加到照片描述库
    - 作为记忆检索的上下文
    - 触发 Storyteller 技能讲述相关故事

    Args:
        image_path: 图片文件路径
        api_key: OpenAI API Key（默认从环境变量读取）
        model: 使用的模型（默认 gpt-4o）
        prompt: 自定义分析提示词（可选）

    Returns:
        图片描述文本
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"图片不存在: {image_path}")

    client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    with open(image_path, "rb") as f:
        base64_image = base64.b64encode(f.read()).decode("utf-8")

    ext = os.path.splitext(image_path)[1].lower().replace(".", "")
    mime_type = f"image/{ext}" if ext in ("jpeg", "jpg", "png", "webp", "gif") else "image/jpeg"

    default_prompt = (
        "请详细描述这张照片的内容，包括：\n"
        "1. 场景中的人物、地点、时间（如果能推断）\n"
        "2. 人物的情绪和互动\n"
        "3. 照片的整体氛围和故事感\n"
        "4. 任何值得记住的细节\n"
        "请用中文回答，控制在200字以内。"
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt or default_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_image}"
                        },
                    },
                ],
            }
        ],
        max_tokens=500,
    )

    return response.choices[0].message.content or ""


def save_photo_description(
    image_path: str,
    description: Optional[str] = None,
    photos_dir: str = "./skills/data/photos",
    api_key: Optional[str] = None,
) -> str:
    """
    分析照片并保存描述文本到文件。

    Args:
        image_path: 图片文件路径
        description: 手动提供的描述（如为 None 则自动分析）
        photos_dir: 描述文件保存目录
        api_key: OpenAI API Key

    Returns:
        描述文本
    """
    if description is None:
        description = analyze_photo(image_path, api_key=api_key)

    os.makedirs(photos_dir, exist_ok=True)
    filename = os.path.splitext(os.path.basename(image_path))[0] + ".txt"
    output_path = os.path.join(photos_dir, filename)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(description)

    return description
