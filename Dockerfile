FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py config_manager.py fake.py network.py test_types.py ./
COPY static/* ./static/
COPY templates/* ./templates/

CMD [ "gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--log-level=info", "--workers=2"]