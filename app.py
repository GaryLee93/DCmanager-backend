from flask import Flask
from BluePrint import DataCenter, Room, Rack, Host

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello from Flask in Docker!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)