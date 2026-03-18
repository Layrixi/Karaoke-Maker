from flask import Flask, render_template

#debug only, delete later
from livereload import Server

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    # debug=false in prod later, change the port adequatly to the pc(if possible)
    #debug code
    server = Server(app.wsgi_app)
    server.watch('templates/**/*.html')
    server.watch('static/**/*.css')
    server.watch('static/**/*.js')
    server.serve(port=5000, debug=True)

    #prod code
    #app.run(debug=True, port=5000)