"""Demo CLI Agent - Entry point."""

import asyncio
import os
import sys

from dotenv import load_dotenv
from openai import AsyncOpenAI

from agents import set_default_openai_client, set_tracing_disabled, set_default_openai_api

from cli import App


def setup_deepseek_client() -> None:
    """Configure DeepSeek as the LLM provider."""
    load_dotenv()

    api_key = os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

    if not api_key:
        print("错误: 未设置 DEEPSEEK_API_KEY 环境变量")
        print("请在 .env 文件中添加: DEEPSEEK_API_KEY=your_api_key")
        sys.exit(1)

    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    set_default_openai_client(client)
    set_default_openai_api("chat_completions")
    enable_tracing = os.getenv("ENABLE_TRACING", "").lower() in ("1", "true", "yes")
    set_tracing_disabled(not enable_tracing)


def main() -> None:
    """Entry point."""
    setup_deepseek_client()
    app = App()
    asyncio.run(app.run())


if __name__ == "__main__":
    main()
