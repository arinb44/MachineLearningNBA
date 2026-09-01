FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scripts/ scripts/
COPY data/ data/
COPY models/ models/
COPY tests/ tests/
COPY streamlit_app.py .

# Interactive demo:
#   docker run --rm -p 8501:8501 nba-predictor \
#     streamlit run streamlit_app.py --server.address 0.0.0.0
EXPOSE 8501

# Demo: train on the committed season data, then predict the sample games.
# Override with any script, e.g.:
#   docker run --rm nba-predictor python scripts/predict_games.py
CMD ["sh", "-c", "python scripts/train_model.py && python scripts/predict_games.py"]
