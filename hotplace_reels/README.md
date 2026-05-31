# Seoul Hot Place Discovery Platform

AI-powered platform to discover emerging places in Seoul, analyze trends, and generate viral content.

## Features
- **Trend Collector**: Aggregates mentions from Naver Blog, News, and Search.
- **Place Discovery Engine**: Identifies hidden gems and fast-growing spots.
- **Viral Score Calculator**: Ranks places based on growth and engagement.
- **Content Generators**: Automatically creates Reels scripts and Threads posts.
- **Streamlit Dashboard**: Visualizes trends and content opportunities.

## Tech Stack
- Python 3.12
- Streamlit (Dashboard)
- SQLite (Database)
- Ollama (Local LLM: Gemma, Qwen)
- Naver Search APIs

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Configure `.env` with Naver API credentials.
3. Run the dashboard: `streamlit run dashboard/app.py`
