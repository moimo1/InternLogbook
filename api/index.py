import os
import sys
import time

os.environ['TZ'] = os.environ.get('APP_TZ', 'Asia/Manila')
if hasattr(time, 'tzset'):
    time.tzset()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app