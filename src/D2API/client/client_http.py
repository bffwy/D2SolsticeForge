import os
from flask import Flask
from flask import request

app = Flask(__name__)


@app.route("/get_code")
def get_code():
    code = request.args.get("code")
    print(code)
    return "Hello, World!"


if __name__ == "__main__":
    app.run(port=9090)
