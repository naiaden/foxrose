FROM python:3.12

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./src /code/app
COPY ./config.example.yaml /code/config.example.yaml

CMD ["python", "app/api.py"]

