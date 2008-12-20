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
	<li><a href="/scikits">Download a SciKit</a> |&nbsp;</li>
	<li><a href="/contribute">Contribute</a></li>
	</ul>
</div>

<div class="sphinxsidebar">
<div class="sphinxsidebarwrapper">

	%(admin_sidebar_html)s

	%(newest_packages_html)s

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
Created page in %(load_time)0.3f seconds. <a href="/edit">Edit Pages</a>.
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
<p>
Welcome to SciKits!  Here you'll find a searchable index of
add-on toolkits that complement <a href="http://www.scipy.org">SciPy</a>, a library of scientific computing routines.
</p>

<p>
The SciKits cover a broad spectrum of application domains,
including financial computation, audio processing, geosciences,
computer vision, engineering, machine learning, medical computing
and bioinformatics.  <a href="/about">Learn more...</a>
</p>

<p>

<table class="contentstable" align="center" style="margin-left: 30px"><tr>
	<td width="50%%">

	<p class="biglink">
	<img src="/static/images/download_large.png" width="32" style="float: left; padding-bottom: 20px; padding-right: 10px;"/>
	<a class="biglink" href="/scikits">Download a SciKit</a><br/>
	<span class="linkdescr">Index of all SciKits.</span>
	</p>

	<p class="biglink">
	<img src="/static/images/organize.png" width="32" style="float: left; padding-bottom: 20px; padding-right: 10px;"/>
	<a class="biglink" href="/contribute">Contribute</a><br/>
	<span class="linkdescr">Add your own SciKit or join an existing project.</span>
	</p>

	</td>
</tr>
</table>

</p>
"""

about_template = """

<h1>About SciKits</h1>

<p>
SciPy Toolkits are independent and seperately installable projects hosted under a common namespace. Packages that are distributed in this way are here (instead of in monolithic SciPy) for at least one of three general reasons. Each of these reasons use the same high-level namespace (scikits).
<ol>
<li> The package is deemed too specialized to live in SciPy itself, but is targeted at the same community.
<li> The package has a GPL (or similar) license which is too restrictive to live in SciPy itself.
<li> The package is meant for eventual inclusion in the SciPy namespace but is being developed as a separately installed package. It is generally the responsibility of the package writer to push for inclusion into SciPy if that is the desire. However, some packages may be moved into SciPy by other interested SciPy developers after approval by the SciPy steering committee.
</ol>
</p>

"""

contribute_page_template = """
<h1>Contribute</h1>

<h3>Add your own package</h3>

<p>
<a href="http://www.scipy.org/scipy/scikits/">SciKits developer resources</a>
</p>

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

<h4>Easy Install</h4>
<p>
Install the <a href="http://peak.telecommunity.com/DevCenter/EasyInstall">Easy Install</a> tools. Afterwards you can install %(name)s from the terminal by executing:
<pre>sudo easy_install %(name)s</pre>
</p>

<p>
If you prefer to do a local installation, specify an installation prefix:
<pre>easy_install --prefix=${HOME} %(name)s</pre>
and ensure that your <code>PYTHONPATH</code> is up to date, e.g.:
<pre>export PYTHONPATH=$PYTHONPATH:${HOME}/lib/python2.5/site-packages</pre>
</p>

<h4>Source code</h4>
<p>
You can get the latest sources from the repository using
<pre>svn checkout <a href="%(repo_url)s">%(repo_url)s</a></pre>
</p>

"""