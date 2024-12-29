FROM python:3.12.5

WORKDIR /app

RUN mkdir -p /var/lib/gamulpung

COPY . .

RUN pip install -r requirements.txt

EXPOSE 8000

# CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
CMD ["python", "-m", "server"]