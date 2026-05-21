FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Add _shared to Python path for LLM gateway
ENV PYTHONPATH="/app/../_shared:${PYTHONPATH}"

RUN useradd --create-home appuser
USER appuser

CMD ["python", "-m", "bot.bot"]
