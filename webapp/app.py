from flask import Flask
from flask import render_template
import datetime

app = Flask(__name__)

@app.route('/')
def index():
   now = datetime.datetime.now()
   timeString = now.strftime("%Y-%m-%d %H:%M")
   templateData = {
      'title' : 'HELLO!',
      'time': timeString
      }
   return render_template('index.html', **templateData)

if __name__ == '__main__':
    app.run(debug=True, port=8080, host='0.0.0.0')

# redirect port 8080 to 80 (only available to root) with:
# sudo iptables -A PREROUTING -t nat -p tcp --dport 80 -j REDIRECT --to-ports 8080
