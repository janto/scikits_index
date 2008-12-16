#!/usr/bin/env python

from __future__ import division

from tools import *

import templates

"""

logger-level rule-of-thumbs
	everything goes into debug by default, higher levels are interesting to human
	debug
		normal operation
	info
		something is unique to this request e.g. forcing bypass of cache
	warn
		e.g. connection to a remote server lost
	error
		unrecoverable
		additional try-catch info

"""

def get_url(url, force_fetch=False):
	result = memcache.get(url)
	if result is None or force_fetch:
		logger.debug("fetching %s" % url)
		result = urlfetch.fetch(url)
		assert memcache.set(key=url, value=result, time=60*60*5), url
	else:
		logger.debug("cache hit for %s" % url)
	return result

class Page(webapp.RequestHandler):

	name = ""

	def __init__(self):
		self.init_time = time.time()
		webapp.RequestHandler.__init__(self)
		self.logger = logging.getLogger(self.name)

		# load from templates.py
		for t in [
			"header_template",
			"footer_template",
			"main_page_template",
			"about_template",
			"package_info_template",
		]:
			template_name = t.rsplit("_", 1)[0]
			text = getattr(templates, t)

			template = PageTemplate.all().filter("name =", template_name).get()
			if template:
				pass
			else:
				self.logger.info("loading %s from templates.py into datastore" % template_name)
				template = PageTemplate(name=template_name, text=text, modified=datetime.datetime.now())
				template.put()

	def write(self, text):
		self.response.out.write(text)

	def print_header(self):
		title = self.name
		search_box_html = SearchPage.search_box()
		self.write(get_template("header") % locals())

	def print_footer(self):
		# http://code.google.com/apis/analytics/docs/gaTrackingOverview.html
		google_analytics = """
			<script type="text/javascript">
			var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");
			document.write(unescape("%3Cscript src='" + gaJsHost + "google-analytics.com/ga.js' type='text/javascript'%3E%3C/script%3E"));
			</script>
			<script type="text/javascript">
			try {
			var pageTracker = _gat._getTracker("UA-6588556-1");
			pageTracker._trackPageview();
			} catch(err) {}</script>
		"""
		#~ if os.environ.get("REMOTE_ADDR") == "127.0.0.1":
			#~ google_analytics = "<!-- google analytics skipped when accessed from local -->"
		if ON_DEV_SERVER:
			google_analytics = "<!-- google analytics skipped when not run at google -->"
		load_time = time.time() - self.init_time
		self.write(get_template("footer") % locals())

	def print_menu(self):
		pass

class MainPage(Page):

	name = "main"

	def get(self):
		self.print_header()
		self.print_menu()
		self.write(get_template("main_page")% locals())
		self.print_footer()

class PackagesPage(Page):

	name = "scikits"

	def get(self):
		self.print_header()
		self.print_menu()

		packages = sorted(System.packages().values())

		# force fetch of some package
		if packages:
			key = "next_package_fetch_index"
			n = memcache.get(key)
			if n is None:
				n = 0
			memcache.set(key, (n+1) % len(packages))
			n %= len(packages) # in case a kit is removed from repo
			package = packages[n]
			self.logger.info("forcing fetch of package: %s" % package.name)
			package.info(force_fetch=True)
			self.write("<!-- forced fetch of package: %s -->\n" % package.name)

		self.write("<h1>SciKits Index</h1>")

		self.write("<p>")
		self.write(table_of_packages(packages))
		self.write("</p>")

		self.print_footer()

class PackageInfoPage(Page):
	name = "package info"

	def get(self, *args):
		"""
		@name
		"""

		package_name = self.request.get("name")
		if args:
			package_name = args[0]

		# done before printing header to build title
		package = System.packages().get(package_name)
		if package is None:
			package_name = "scikits.%s" % package_name
			package = System.packages().get(package_name)
		if package is None:
			self.error(404)
			self.write("404 not found")
			return
		self.name = package.name

		self.print_header()
		self.print_menu()

		self.write(package.to_html())

		self.print_footer()

def make_link(url):
	return '<a href="%s">%s</a>' % (url, url)

def table_of_packages(packages):
	result = ["<table>"]
	odd = False
	for p in packages:
		odd = not odd
		if odd:
			result.append('<tr style="background-color: #f8f8f8">')
		else:
			result.append('<tr>')
		d = p.info()
		r = """
		<td><a href="/%(name)s">%(short_name)s</a></td>
		<td>%(shortdesc)s</td>
		</tr>
		""" % dictadd(p.__dict__, d, locals())
		result.append(r)
	result.append("</table>")
	return "\n".join(result)

class Package(object):
	def __init__(self, repo_url):
		"""
		init should cache minimal information. actual information extraction should be done on page requests. with memcaching where needed.
		"""
		self.repo_url = repo_url

		self.name = "scikits.%s" % os.path.split(self.repo_url)[1]

		self.readme_filename = os.path.join(self.repo_url, "README")

		url = os.path.join(self.repo_url, "setup.py")
		result = get_url(url)
		if result.status_code != 200:
			self.valid = False
			return

		self.valid = True

	def __cmp__(self, other):
		return cmp(self.name, other.name)

	def info(self, force_fetch=False):
		d = dict(
			name=self.name,
			shortdesc="",
			description="",
			homepage="",
			revision="",
			people="",
			)
		doap_result = get_url("http://pypi.python.org/pypi?:action=doap&name=%s" % self.name, force_fetch=force_fetch)
		if doap_result.status_code == 200:

			doap_text = doap_result.content
			#~ http://wiki.python.org/moin/PyPIXmlRpc?highlight=(CategoryDocumentation)
			try:
				tuples = rdfToPython(doap_text)
			except:
				logger.error(doap_text)
				raise
			d["people"] = []
			for subject, predicate, ob in tuples:

				if predicate == "<http://xmlns.com/foaf/0.1/name>":
					d["people"].append(ob[1:-1])
					continue

				#~ logger.warn((subject, predicate, ob))
				name = re.findall(r"doap#(.+)>", predicate)
				if not name:
					continue
				name = name[0]
				value = ob

				if name == "homepage":
					value = value[1:-1] # strip angle brackets
				else:
					if not (value.startswith('"') and value.endswith('"')):
						continue
					value = value[1:-1] # strip quotes

				d[name] = value

			d["people"] = ", ".join(d["people"])

			download_page = d.get("download-page", "") or ("http://pypi.python.org/pypi/%(name)s" % d)
			d["download_link"] = make_link(download_page)

		else:

			d["download_link"] = "<code>svn checkout %s</code>" % make_link(self.repo_url)

		d["short_name"] = d["name"].split(".")[-1]

		return d

	def to_html(self):
		d = self.info()

		#~ from docutils.core import publish_parts
		#~ parts = publish_parts(
			#~ source=d["description"],
			#~ settings_overrides={'file_insertion_enabled': 0, 'raw_enabled': 0},
			#~ writer_name='html')
		#~ logger.debug(parts)
		#~ escaped_description = parts["fragment"]

		#~ if "WARNING" in escaped_description:
		escaped_description = htmlquote(d["description"]).replace(r"\n", "<br />\n")

		revision = d.get("revision")
		revision = ("version " + revision) if revision else ""

		return get_template("package_info") % dictadd(self.__dict__, d, locals())

def fetch_dir_links(url):
	result = get_url(url)
	if result.status_code != 200:
		return

	items = re.findall('<a href="(.+?)/">.+?</a>', result.content)
	return [os.path.join(url, item) for item in items if not item.startswith("http://") and not item.startswith("..")]

class System:

	@classmethod
	def init(self):
		pass

	@classmethod
	def packages(self):
		packages = memcache.get("packages")
		if packages is None:
			packages = {}
			for url in fetch_dir_links(REPO_PATH):
				logger.debug(url)
				package = Package(repo_url=url)
				if package.valid: # setup.py was not found
					packages[package.name] = package
		return packages

#~ class RecentChangesPage(Page):
	#~ def get(self):
		#~ rss = RSS2.RSS2(
			#~ title = "",
			#~ link = "",
			#~ description = "",

			#~ lastBuildDate = datetime.datetime.now(),

			#~ items = [

				#~ RSS2.RSSItem(
					#~ title = "PyRSS2Gen-0.0 released",
					#~ link = "http://www.dalkescientific.com/news/030906-PyRSS2Gen.html",
					#~ description = "Dalke Scientific today announced PyRSS2Gen-0.0, a library for generating RSS feeds for Python.  ",
					#~ guid = RSS2.Guid("http://www.dalkescientific.com/news/"
					#~ "030906-PyRSS2Gen.html"),
					#~ pubDate = datetime.datetime(2003, 9, 6, 21, 31)
					#~ ),

			#~ ])

		#~ rss.write_xml(self)

class SearchPage(Page):
	name="search"

	@classmethod
	def search_box(self, default="", prepend=""):
		default = htmlquote(default)
		return """
			<form action="/search" method="get">
			%(prepend)s
			<input type="text" name="text" value="%(default)s"/>
			<input type="submit" value="Go" />
			</form>
		""" % locals()

	def get(self):
		"""
		@text
		"""
		self.print_header()
		self.print_menu()
		text = self.request.get("text").strip()

		self.write("<p>")
		self.write(self.search_box(default=text))
		self.write("</p>")

		packages = []
		for package in System.packages().values():
			d = package.info()
			if any(text in field for field in package.info().values()):
				packages.append(package)
				continue

		self.write("<p>search results for <strong>%s</strong>:<br />" % (htmlquote(text) or "all"))
		if packages:
			self.write(table_of_packages(packages))
		else:
			self.write("<strong>no matches</strong>")
		self.write("</p>")

		self.print_footer()

def get_template(name):
	#~ return getattr(templates, name+"_template")
	template = PageTemplate.all().filter("name =", name).get()
	return template.text

class PageTemplate(db.Model):
	name = db.StringProperty(required=True)
	text = db.TextProperty()
	modified = db.DateTimeProperty(auto_now=False)
	username = db.TextProperty()

def collect_templates():
	result = []
	query = PageTemplate.all()
	for template in query.order("name"):
		template_name = template.name
		template_text = htmlquote(template.text).strip()
		result.append('''
%(template_name)s_template = """
%(template_text)s
"""
	'''.strip() % locals())
	return "\n".join(result)

class AdminPage(Page):
	name="admin"
	def get(self):
		"""
		@template_name
		@template_text

		@email_backup
		"""
		self.print_header()
		self.print_menu()

		user = users.get_current_user()
		self.write("<p>")
		if not user:
			self.write('only site admins allowed here.')
			self.write('<a href="%s">sign in</a>' % users.create_login_url("/admin"))
			self.print_footer()
			return
		if not users.is_current_user_admin():
			self.write('only site admin allowed here.')
			self.write('<a href="%s">sign out</a>.' % users.create_logout_url("/admin"))
			self.print_footer()
			return
		self.write("welcome %s. " % user.nickname())
		self.write('<a href="%s">sign out</a>.' % users.create_logout_url("/admin"))
		self.write("</p>")

		self.write("<p>")
		if self.request.get("email_backup") == "yes":
			t = datetime.datetime.now()
			address = users.get_current_user().email()
			if address:
				mail.send_mail(sender="jantod@gmail.com",
					to=address,
					subject="backup %s" % t,
					body="""Here's the backup""",
					attachments=[("templates.py.rss", collect_templates())] #XXX google keeps escaping the <> chars! arg!
				)
				self.write("sent backup to %s at %s" % (address, t))
		self.write("""
		<form action="/admin" method="post">
		<input type="hidden" name="email_backup" value="yes">
		<input type="submit" value="Email me a backup" />
		</form>
		</p>
		""")

		template_name = self.request.get("template_name")
		template = PageTemplate.all().filter("name =", template_name).get()
		saved = False
		if template:
			self.write("<p>")
			template_text = self.request.get("template_text")
			if template_text.strip():
				template.text = template_text
				template.modified = datetime.datetime.now()
				template.username = user.nickname()
				template.put()
				saved = True
			if saved:
				self.write("<strong>saved</strong><br />")
			self.write("last_modified(<em>%s</em>) = %s" % (template.name, template.modified))
			self.write("</p>")

		query = PageTemplate.all()
		for template in query.order("name"):
			modified = template.modified
			template_name = template.name
			template_text = htmlquote(template.text)
			self.write("""
<h2>%(template_name)s</h2>
<p>
<form action="/admin" method="post">
<textarea name="template_text" cols="80" rows="20">%(template_text)s</textarea>
<input type="hidden" name="template_name" value="%(template_name)s">
<input type="submit" value="Save" />
modified %(modified)s
</form>
</p>
			""" % locals())

		self.print_footer()

	post = get

class AboutPage(Page):
	name = "about"
	def get(self):
		self.print_header()
		self.print_menu()
		self.write(get_template("about") % locals())
		self.print_footer()

class DebugPage(Page):
	name = "debug"
	def get(self):
		self.print_header()
		self.print_menu()

		#~ http://wiki.python.org/moin/PyPiXmlRpc
		server = xmlrpclib.ServerProxy('http://pypi.python.org/pypi', transport=GoogleXMLRPCTransport())

		result = server.package_releases('roundup')
		self.write(result)

		result = server.package_urls('roundup', '1.1.2')
		self.write(result)

		self.print_footer()

application = webapp.WSGIApplication([
	('/', MainPage),

	('/scikits', PackagesPage),
	('/(scikits[.].+)', PackageInfoPage),

	('/about', AboutPage),

	#~ ('/recent_changes', RecentChangesPage),
	('/search', SearchPage),
	('/admin', AdminPage),
	('/debug', DebugPage),

	('/(.+)', PackageInfoPage),
	], debug=True)

def main():
	System.init()
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
	main()
