FROM python:3

WORKDIR /app

COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt
RUN pip install --no-deps topggpy

COPY . ./

CMD ["python", "-u","main.py"]
