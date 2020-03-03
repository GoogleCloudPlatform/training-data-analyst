#This container contains your model and any helper scripts specific to your model.
FROM tensorflow/tensorflow:1.7.0

ADD model.py /opt/model.py
RUN chmod +x /opt/model.py

ENTRYPOINT ["/usr/bin/python"]
CMD ["/opt/model.py"]
