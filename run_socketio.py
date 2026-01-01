from gevent import monkey
monkey.patch_all()

import os
import sys

project_home = '/home/dossdowncom/dossdownbackend/bookingappbackend'
sys.path.insert(0, project_home)

from dotenv import load_dotenv
load_dotenv(os.path.join(project_home, '.env'))

from app import create_app, socketio

app = create_app('production')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8000)