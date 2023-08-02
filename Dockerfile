FROM python:3.11.4

WORKDIR /app

COPY requirements.txt requirements.txt

RUN  pip install --upgrade pip && pip install -r requirements.txt --no-cache-dir

COPY ./src ./src

ENTRYPOINT ["python", "src/main.py"]
