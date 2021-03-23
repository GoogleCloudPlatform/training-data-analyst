FROM tensorflow/tensorflow:2.0.0-py3
RUN pip install gcsfs pandas matplotlib seaborn
COPY ./visualize.py .
CMD ["python", 'visualize.py']