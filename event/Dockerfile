FROM python:3.12

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
COPY ./settings.yaml /code/settings.yaml

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./src /code/app

CMD ["python", "app/api.py"]
