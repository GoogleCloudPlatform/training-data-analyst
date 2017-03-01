FROM gcr.io/cloud-datalab/datalab:mlhack

ADD startup.sh /datalab/
RUN chmod a+x /datalab/startup.sh

ENTRYPOINT [ "/bin/bash", "-c", "/datalab/startup.sh && /datalab/run.sh" ]
