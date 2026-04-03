import os
from typing import Optional
from openai import OpenAI


def clone_voice(
    text: str,
    output_path: str,
    api_key: Optional[str] = None,
    voice: str = "alloy",
    model: str = "tts-1",
) -> str:
    """
    将文本转换为语音输出。

    使用 OpenAI TTS API 生成语音。如需克隆用户真实声音，
    需要先将用户的声音样本上传到 OpenAI 进行 Voice Cloning，
    然后使用返回的 voice_id。

    Args:
        text: 要转换为语音的文本
        output_path: 输出音频文件路径（.mp3）
        api_key: OpenAI API Key（默认从环境变量读取）
        voice: 声音类型（alloy/echo/fable/onyx/nova/shimmer）
        model: TTS 模型（tts-1 或 tts-1-hd）

    Returns:
        输出文件路径
    """
    client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    response = client.audio.speech.create(
        model=model,
        voice=voice,
        input=text,
    )

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    response.stream_to_file(output_path)

    return output_path


def clone_voice_stream(
    text: str,
    api_key: Optional[str] = None,
    voice: str = "alloy",
    model: str = "tts-1",
) -> bytes:
    """
    将文本转换为语音并返回字节流（用于 Web 直接传输）。

    Args:
        text: 要转换为语音的文本
        api_key: OpenAI API Key
        voice: 声音类型
        model: TTS 模型

    Returns:
        音频字节流
    """
    client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    response = client.audio.speech.create(
        model=model,
        voice=voice,
        input=text,
    )

    return response.content
