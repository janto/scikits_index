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

class NoSuchTemplateException(Exception):
	pass

class Page(webapp.RequestHandler):

	name = ""

	def __init__(self):
		self.init_time = time.time()
		webapp.RequestHandler.__init__(self)
		self.logger = logging.getLogger(self.name)

	def write(self, text):
		self.response.out.write(text)

	def print_header(self, title=None):
		template_values = {}
		template_values["name"] = title or self.name
		template_values["search_box_html"] = SearchPage.search_box()

		# latest changes
		#XXX codeblock waaaay too complex
		t = time.time()
		checked_urls = [] # the urls checked for updates
		show_latest_changes = 0
		newest_packages_html = ""
		if show_latest_changes:
			# create html lines
			newest_packages_html_lines = []
			for package in Package.packages().values():
				short_name = package.info()["short_name"]
				news_items, _checked_urls = package.release_files(return_checked_urls=True)
				checked_urls.extend(_checked_urls)
				if news_items:
					actions = ", ".join(name for name, _url, t in news_items)
					last_update_time = max(t for name, _url, t in news_items)
					last_update_time_string = last_update_time.strftime("%d %b %Y")
					#~ t = t.strftime("%d %b" if t.year == datetime.datetime.now().year else "%d %b %Y")
					html = '<a href="/%(short_name)s" title="%(actions)s">%(short_name)s</a> <span style="font-size: 10px; color:gray;">%(last_update_time_string)s</span><br />\n' % locals()
					newest_packages_html_lines.append((last_update_time, html))

			newest_packages_html = "\n".join(html for last_update_time, html in sorted(newest_packages_html_lines, reverse=True))
			if newest_packages_html:
				#~ feed_icon = '<a href="/rss.xml" style="font: bold 0.75em sans-serif; color: #fff; background: #f60; padding: 0.2em 0.35em; float: left;">RSS</a>'
				feed_icon = '<a href="/rss.xml" style="font: 0.75em sans-serif; text-decoration: underline">(RSS)</a>'
				newest_packages_html = '<h3>Latest Releases %s</h3>\n%s' % (feed_icon, newest_packages_html)
		template_values["newest_packages_html"] = newest_packages_html
		self.write("<!-- checked changes in %0.2f sec -->" % (time.time() - t))

		# admin sidebar
		template_values["admin_sidebar_html"] = ""
		if users.is_current_user_admin():
			template_values["admin_sidebar_html"] = """
				<h3><a href="/admin">Admin</a></h3>
				<ul>
				<li><a href="/admin">Admin Page</a></li>
				<li><a href="http://appengine.google.com/dashboard?&app_id=scikits">GAE Dashboard</a> </li>
				<li><a href="http://code.google.com/appengine/docs/">GAE Docs</a> </li>
				<li><a href="https://www.google.com/analytics/reporting/?reset=1&id=13320564">Analytics</a> </li>
				</ul>
			"""

		# editor sidebar
		template_values["editor_sidebar_html"] = ""
		if is_current_user_editor():

			html = ['<h3><a href="/edit">Edit</a></h3>']
			html.append('<ul>')
			try:
				get_template(self.name)
				html.append('<li><a href="/edit?template_name=%s">Edit this page</a>' % self.name)
			except NoSuchTemplateException:
				pass
			html.append('<li><a href="/edit">Edit all pages</a>')
			html.append('</ul>')

			template_values["editor_sidebar_html"] = "\n".join(html)

		self.write(render_template("header", template_values))

	def print_footer(self, title=None):
		template_values = {}
		template_values["name"] = title or self.name

		# google analytics
		# http://code.google.com/apis/analytics/docs/gaTrackingOverview.html
		if ON_DEV_SERVER:
			template_values["google_analytics"] = "<!-- google analytics skipped when not run at google -->"
		else:
			template_values["google_analytics"] = """
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

		url_requested = os.environ["PATH_INFO"] + "?" + os.environ["QUERY_STRING"]
		if users.get_current_user():
			template_values["login_logout_html"] = '<a href="%s">Sign out</a>.' % users.create_logout_url(url_requested)
		else:
			template_values["login_logout_html"] = '<a href="%s">Sign in</a>' % users.create_login_url(url_requested)

		template_values["load_time"] = "%0.3f" % (time.time() - self.init_time)
		self.write(render_template("footer", template_values))

	def print_menu(self):
		pass

class WorkerPage(Page):
	name = "worker"

	def get(self):
		checked_urls = []
		for package in Package.packages().values():
			news_items, _checked_urls = package.release_files(return_checked_urls=True)
			checked_urls.extend(_checked_urls)

		# force a fetch of one of the http listings
		t = time.time()
		key = "next_listing_url_index"
		n = memcache.get(key)
		if n is None:
			n = 0
		memcache.set(key, (n+1) % len(checked_urls)) # set the next url to be fetched
		url = checked_urls[n]
		report = "forcing fetch of url: %s (n=%d/%d)" % (url, n, len(checked_urls))
		self.logger.info(report)
		self.write("<li>"+report)
		get_url(url, force_fetch=True, cache_duration=PACKAGE_NEWS_CACHE_DURATION)
		report = "<li>fetched url in %0.2f seconds" % (time.time() - t)
		self.logger.info(report)
		self.write(report)

class MainPage(Page):

	name = "main"

	def get(self):
		if memcache.get("turn_off_website"):
			self.write("""
			<html><body>
			We are experiencing some technical difficulties.
			<br />In the meantime have a look at
			<a href="http://pypi.python.org/pypi?:action=search&term=scikits&submit=search">PyPI's scikits listing</a>
			</body></html>
			""")
			return
		self.print_header()
		self.print_menu()
		self.write(render_template(self.name, locals()))
		self.print_footer()

class ContributePage(Page):

	name = "contribute"

	def get(self):
		self.print_header()
		self.print_menu()
		self.write(render_template(self.name, locals()))
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
	name = "package_info"

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

		self.print_header(title=package.name)
		self.print_menu()

		self.write(package.to_html())

		self.print_footer(title=package.name)

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
	def __init__(self, name, repo_url, info_source=""):
		"""
		init should cache minimal information. actual information extraction should be done on page requests. with memcaching where needed.
		"""
		self.name = name
		self.repo_url = repo_url
		self.info_source = info_source

	def release_files(self, return_checked_urls=False):
		logger.debug(self.name)
		first_char = self.name[0]
		package_name = self.name
		short_name = self.info()["short_name"]

		oldest = datetime.datetime.fromtimestamp(time.time() - SECONDS_IN_MONTH)

		package_news_items = []
		checked_urls = []
		for dist in ["2.5", "2.6", "2.7", "3.0", "any", "source"]: # check various distributions
			url = "http://pypi.python.org/packages/%(dist)s/%(first_char)s/%(package_name)s/" % locals()
			checked_urls.append(url) # remember for forcing fetch
			items = fetch_links_with_dates(url, cache_duration=PACKAGE_NEWS_CACHE_DURATION)
			if items is None:
				continue
			#~ package_news_items.extend([(name, _url, t) for name, _url, t in items if oldest < t])
			package_news_items.extend([(name, _url, t) for name, _url, t in items]) #XXX temporarily disabled date threshold - not enough recent updates
		package_news_items.sort(key=lambda c: (c[-1], c[0])) # oldest first

		if return_checked_urls:
			return package_news_items, checked_urls

		return package_news_items

	@classmethod
	def packages(self):
		packages, expired = Cache.get("packages")
		if expired or packages is None:
			packages = {}

			from_pypi_search = 1
			if from_pypi_search:
				logger.info("loading packages from PyPI")
				server = xmlrpclib.ServerProxy('http://pypi.python.org/pypi', transport=GoogleXMLRPCTransport())
				results = server.search(dict(name="scikits"))
				for package_name in set(result["name"] for result in results): # unique names, pypi contains duplicate names

					#~ package_name_short = package_name.split(".", 1)[0] if package_name.startswith("scikits.") else package_name
					repo_url = "" #XXX where can we get this?
					package = Package(name=package_name, repo_url=repo_url, info_source="PyPI")
					packages[package.name] = package

			from_repo = 1
			if from_repo:
				for repo_base_url in [
						"http://svn.scipy.org/svn/scikits/trunk",
						]:
					logger.info("loading packages from repo %s" % repo_base_url)
					for repo_url in fetch_dir_links(repo_base_url):
						package_name = "scikits.%s" % os.path.split(repo_url)[1]

						# check if really a package
						#~ url = os.path.join(repo_url, "setup.py")
						#~ result = get_url(url)
						#~ if result.status_code != 200: # setup.py was not found
							#~ continue

						package = Package(name=package_name, repo_url=repo_url, info_source="svn.scipy.org")
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
			pypi_name="",
			info_source=self.info_source,

			shortdesc="",
			description="",

			homepage="",
			download_url="",

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
			d["pypi_name"] = d["name"]

			d["download_url"] = d.get("download-page", "") or ("http://pypi.python.org/pypi/%(name)s" % d)

		d["short_name"] = d["name"].split(".")[-1]

		# determine repository type and url

		urls = [
			self.repo_url,
			d["download_url"],
			d["homepage"],
		]
		repo_command = "svn checkout"
		for url in urls:

			if "svn" in url:
				repo_command = "svn checkout"
				self.repo_url = url
				break
			if "launchpad" in url:
				repo_command = "bzr branch"
				self.repo_url = url
				break
			if "bitbucket" in url or "hg" in url:
				repo_command = "hg clone"
				self.repo_url = url
				break
			if "git" in self.repo_url:
				repo_command = "git clone"
				self.repo_url = url
				break
		d["repo_command"] = repo_command

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

		try:
			escaped_description = rst2html(d["description"].replace(r"\n", "\n"))
		except docutils.utils.SystemMessage, e:
			escaped_description = ("<!-- DOCUTILS WARNING! %s -->\n" % str(e)) + htmlquote(d["description"]).replace(r"\n", "<br />\n")

		revision = d.get("revision")
		revision = ("version " + revision) if revision else ""

		return render_template("package_info", dictadd(self.__dict__, d, locals()))

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
				w += field_weight.get(field, 1) * n # other fields get scores of 1
			if 0 < w:
				weights_packages.append((-w, package)) # negate value, so results with equal weight are alphabetical wrt names when sorted
		weights_packages.sort() # best scoring first
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
	assert name, name
	template = DBPageTemplate.all().filter("name =", name).get()
	if template is not None:
		return template.text
	try:
		return getattr(templates, name+"_template").strip()
	except AttributeError:
		raise NoSuchTemplateException(name)

def render_template(template_name, d):
	return templating.Template(get_template(template_name)).render(templating.Context(d))

class DBPageTemplate(db.Model):
	name = db.StringProperty(required=True)
	text = db.TextProperty()
	modified = db.DateTimeProperty(auto_now=False)
	username = db.TextProperty()

def collect_templates():
	result = []
	query = DBPageTemplate.all()
	for template in query.order("name"):
		template_name = template.name
		template_text = template.text.strip()
		result.append('''
%(template_name)s_template = """
%(template_text)s
"""
	'''.strip() % locals())
	return "\n".join(result)

class DBEditors(db.Model):
	email = db.StringProperty(required=True)
	comment = db.StringProperty()

def is_current_user_editor():
	if users.is_current_user_admin():
		return True
	user = users.get_current_user()
	if user is None:
		return False
	addresses = [editor.email for editor in DBEditors.all().order("email")]
	addresses.extend([
		#~ "jantod"+"@gmail.com",
		#~ "sjvdwalt"+"@gmail.com",
		#~ "damian.eads"+"@gmail.com",
	])
	logger.debug(addresses)
	return user.email().lower() in addresses

class EditPage(Page):
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
		url_requested = os.environ["PATH_INFO"] + "?" + os.environ["QUERY_STRING"]
		if not user:
			self.write('only site editors allowed here.\n')
			self.write('<a href="%s">sign in</a>' % users.create_login_url(url_requested))
			self.print_footer()
			return
		if not is_current_user_editor():
			self.write('only site editors allowed here.\n')
			self.write('<a href="%s">sign out</a>.' % users.create_logout_url(url_requested))
			self.print_footer()
			return

		# backup and stats

		self.write("<h1>Page Templates</h1>")
		self.write("<p>Django style templates</p>")
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
			template = DBPageTemplate.all().filter("name =", template_name).get()
			if not template:
				template = DBPageTemplate(name=template_name)
			template.text = template_text
			template.modified = datetime.datetime.now()
			template.username = user.nickname()
			template.put()

			self.write("<p>")
			self.write("<strong>saved</strong><br />")
			self.write("last_modified(<em>%s</em>) = %s" % (template.name, template.modified))
			self.write("</p>")

		template_name = self.request.get("template_name", None)
		template_names = [template_name] if template_name is not None else templates.names

		# list templates
		for template_name in template_names:
			# check if in db
			template = DBPageTemplate.all().filter("name =", template_name).get()
			if template:
				template_text = htmlquote(template.text)
				modified_time = "modified %s," % template.modified
				modified_username = "by %s" % template.username
			else:
				template_text = htmlquote(get_template(template_name))
				modified_time = "never modified,"
				modified_username = "loading from <i>template.py</i>"

			self.write("""
<h2>template: <i>%(template_name)s</i></h2>
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
		@clear_memcache = 1
		@add_editor = 1
		@modify_editor = 1

		@email
		@comment

		"""
		self.print_header()
		self.print_menu()

		# authorize

		user = users.get_current_user()
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

		self.write("""

		<a href="http://feedvalidator.org.li.sabren.com/check.cgi?url=http%3A//scikits.appspot.com/rss.xml">validate rss</a>

		""")

		# manage editors
		email_address = self.request.get("email").strip()
		if self.request.get("add_editor"):
			editor = DBEditors(
				comment=self.request.get("comment"),
				email=email_address,
				)
			editor.put()
		if self.request.get("modify_editor"):
			editor = DBEditors.all().filter("email = ", self.request.get("old_email")).get()
			if editor is not None:
				if not email_address:
					editor.delete()
				else:
					# modify editor
					editor.comment= self.request.get("comment")
					editor.email = email_address
					editor.put()

		# view editors
		self.write("<h2>Editors</h2>")
		self.write("<p>clear email field to delete")
		for editor in DBEditors.all().order("email"):
			d = dict(comment=editor.comment, email=editor.email)
			self.write("""
			<form action="/admin" method="post">
			<input type="hidden" name="modify_editor" value="1">
			<input type="hidden" name="old_email" value="%(email)s">
			email: <input type="text" name="email" value="%(email)s">
			comment: <input type="text" name="comment" value="%(comment)s">
			<input type="submit" value="Save" />
			</form>
			""" % d)
		self.write("""
			<form action="/admin" method="post">
			<input type="hidden" name="add_editor" value="1">
			email: <input type="text" name="email" value="">
			comment: <input type="text" name="comment" value="">
			<input type="submit" value="Add" />
			</form>
			</p>
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

		self.write("<h2>dangerous settings</h2>")
		if self.request.get("turn_off_website"):
			memcache.set("turn_off_website", (self.request.get("turn_off_website") == "True"))
		self.write("<p><b>Warning</b>: setting this to true will disable access to the main page. You can only change the setting back to False from here (the admin page) or by clearing the memcache.</p>")
		self.write("turn_off_website = %s" % memcache.get("turn_off_website"))
		self.write("""
			<p>
			<form action="/admin" method="post">
			<input type="hidden" name="turn_off_website" value="%s">
			<input type="submit" value="Toggle" />
			</form>
			</p>
			""" % (not memcache.get("turn_off_website")))

		self.print_footer()

	post = get

class AboutPage(Page):
	name = "about"
	def get(self):
		self.print_header()
		self.print_menu()
		self.write(render_template("about", locals()))
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
		#XXX are new lines ignored?
		self.write("""
User-agent: *
Disallow: /static/
		""".strip())

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
	('/worker', WorkerPage),

	('/scikits', PackagesPage),
	('/(scikits[.].+)', PackageInfoPage),

	('/about', AboutPage),
	('/contribute', ContributePage),

	#~ ('/recent_changes', RecentChangesPage),
	('/search', SearchPage),
	('/admin', AdminPage),
	('/debug', DebugPage),
	('/edit', EditPage),
	#~ ('/robots.txt', RobotsPage),
	('/rss.xml', RSSFeedPage),

	('/(.+)', PackageInfoPage),
	], debug=True)

def main():
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
	main()
