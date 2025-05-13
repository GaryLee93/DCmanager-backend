from flask import Flask
from BluePrint import DataCenter, Room, Rack, Host, Service, Auth

app = Flask(__name__)
app.register_blueprint(DataCenter)
app.register_blueprint(Room)
app.register_blueprint(Rack)
app.register_blueprint(Host)
app.register_blueprint(Service)
app.register_blueprint(Auth)

@app.route("/")
def hello():
    return "Hello from Flask in Docker!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)