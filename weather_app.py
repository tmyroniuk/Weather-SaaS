import datetime as dt
import json

import requests
from flask import Flask, jsonify, request

API_TOKEN = ""
API_KEY = ""

app = Flask(__name__)


def get_weather(api: str, location: str, date: str):
    base_url = "http://api.weatherapi.com"
    version = "v1"

    url = f"{base_url}/{version}/{api}"

    params = {
        "key": API_KEY,
        "q" : location,
        "date" : date,
        "aqi" : "no"
    }
    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload, params=params)
    return json.loads(response.text)


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route("/")
def home_page():
    return "<p><h2>Weather SaaS</h2></p>"


@app.route(
    "/content/api/v1",
    methods=["POST"],
)
def weather_endpoint():
    json_data = request.get_json()

    if json_data.get("token") is None:
        raise InvalidUsage("token is required", status_code=400)

    token = json_data.get("token")

    if token != API_TOKEN:
        raise InvalidUsage("wrong API token", status_code=403)

    location = ""
    date = ""
    api = ""

    if json_data.get("location"):
        location = json_data.get("location")

    if json_data.get("date"):
        date = json_data.get("date")
        api = "history.json"
    else:
        api = "current.json"


    weather = get_weather(api, location, date)

    request_dt = dt.datetime.now()
    location = weather["location"]["country"] + ", " + weather["location"]["name"]

    result = {
        "request_timestamp": request_dt.isoformat(),
        "location": location,
    }

    if api == "history.json":
        result["weather"] = weather["forecast"]["forecastday"][0]["day"]
        result["date"] = date

    if api == "current.json":
        result["weather"] = weather["current"]
        result["datetime"] = weather["current"]["last_updated"]

    result["weather"]["condition"] = None

    return result