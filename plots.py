import time
from datetime import datetime
import sqlite3

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from scipy.interpolate import spline
import numpy as np


dates = []
durations = []

db = sqlite3.connect('radiot.db')

res = db.execute('SELECT date,duration FROM podcasts;')

for r in res.fetchall():
    dur = int(r[1]) / 60
    if dur == 0 or dur < 30:
        continue
    #dates.append(int(time.mktime(datetime.strptime(r[0][:-6], '%a, %d %b %Y %X').timetuple())))
    dates.append(datetime.strptime(r[0][:-6], '%a, %d %b %Y %X'))
    durations.append(dur)


plt.plot_date(dates, durations)
plt.show()