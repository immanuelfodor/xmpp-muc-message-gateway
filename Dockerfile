FROM python:3-alpine

WORKDIR /usr/src/app
EXPOSE 5000

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY .pyenv gateway.py xmpp_client.py ./

ENV LOG_LEVEL=debug

CMD [ "sh", "-c", "gunicorn --workers=1 --bind=0.0.0.0:5000 --log-level=${LOG_LEVEL} --access-logfile=- gateway:app" ]
