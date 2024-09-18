FROM python:3.12

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./src /code/app
COPY ./settings.yaml /code/settings.yaml
COPY ./.secrets.yaml /code/.secrets.yaml

CMD ["python", "app/api.py"]
