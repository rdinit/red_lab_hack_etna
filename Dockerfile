FROM python:3.9-slim

COPY . .

RUN pip3 install poetry
RUN poetry install

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["poetry", "run", "streamlit", "run", "etna_anomaly_detector/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
