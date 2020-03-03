import logging
import os
from flask import Flask, request, abort, jsonify, make_response, redirect


class CodeSearchServer:
  """Flask server wrapping the Search Engine.

  This utility class simply wraps the search engine
  into an HTTP server based on Flask. The root path
  is redirected to `index.html` as Flask does not
  do that automatically.

  Args:
    engine: An instance of CodeSearchEngine.
    ui_dir: Path to directory containing index.html and
            other static assets for the web application.
    host: A string host in IPv4 format.
    port: An integer for port binding.
  """
  def __init__(self, engine, ui_dir, host='0.0.0.0', port=8008):
    self.app = Flask(__name__, static_folder=ui_dir, static_url_path='')
    self.host = host
    self.port = port
    self.engine = engine

    self.init_routes()

  def init_routes(self):
    # pylint: disable=unused-variable

    @self.app.route('/')
    def index():
      redirect_path = os.environ.get('PUBLIC_URL', '') + '/index.html'
      return redirect(redirect_path, code=302)

    @self.app.route('/ping')
    def ping():
      return make_response(jsonify(status=200), 200)

    @self.app.route('/query')
    def query():
      query_str = request.args.get('q')
      logging.info("Got query: %s", query_str)
      if not query_str:
        abort(make_response(
          jsonify(status=400, error="empty query"), 400))

      num_results = int(request.args.get('n', 2))
      result = self.engine.query(query_str, k=num_results)
      return make_response(jsonify(result=result))

  def run(self):
    self.app.run(host=self.host, port=self.port)
