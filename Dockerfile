FROM python:3.9.10-bullseye

RUN apt-get update && apt-get install -y\
    iproute2 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /usr/src/app

COPY appliance_status_py/requirements/main.txt ./
RUN pip install --no-cache-dir -r main.txt

COPY appliance_status_py/appliance_status ./appliance_status
COPY app_config.json .

CMD [ "gunicorn", "appliance_status.app:app", "--bind", "0.0.0.0:5000", "--log-level=info", "--workers=2"]
