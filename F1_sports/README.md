# F1 AI Race Strategist

A production-quality AI-powered Formula 1 race intelligence platform built in Python.

## Features
- **Automatic Session Detection**: Monitors the F1 schedule and activates data pipelines during live sessions.
- **Telemetry Ingestion**: Gathers live telemetry and timing data using OpenF1/FastF1 APIs and stores it as efficient Parquet files.
- **AI Strategy Commentary**: Uses local LLMs (via Ollama) to generate race engineer-style commentary, summarizing situations and suggesting pit strategies.
- **Prediction Pipeline**: Uses XGBoost/LightGBM to predict tire degradation and driver performance.
- **Mobile-Friendly Dashboard**: A responsive Streamlit frontend for viewing live standings, AI commentary, and telemetry charts.

## Architecture
This project focuses on a lightweight, event-driven architecture suitable for local execution:
- **Scheduler**: `APScheduler` monitors upcoming sessions.
- **Storage**: Local filesystem using columnar `Parquet` format for fast IO and low memory footprint.
- **Inference**: Local ML models (scikit-learn/XGBoost) and Local LLMs (Ollama) to keep operational costs at zero.
- **Frontend**: `Streamlit` for a fast, responsive, and reactive web/mobile UI.

## Setup Instructions

1. **Install uv**
   If you don't have `uv` installed:
   ```bash
   pip install uv
   ```

2. **Sync Dependencies**
   `uv` will automatically create a virtual environment and install all dependencies from `pyproject.toml`.
   ```bash
   uv sync
   ```

3. **Environment Variables**
   Copy `.env.example` to `.env` and configure your settings.
   ```bash
   cp .env.example .env
   ```

4. **Install & Run Ollama**
   Ensure you have [Ollama](https://ollama.com/) installed and running locally.
   Pull the required model:
   ```bash
   ollama pull qwen2.5
   ```

5. **Run the Application**
   ```bash
   uv run streamlit run app/Home.py
   ```

## Directory Structure
- `app/`: Streamlit dashboard code.
- `data/`: Local storage for raw/processed data and trained models.
- `src/`: Core Python modules (scheduler, ingestion, ml, llm).
