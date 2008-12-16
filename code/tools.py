from itertools import *
from net import *
from utils import *

import cgi
import datetime
import wsgiref.handlers

import re
import os.path

from google.appengine.api import users, urlfetch, memcache, mail
from google.appengine.ext import webapp, db
from google.appengine.api import users

import xmlrpclib

#~ import xml.etree.ElementTree as ET

# set up locations
ROOT = os.path.dirname(__file__)

ON_DEV_SERVER = os.environ.get("SERVER_SOFTWARE", "dev").lower().startswith("dev")

REPO_PATH = "http://svn.scipy.org/svn/scikits/trunk"

import time

# set up logging system
import logging
log_format = "%(levelname)s:%(module)s.%(name)s@%(asctime)s : %(message)s"
logging.basicConfig(
	level=logging.DEBUG,
	datefmt="%H:%M",
	format=log_format,
	)
logger = logging.getLogger("")

import rdfxml
class Sink(object):
	def __init__(self):
		self.result = []
	def triple(self, s, p, o):
		self.result.append((s, p, o))
def rdfToPython(s, base=None):
	sink = Sink()
	return rdfxml.parseRDF(s, base=None, sink=sink).result

class GoogleXMLRPCTransport(object):
	"""Handles an HTTP transaction to an XML-RPC server."""

	def __init__(self, use_datetime=0):
		self._use_datetime = use_datetime

	def request(self, host, handler, request_body, verbose=0):
		"""
		Send a complete request, and parse the response. See xmlrpclib.py.

		:Parameters:
			host : str
				target host

			handler : str
				RPC handler on server (i.e., path to handler)

			request_body : str
				XML-RPC request body

			verbose : bool/int
				debugging flag. Ignored by this implementation

		:rtype: dict
		:return: parsed response, as key/value pairs
		"""

		# issue XML-RPC request

		result = None
		url = 'http://%s%s' % (host, handler)
		try:
			response = urlfetch.fetch(url,
				payload=request_body,
				method=urlfetch.POST,
				headers={'Content-Type': 'text/xml'})
		except:
			msg = 'Failed to fetch %s' % url
			raise xmlrpclib.ProtocolError(host + handler, 500, msg, {})

		if response.status_code != 200:
			logging.error('%s returned status code %s' % (url, response.status_code))
			raise xmlrpclib.ProtocolError(host + handler,
				  response.status_code,
				  "",
				  response.headers)
		else:
			result = self.__parse_response(response.content)

		return result

	def __parse_response(self, response_body):
		p, u = xmlrpclib.getparser(use_datetime=self._use_datetime)
		p.feed(response_body)
		return u.close()
