import os
import sys
import time
import sqlite3
import threading
from Queue import Queue
from datetime import datetime

import lxml
from lxml import etree
import requests
import audioread


DOWNLOAD_Q = Queue()
PARSE_Q = Queue()
EXIT = threading.Event()

DB = sqlite3.connect('radiot.db')

def download_episode_worker():
	while not DOWNLOAD_Q.empty():
		task = DOWNLOAD_Q.get()
		url = task['url']
		print 'Download: %s' % url
		r = requests.get(url, stream=True)
		with open('podcasts/%s' % url.split('/')[-1], 'w+') as f:
			for chunk in r.iter_content(chunk_size=4096):
				if chunk:
					f.write(chunk)
					f.flush()
		task['file'] = 'podcasts/%s' % url.split('/')[-1]
		print 'Complete downloading: %s' % url
		PARSE_Q.put(task)
	print "Set exit event"
	EXIT.set()


def parse_mp3():
	while not (EXIT.is_set() and PARSE_Q.empty()):
		if PARSE_Q.empty():
			time.sleep(3)
			continue
		task = PARSE_Q.get()
		print 'Parse %s' % task['file']
		with audioread.audio_open(task['file']) as mp3:
			task['duration'] = int(mp3.duration)
		save_result(task)


def save_result(task):
	print 'Save result %s' % task['file']
	cursor = DB.cursor()
	cursor.execute('INSERT INTO podcasts VALUES (?, ?, ?, ?, ?, ?)',
		(task['title'],
		 task['link'],
		 task['pubDate'],
		 task['duration'],
		 task['summary'],
		 os.path.getsize(task['file'])
		)
	)
	DB.commit()
	cursor.close()


def parse_feed(feed):
	with open(feed, 'r') as f:
		tree = etree.XML(f.read())
	items = tree.xpath('//item')
	for item in items:
		podcast = {}
		for opt in ('title', 'link', 'pubDate',
			'{http://www.itunes.com/dtds/podcast-1.0.dtd}summary',
			'enclosure'):
			tag = item.find(opt)
			if opt.startswith('{'):
				name = opt.split('}')[1]
				value = tag.text
			elif opt == 'enclosure':
				name = 'url'
				value = tag.attrib['url']
			else:
				name = opt
				value = tag.text
			podcast[name] = value
		DOWNLOAD_Q.put(podcast)
	


def main():
	feed = requests.get(sys.argv[1]).text
	with open('podcast_feed.xml', 'w+') as f:
		f.write(feed.encode('utf8'))
		f.flush()
	parse_feed('podcast_feed.xml')
	if not os.path.isdir('podcasts'):
		os.mkdir('podcasts')
	for i in range(5):
		t = threading.Thread(target=download_episode_worker)
		t.start()
	parse_mp3()
	

if __name__ == '__main__':
	main()