from flask import Flask, request, jsonify
from flask_cors import CORS
from tailor import generate

app = Flask(__name__)
CORS(app)

@app.route("/tailor", methods = ['POST'])
def generate_resume():
    job_description = request.get_json()['job_description']
    print(job_description)
    status = generate(job_description)
    if status:
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "error"})
    
if __name__ == '__main__':
    app.run("localhost", 8000, True)