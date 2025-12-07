from flask import Flask, request
from tailor import generate

app = Flask(__name__)

@app.route("/tailor", methods = ['POST'])
def generate_resume():
    job_description = request.get_json()['job_description']
    print(job_description)
    status = generate(job_description)
    if status:
        return 'All done!'
    else:
        return 'Something went wrong!'
    
if __name__ == '__main__':
    app.run("localhost", 5000, True)