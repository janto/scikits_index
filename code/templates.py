header_template = """

<html>
<head>
	<title>SciKits - %(title)s</title>
	<script type="text/javascript" src="/static/jquery.js"></script>
	<script type="text/javascript" src="/static/jquery.corners.min.js"></script>

	<link href="/static/sphinxdoc.css" rel="stylesheet" type="text/css" />

</head>

<body>

<div style="background-color: white; text-align: left; padding: 10px 10px 15px 15px">
<table></tr>
<td><a href="/"><img src="/static/images/scipyshiny_small.png" width="64" border="0" /></a>
<td><a href="/"><span style="font-size: 36px;">SciKits</span></a></td>
</tr></table>
</div>

<div class="related">
	<h3>Navigation</h3>
	<ul>
	<li><a href="/">Home</a> |&nbsp;</li>
	<li><a href="/about">About SciKits</a> |&nbsp;</li>
	<li><a href="/scikits">Get SciKits</a> |&nbsp;</li>
	<li><a href="/contribute">Contribute</a></li>
	</ul>
</div>

<div class="sphinxsidebar">
<div class="sphinxsidebarwrapper">

	%(admin_sidebar_html)s

	<h3>Quick search</h3>
	%(search_box_html)s

</div>
</div>

<div class="document">
<div class="documentwrapper">
<div class="bodywrapper">
<div class="body">

<div class="section" id="%(title)s">

"""

footer_template = """

</div> <!-- section -->
</div> <!-- body -->
</div> <!-- bodywrapper -->
</div> <!-- documentwrapper -->
</div> <!-- document -->

<div class="clearer"></div>

<div class="footer">
See the <a href="http://code.google.com/p/scikits-index/source/checkout">source</a>.
Created page in %(load_time)0.3f seconds. <a href="/admin">Admin</a>.
<br />
Designed by <a href="http://janto.blogspot.com/">Janto Dreijer</a>.
Appearance based on <a href="http://sphinx.pocoo.org/">Sphinx</a> and <a href="http://www.vistaicons.com/icon/i160s0/phuzion_icon_pack.htm">Phuzion icons</a>.
</div>

<script>
$(document).ready( function(){
	$('.rounded').corners();
});
</script>

%(google_analytics)s

</body>
</html>

"""

# =======================================

main_page_template = """
<h1>SciKits</h1>
<p>
Scipy Toolkits are separately installable projects hosted under a common namespace.
They are separate from the scipy library because they are either too specialized, have incompatible licensing terms or is meant for eventual inclusion.
</p>

<p>

<table class="contentstable" align="center" style="margin-left: 30px"><tr>
	<td width="50%%">
	<p class="biglink"><a class="biglink" href="/about">About SciKits</a><br/>
	<span class="linkdescr">what scikits are all about</span></p>
	<p class="biglink"><a class="biglink" href="/scikits">Get SciKits</a><br/>
	<span class="linkdescr">index of all scikits</span></p>
	<p class="biglink"><a class="biglink" href="/contribute">Contribute</a><br/>
	<span class="linkdescr">add your own scikit or join a project</span></p>
	</td>
</tr>
</table>

</p>

"""

about_template = """

<h1>About SciKits</h1>

<p>
Scipy Toolkits are independent and seperately installable projects hosted under a common namespace. Packages that are distributed in this way are here (instead of in monolithic scipy) for at least one of three general reasons. Each of these reasons use the same high-level namespace (scikits).
<ol>
<li> The package is deemed too specialized to live in scipy itself, but is targeted at the same community.
<li> The package has a GPL (or similar) license which is too restrictive to live in scipy itself.
<li> The package is meant for eventual inclusion in the scipy namespace but is being developed as a separately installed package. It is generally the responsibility of the package writer to push for inclusion into SciPy if that is the desire. However, some packages may be moved into SciPy by other interested SciPy developers after approval by the SciPy steering committee.
</ol>
</p>

<h3>About the package listing</h3>

<p>The goal is to introduce people to scikits packages that are relavant to them and get them to where they need to be fast.
one page summary of all packages in repository, short descriptions, quick installs and links</p>

<p>This websites acts as a simple layer on top of PyPI and the web interface to the subversion repository.
Hosting of release files is done on PyPI. PyPI already has basic project management that can be leveraged.</p>

<h4>About the implementation</h4>

<p>More specifically it is a Google web app that intermittently scans http://svn.scipy.org/svn/scikits/trunk/ for new packages.
Information about the packages is collected from PyPI (via DOAP info: name, description, homepage/wiki, download page, easy_install) and the repository (primarily its location and possibly README file content).</p>

<p>
Assuming a developer has code (based on example scikit) somewhere under http://svn.scipy.org/svn/scikits/trunk/ he should:
<ol>
<li>create a username at PyPI.
<li>modify his setup.py
<li>run "python setup.py register"
</ol>
</p>

<p>
When a developer wants to update his kit's information, he should update his setup.py and rerun "python setup.py register".
</p>

<p>
When a developer wants to release a new version of his kit he either manually uploads it to PyPI or uses distutils (e.g. "python setup.py sdist bdist_wininst upload" [http://www.python.org/doc/2.5.2/dist/package-upload.html).
</p>

<h4>registering a package under scikits namespace</h4>
contact David

<br />
"""

contribute_page_template = """
<h1>Contribute</h1>

<h3>Add your own package</h3>
<p>
<!-- Register at PyPI or add to SVN repository -->
</p>

<h3>Join a project</h3>
<p>
Join a mailing list.
</p>

"""

package_info_template = """
<a href="" style="text-decoration:none"><h1>%(name)s</h1></a>
<i>%(revision)s</i>
<p>
%(shortdesc)s
</p>

<p>
<img src="/static/images/download_large.png" width="16" border="0" /> Download:  %(download_link)s <br />
Homepage: <a href="%(homepage)s">%(homepage)s</a> <br />
PyPI: <a href="http://pypi.python.org/pypi/%(name)s">http://pypi.python.org/pypi/%(name)s</a> <br />
Source Repository: <a href="%(repo_url)s">%(repo_url)s</a> <br />
People: %(people)s <br />
</p>

<h3>Description</h3>
<i>fetched from source</i>
<div style="background-color:#f0f0f0; padding:5px" class="rounded">
%(escaped_description)s
</div>

<h3>Installation</h3>

<h4>PyPI</h4>
<p>
You can download the latest distribution from PyPI here: <a href="http://pypi.python.org/pypi/%(name)s">http://pypi.python.org/pypi/%(name)s</a>
</p>

<h4>EasyInstall</h4>
<p>
Install the <a href="http://peak.telecommunity.com/DevCenter/EasyInstall">EasyInstall</a> tools. Afterwards you can install %(name)s from the terminal by executing:
<code>sudo easy_install %(name)s</code>
</p>

<h4>Source code</h4>
<p>
You can get the latest sources from the repository
<code>svn checkout <a href="%(repo_url)s">%(repo_url)s</a></code>
</p>

"""