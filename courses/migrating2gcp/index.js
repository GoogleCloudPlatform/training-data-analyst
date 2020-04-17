// content of index.js
const http = require('http')
const port = 8080

const requestHandler = (request, response) => {
  console.log(request.url)
  response.end('Hello from your Cloud Shell!')
}

const server = http.createServer(requestHandler)

server.listen(port, (err) => {
  if (err) {
    return console.log('something bad happened', err)
  }

  console.log(`server is listening on ${port}`)
})
