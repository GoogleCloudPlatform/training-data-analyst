# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from flask import Flask, render_template, request
import calendar

app = Flask(__name__)


@app.route("/", methods=["GET"])
def home_page():
    return render_template("index.html")


@app.route("/convert", methods=["POST"])
def convert():
    number = request.form["number"]
    roman = calendar.number_to_roman(number)
    return render_template("convert.html", number=number, roman=roman)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
