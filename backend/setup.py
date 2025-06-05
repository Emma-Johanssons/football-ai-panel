from setuptools import setup, find_packages

setup(
    name="football-ai-panel",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "gtts",
        "python-dotenv",
        "requests",
        "asyncio",
        "openai>=1.0.0",
        "langchain-community",
        "langchain-core",
        "langchain-openai",
        "langchain-chroma",
        "langchain-huggingface",
        "chromadb",
        "sentence-transformers",
        "ffmpeg-python",
    ],
    python_requires=">=3.8",
) 