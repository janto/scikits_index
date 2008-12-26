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
		e.g. connection to a remote server lost and reusing old data
	error
		unrecoverable
		additional try-catch info

"""

class Page(webapp.RequestHandler):

	name = ""

	def __init__(self):
		self.init_time = time.time()
		webapp.RequestHandler.__init__(self)
		self.logger = logging.getLogger(self.name)

	def write(self, text):
		self.response.out.write(text)

	def print_header(self):
		title = self.name
		search_box_html = SearchPage.search_box()

		# latest changes
		checked_urls = [] # the urls checked for updates
		show_latest_changes = 1
		newest_packages_html = ""
		if show_latest_changes:
			newest_packages_html = []

			for package in Package.packages().values():
				short_name = package.info()["short_name"]
				package_news_items, _checked_urls = package.release_files(return_checked_urls=True)
				checked_urls.extend(_checked_urls)
				if package_news_items:
					actions = ", ".join(name for name, _url, t in package_news_items)
					newest_packages_html.append('<a href="/%(short_name)s" title="%(actions)s">%(short_name)s</a><br />\n' % locals())

			newest_packages_html = "\n".join(sorted(newest_packages_html)[:5])
			if newest_packages_html:
				#~ feed_icon = '<a href="/rss.xml" style="font: bold 0.75em sans-serif; color: #fff; background: #f60; padding: 0.2em 0.35em; float: left;">RSS</a>'
				feed_icon = '<a href="/rss.xml" style="font: 0.75em sans-serif; text-decoration: underline">(RSS)</a>'
				newest_packages_html = '<h3>Latest Releases %s</h3>\n%s' % (feed_icon, newest_packages_html)

		# force a fetch of one of the http listings
		key = "next_listing_url_index"
		n = memcache.get(key)
		if n is None:
			n = 0
		memcache.set(key, (n+1) % len(checked_urls)) # set the next url to be fetched
		url = checked_urls[n]
		self.logger.info("forcing fetch of url: %s" % url)
		newest_packages_html += "<!-- forced fetch of url : %s -->\n" % url
		get_url(url, force_fetch=True, cache_duration=PACKAGE_NEWS_CACHE_DURATION)

		# admin sidebar
		admin_sidebar_html = ""
		if users.is_current_user_admin():
			admin_sidebar_html = """
			<h3><a href="/admin">Admin</a></h3>
				<ul>
				<li><a href="%s">Sign Out</a></li>
				<li><a href="http://appengine.google.com/dashboard?&app_id=scikits">GAE Dashboard</a> </li>
				<li><a href="http://code.google.com/appengine/docs/">GAE Docs</a> </li>
				<li><a href="https://www.google.com/analytics/reporting/?reset=1&id=13320564">Analytics</a> </li>
				</ul>
			""" % users.create_logout_url("/admin")

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

class ContributePage(Page):

	name = "contribute"

	def get(self):
		self.print_header()
		self.print_menu()
		self.write(get_template("contribute_page") % locals())
		self.print_footer()

class PackagesPage(Page):

	name = "scikits"

	def get(self):
		self.print_header()
		self.print_menu()

		packages = sorted(Package.packages().values())

		# force fetch of some package
		if packages:
			key = "next_package_fetch_index"
			n = memcache.get(key)
			if n is None:
				n = 0
			memcache.set(key, (n+1) % len(packages)) # set the next package to be fetched
			n %= len(packages) # in case a kit is removed
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
		package = Package.packages().get(package_name)
		if package is None:
			package_name = "scikits.%s" % package_name
			package = Package.packages().get(package_name)
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
		<td><a href="/%(short_name)s">%(short_name)s</a></td>
		<td>%(shortdesc)s</td>
		</tr>
		""" % dictadd(p.__dict__, d, locals())
		result.append(r)
	result.append("</table>")
	return "\n".join(result)

class Package(object):
	def __init__(self, name, repo_url):
		"""
		init should cache minimal information. actual information extraction should be done on page requests. with memcaching where needed.
		"""
		self.name = name
		self.repo_url = repo_url

	def release_files(self, return_checked_urls=False):
		first_char = self.name[0]
		package_name = self.name
		short_name = self.info()["short_name"]

		oldest = datetime.datetime.fromtimestamp(time.time() - SECONDS_IN_WEEK * 3)

		package_news_items = []
		checked_urls = []
		for dist in ["2.5", "2.6", "3.0", "any", "source"]: # check various distributions
			url = "http://pypi.python.org/packages/%(dist)s/%(first_char)s/%(package_name)s/" % locals()
			checked_urls.append(url) # remember for forcing fetch
			items = fetch_links_with_dates(url, cache_duration=PACKAGE_NEWS_CACHE_DURATION)
			if items is None:
				continue
			package_news_items.extend([(name, _url, t) for name, _url, t in items if oldest < t])
		package_news_items.sort(key=lambda c: (c[-1], c[0])) # oldest first

		if return_checked_urls:
			return package_news_items, checked_urls

		return package_news_items

	@classmethod
	def packages(self):
		packages, expired = Cache.get("packages")
		if expired or packages is None:
			packages = {}

			from_repo = 1
			if from_repo:
				for repo_base_url in [
						"http://svn.scipy.org/svn/scikits/trunk",
						"http://svn.scipy.org/svn/scikits/trunk/learn/scikits/learn/machine/",
						]:
					logger.info("loading packages from repo %s" % repo_base_url)
					for repo_url in fetch_dir_links(repo_base_url):
						package_name = "scikits.%s" % os.path.split(repo_url)[1]
						if package_name in packages:
							continue


						# check if really a package
						#~ url = os.path.join(repo_url, "setup.py")
						#~ result = get_url(url)
						#~ if result.status_code != 200: # setup.py was not found
							#~ continue

						package = Package(name=package_name, repo_url=repo_url)
						packages[package.name] = package

			from_pypi_search = 1
			if from_pypi_search:
				logger.info("loading packages from PyPI")
				server = xmlrpclib.ServerProxy('http://pypi.python.org/pypi', transport=GoogleXMLRPCTransport())
				results = server.search(dict(name="scikits"))
				for package_name in set(result["name"] for result in results): # unique names, pypi contains duplicate names

					#XXX remove this once no longer scanning repo for package name
					if package_name in packages:
						continue

					repo_url = "" #XXX where can we get this?
					package = Package(name=package_name, repo_url=repo_url)
					packages[package.name] = package

			assert Cache.set(key="packages", value=packages, duration=PACKAGE_LISTING_CACHE_DURATION), package

		return packages

	def __cmp__(self, other):
		return cmp(self.name, other.name)

	def python_versions(self):
		#XXX xmlrpc call truncated?
		return

		server = xmlrpclib.ServerProxy('http://pypi.python.org/pypi', transport=GoogleXMLRPCTransport())
		release_versions = server.package_releases(self.name)
		python_versions = []
		for release_version in sorted(release_versions, reverse=True):
			for d in server.release_urls(self.name, release_version):
				release_versions.append(d["python_version"])
			break #XXX only the biggest listed version number?
		return python_versions

	def download_links_html(self):
		#XXX xmlrpc call truncated?
		return

		text = []
		server = xmlrpclib.ServerProxy('http://pypi.python.org/pypi', transport=GoogleXMLRPCTransport())
		versions = server.package_releases(self.name)
		for version in sorted(versions, reverse=True):
			text.append("<table>")
			text.append("""<tr>
				<th>Python version</th>
				<th>URL</th>
				<th>Size</th>
				</tr>""")
			for d in server.release_urls(self.name, version):
				text.append("<tr>")
				text.append("""
				<td>%(python_version)s</td>
				<td><a href="%(url)s">%(filename)s</a></td>
				<td>%(size)s</td>
				"""% d)
				text.append("</tr>")
			text.append("</table>")

			break #XXX only the biggest listed version number?
		return "\n".join(text)

	def info(self, force_fetch=False):
		d = dict(
			name=self.name,
			shortdesc="",
			description="",
			homepage="",
			revision="",
			people="",
			)
		doap_result = get_url(
			"http://pypi.python.org/pypi?:action=doap&name=%s" % self.name,
			force_fetch=force_fetch,
			cache_duration=PACKAGE_INFO_CACHE_DURATION,
			)
		if doap_result.status_code == 200:

			doap_text = doap_result.content
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

		escaped_description = htmlquote(d["description"]).replace(r"\n", "<br />\n")

		revision = d.get("revision")
		revision = ("version " + revision) if revision else ""

		return get_template("package_info") % dictadd(self.__dict__, d, locals())

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
		query_text = self.request.get("text").strip()

		self.write("<p>")
		self.write(self.search_box(default=query_text))
		self.write("</p>")

		field_weight = dict(name=100, shortdesc=50, description=25)
		weights_packages = []
		for package in Package.packages().values():
			w = 0
			for field, text in package.info().items():
				n = query_text in text.lower()
				w += field_weight.get(field, 1) * n
			if 0 < w:
				weights_packages.append((-w, package)) # negate value, so results with equal weight are alphabetical wrt names when sorted
		weights_packages.sort() # highest scoring first
		if weights_packages:
			weights, packages = zip(*weights_packages)
			self.write("\n<!-- ")
			self.write(weights)
			self.write(" -->\n")
		else:
			packages = []

		self.write("<p>search results for <strong>%s</strong>:<br />" % (htmlquote(query_text) or "all"))
		if packages:
			self.write(table_of_packages(packages))
		else:
			self.write("<strong>no matches</strong>")
		self.write("</p>")

		self.print_footer()

def get_template(name):
	template = PageTemplate.all().filter("name =", name).get()
	if template is not None:
		return template.text
	return getattr(templates, name+"_template").strip()

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
		template_text = template.text.strip()
		result.append('''
%(template_name)s_template = """
%(template_text)s
"""
	'''.strip() % locals())
	return "\n".join(result)

class EditPage(Page):
	editors = [
		"jantod"+"@gmail.com",
		"sjvdwalt"+"@gmail.com",
		"damian.eads"+"@gmail.com",
	]
	name="edit"
	def get(self):
		"""
		@template_name
		@template_text

		@email_backup
		"""
		self.print_header()
		self.print_menu()

		# authorize

		user = users.get_current_user()
		self.write("<p>")
		if not user:
			self.write('only site editors allowed here.\n')
			self.write('<a href="%s">sign in</a>' % users.create_login_url("/edit"))
			self.print_footer()
			return
		if users.get_current_user().email().lower() not in self.editors:
			self.write('only site editors allowed here.\n')
			self.write('<a href="%s">sign out</a>.' % users.create_logout_url("/edit"))
			self.print_footer()
			return
		self.write("welcome %s.\n" % user.nickname())
		self.write('<a href="%s">sign out</a>.' % users.create_logout_url("/edit"))
		self.write("</p>")

		# backup and stats

		self.write("<h1>Page Templates</h1>")
		self.write("<p>")
		if self.request.get("email_backup") == "yes":
			t = datetime.datetime.now()
			address = users.get_current_user().email()
			if address:
				mail.send_mail(sender="jantod@gmail.com",
					to=address,
					subject="scikits index backup %s" % t,
					body="""Here's the backups. \nIf there isn't anything attached to this message then all pages were loaded from the template.py file.""",
					attachments=[("templates.py.txt", collect_templates())]
				)
				self.write("sent backup to %s at %s" % (address, t))
		self.write("""
		<form action="/edit" method="post">
		<input type="hidden" name="email_backup" value="yes">
		<input type="submit" value="Email me a backup" />
		</form>
		</p>
		""")

		# save modifications

		template_name = self.request.get("template_name")
		template_text = self.request.get("template_text", "").strip()
		if template_name and template_text: # user provided new content
			template = PageTemplate.all().filter("name =", template_name).get()
			if not template:
				template = PageTemplate(name=template_name)
			template.text = template_text
			template.modified = datetime.datetime.now()
			template.username = user.nickname()
			template.put()

			self.write("<p>")
			self.write("<strong>saved</strong><br />")
			self.write("last_modified(<em>%s</em>) = %s" % (template.name, template.modified))
			self.write("</p>")

		# list templates
		for template_name in [
			"header",
			"footer",
			"main_page",
			"about",
			"contribute_page",
			"package_info",
		]:
			# check if in db
			template = PageTemplate.all().filter("name =", template_name).get()
			if template:
				template_text = htmlquote(template.text)
				modified_time = "modified %s," % template.modified
				modified_username = "by %s" % template.username
			else:
				template_text = htmlquote(get_template(template_name))
				modified_time = "never modified,"
				modified_username = "loading from <i>template.py</i>"

			self.write("""
<h2>%(template_name)s</h2>
<p>
<form action="/edit" method="post">
<textarea name="template_text" cols="80" rows="20">%(template_text)s</textarea>
<input type="hidden" name="template_name" value="%(template_name)s">
<br />
<input type="submit" value="Save" />
%(modified_time)s %(modified_username)s
</form>
</p>
			""" % locals())

		self.print_footer()

	post = get

class AdminPage(Page):

	name="admin"
	def get(self):
		"""
		@clear_memcache

		"""
		self.print_header()
		self.print_menu()

		# authorize

		user = users.get_current_user()
		self.write("<p>")
		if not user:
			self.write('only site admins allowed here.\n')
			self.write('<a href="%s">sign in</a>' % users.create_login_url("/admin"))
			self.print_footer()
			return
		if not users.is_current_user_admin():
			self.write('only site admin allowed here.\n')
			self.write('<a href="%s">sign out</a>.' % users.create_logout_url("/admin"))
			self.print_footer()
			return
		self.write("welcome %s.\n" % user.nickname())
		self.write('<a href="%s">sign out</a>.' % users.create_logout_url("/admin"))
		self.write("</p>")

		self.write("""

		<a href="http://feedvalidator.org.li.sabren.com/check.cgi?url=http%3A//scikits.appspot.com/rss.xml">validate rss</a>

		""")

		# memcache management
		self.write("<h2>memcache</h2>")
		if self.request.get("clear_memcache"):
			memcache.flush_all()
			self.write("<p><strong>flushed memcache</strong></p>")

		self.write("""
<p>
%s
<form action="/admin" method="post">
<input type="hidden" name="clear_memcache" value="1">
<input type="submit" value="Flush" />
</form>
</p>
		""" % memcache.get_stats())

		key = "next_package_fetch_index"
		self.write("<h3>%s</h3>" % key)
		self.write(memcache.get(key))

		key = "next_listing_url_index"
		self.write("<h3>%s</h3>" % key)
		self.write(memcache.get(key))

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


		for p in Package.packages().values():
			self.write("<h4>%s</h4>\n" % p.name)
			self.write(p.python_versions())

		self.print_footer()

class RobotsPage(Page):
	def get(self):
		return

class RSSFeedPage(Page):
	def get(self):

		items = []
		for package in Package.packages().values():
			d = package.info()
			short_name = d["short_name"]
			for (name, url, t) in package.release_files():
				rss_item = PyRSS2Gen.RSSItem(
					title = name,
					link = "http://scikits.appspot.com/%s" % short_name,
					description = 'Released file: <a href="%(url)s">%(url)s</a>' % locals(),
					guid = PyRSS2Gen.Guid("http://scikits.appspot.com/%(short_name)s?feed_release=%(name)s" % locals()),
					pubDate = t)
				items.append(rss_item)

		rss = PyRSS2Gen.RSS2(
			title = "SciKits",
			link = "http://scikits.appspot.com/",
			description = "SciKits released via PyPI",
			lastBuildDate = datetime.datetime.now(),
			items = items)

		self.write(rss.to_xml("utf-8"))

application = webapp.WSGIApplication([
	('/', MainPage),

	('/scikits', PackagesPage),
	('/(scikits[.].+)', PackageInfoPage),

	('/about', AboutPage),
	('/contribute', ContributePage),

	#~ ('/recent_changes', RecentChangesPage),
	('/search', SearchPage),
	('/admin', AdminPage),
	('/debug', DebugPage),
	('/edit', EditPage),
	('/robots.txt', RobotsPage),
	('/rss.xml', RSSFeedPage),

	('/(.+)', PackageInfoPage),
	], debug=True)

def main():
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
	main()
