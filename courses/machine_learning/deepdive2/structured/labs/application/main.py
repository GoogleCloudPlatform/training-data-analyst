import os

from flask import Flask
from flask import render_template
from flask import request
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials


credentials = GoogleCredentials.get_application_default()
api = discovery.build("ml", "v1", credentials=credentials)

app = Flask(__name__)


def get_prediction(features):
    project = "" # TODO:Input your project name
    model_name = "" # TODO: Input your model name
    version_name = "" # TODO: Input your model version name

    input_data = {"instances": [features]}
    # TODO: Write a formatted string to make a prediction against a CAIP deployed model.
    # HINT: Review documentation on API for model string format at:
    # https://cloud.google.com/ai-platform/prediction/docs/online-predict#requesting_predictions
    parent = "".format()
    prediction = api.projects().predict(body=input_data, name=parent).execute()

    return prediction["predictions"][0]["weight"][0]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    def gender2str(val):
        # TODO: complete genders mapping dictionary.
        genders = {"female": "False", }
        return genders[val]

    def plurality2str(val):
        # TODO: complete pluralities mapping dictionary.
        pluralities = {"1": "Single(1)", }
        if features["is_male"] == "Unknown" and int(val) > 1:
            return "Multiple(2+)"
        return pluralities[val]

    data = request.form.to_dict()
    mandatory_items = ["babyGender",
                       "motherAge",
                       "plurality",
                       "gestationWeeks"]
    for item in mandatory_items:
        if item not in data.keys():
            return "Set all items."

    features = {}
    features["is_male"] = gender2str(data["babyGender"])
    features["mother_age"] = float(data["motherAge"])
    features["plurality"] = plurality2str(data["plurality"])
    features["gestation_weeks"] = float(data["gestationWeeks"])

    prediction = get_prediction(features)

    return "{:.2f} lbs.".format(prediction)


if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=8080)
