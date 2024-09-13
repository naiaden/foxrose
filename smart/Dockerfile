FROM python:3.12

WORKDIR /code

COPY ./install-coap-client.sh /install-coap-client.sh
COPY ./requirements.txt /code/requirements.txt
COPY ./settings.yaml /code/settings.yaml

RUN pip install --upgrade pip setuptools wheel cython && \
        pip install --no-cache-dir --upgrade -r /code/requirements.txt && \
        chmod +x /install-coap-client.sh && \
        /install-coap-client.sh

COPY ./src /code/app

CMD ["fastapi", "run", "app/api.py", "--port", "8000", "--host", "0.0.0.0"]
