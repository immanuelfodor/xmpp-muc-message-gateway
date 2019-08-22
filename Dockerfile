FROM python:3-alpine

WORKDIR /usr/src/app
EXPOSE 5000
ENV LOG_LEVEL=debug

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY .pyenv gateway.py gateway_helper.py xmpp_client.py ./

CMD [ "sh", "-c", "gunicorn --workers=1 --bind=0.0.0.0:5000 --log-level=${LOG_LEVEL} --access-logfile=- gateway:app" ]
