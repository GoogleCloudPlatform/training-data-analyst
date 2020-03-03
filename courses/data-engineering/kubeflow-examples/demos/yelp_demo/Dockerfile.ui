FROM python:3.6

COPY ui/requirements.txt /app/requirements.txt

RUN pip install -r /app/requirements.txt

WORKDIR /app

ENTRYPOINT ["python", "app.py"]

COPY yelp/yelp_sentiment /app/yelp_sentiment/

COPY ui /app/
