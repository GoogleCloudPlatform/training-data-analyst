FROM node:12-slim
WORKDIR /srv/grpc
COPY server.js *.proto package.json ./
RUN npm install --only=production
CMD [ "node", "server.js" ]
