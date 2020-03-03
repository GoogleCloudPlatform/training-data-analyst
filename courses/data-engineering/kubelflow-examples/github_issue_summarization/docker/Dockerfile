FROM python:3.6

COPY ./flask_web/requirements.txt /app/

WORKDIR /app

RUN pip install -r requirements.txt

COPY ./flask_web /app

ENTRYPOINT [ "python" ]

CMD [ "app.py" ]
