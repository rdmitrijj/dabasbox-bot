FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY bot ./bot
RUN useradd --create-home app && mkdir -p /app/data && chown app /app/data
USER app
VOLUME ["/app/data"]
CMD ["python", "-m", "bot"]
