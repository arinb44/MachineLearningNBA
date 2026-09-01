FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scripts/ scripts/
COPY data/ data/
COPY models/ models/
COPY tests/ tests/

# Demo: train on the committed season data, then predict the sample games.
# Override with any script, e.g.:
#   docker run --rm nba-predictor python scripts/predict_games.py
CMD ["sh", "-c", "python scripts/train_model.py && python scripts/predict_games.py"]
