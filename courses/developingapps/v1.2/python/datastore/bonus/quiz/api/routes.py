# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import api

from flask import request, Blueprint

api_blueprint = Blueprint('api', __name__)

"""
API endpoint for quiz

- GET will return list of questions for quiz
- POST will do grading
"""
@api_blueprint.route('/quizzes/<quiz_name>', methods=['GET', 'POST'])
def quiz_methods(quiz_name):
    if request.method == 'GET':
        return api.get_questions(quiz_name)
    elif request.method == 'POST':
        answers = request.get_json()
        return api.get_grade(quiz_name, answers)
    else:
        return "The Quiz API only supports GET and POST requests"

"""
API endpoint for feedback
"""
@api_blueprint.route('/quizzes/feedback/<quiz_name>', methods=['POST'])
def feedback_method(quiz_name):
    feedback = request.get_json()
    return 