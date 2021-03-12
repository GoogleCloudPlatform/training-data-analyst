FROM python:3.7
ENV KAGGLE_USERNAME=[YOUR KAGGLE USERNAME] \
    KAGGLE_KEY=[YOUR KAGGLE KEY]
RUN pip install kaggle
RUN pip install google-cloud-storage
COPY ./download_data.py .
CMD ["python", "download_data.py"]