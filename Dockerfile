FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y build-essential libmupdf-dev libgl1-mesa-glx git && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production
ENV PORT=8080
EXPOSE 8080
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:8080", "app.main:app"]
