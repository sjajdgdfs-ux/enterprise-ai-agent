#!/bin/bash

# 1. Build local knowledge base vectorstore inside container
python build_kb.py

# 2. Launch FastAPI backend on port 8000 in background
uvicorn server:app --host 0.0.0.0 --port 8000 &

# 3. Wait 3 seconds for FastAPI backend to initialize
sleep 3

# 4. Launch Streamlit frontend on port 7860
python -m streamlit run capstone_ui.py --server.port 7860 --server.address 0.0.0.0