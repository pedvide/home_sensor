from flask import Flask
from flask import render_template
from flask import request
import arrow

# from pprint import pprint

app = Flask(__name__)

last_request = None
timezone = "local"


@app.route("/")
def index():
    template_data = parse_measurement_request(last_request)
    return render_template("index.html", **template_data)


@app.route("/api/upload_data", methods=["POST"])
def upload_data():
    global last_request
    content = request.get_json(silent=True)
    last_request = content
    return {"success": True}, 200


def parse_measurement_request(request_json):
    """Parse request and return dict with measurement data"""
    now = arrow.now(timezone)
    sensor_id = request_json.get("sensor_id")
    measurement_datetime = arrow.get(request_json.get("time")).to(timezone)
    measurement = {
        "sensor_id": sensor_id,
        "measurement_datetime": f"{measurement_datetime.format()} ({measurement_datetime.humanize(now)})",
        "server_time": now.format(),
    }

    request_data = request_json.get("data")
    for item in request_data:
        name = item.get("name")
        value = item.get("value")
        unit = item.get("unit")
        if name and value:
            if unit in ("C", "%"):
                fmt_value = f"{float(value):.2f}"
            else:
                fmt_value = str(value)
            measurement[name] = fmt_value

    return measurement


@app.route("/api/last_measurement")
def last_measurement():
    if not last_request:
        return "Not ready", 404
    return parse_measurement_request(last_request)


if __name__ == "__main__":
    app.run(debug=True, port=8080, host="0.0.0.0")

# redirect port 8080 to 80 (only available to root) with:
# sudo iptables -A PREROUTING -t nat -p tcp --dport 80 -j REDIRECT --to-ports 8080
# sudo iptables-save
