FROM google/cloud-sdk:latest
ADD ./src /pipelines/component/src
RUN chmod 755 /pipelines/component/src/deploy.sh
ENTRYPOINT ["/pipelines/component/src/deploy.sh"]