import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules import create_app, start_background_tasks
app, config = create_app()
start_background_tasks(app, config)

while True:
    time.sleep(60)