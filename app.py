from flask import Flask
from flask_cors import CORS
from BluePrint.DataCenter import DATA_CENTER_BLUEPRINT
from BluePrint.Room import ROOM_BLUEPRINT
from BluePrint.Rack import RACK_BLUEPRINT
from BluePrint.Host import HOST_BLUEPRINT
from BluePrint.Service import SERVICE_BLUEPRINT
from BluePrint.Auth import AUTH_BLUEPRINT

app = Flask(__name__)
app.register_blueprint(DATA_CENTER_BLUEPRINT, url_prefix="/dc")
app.register_blueprint(ROOM_BLUEPRINT, url_prefix="/room")
app.register_blueprint(RACK_BLUEPRINT, url_prefix="/rack")
app.register_blueprint(HOST_BLUEPRINT, url_prefix="/host")
app.register_blueprint(SERVICE_BLUEPRINT, url_prefix="/service")
app.register_blueprint(AUTH_BLUEPRINT, url_prefix="/auth")

@app.route("/")
def hello():
    return "Hello from Flask in Docker!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)