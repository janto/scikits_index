"""
This might not be such a good way to store page temlplates, but what are the alternatives?
	I don't want to store it as part of the DB alone as I want this info available both when running a local GAE and on the online GAE.
	I don't want to store it as separate files, because then you won't be able to modify them from the web. GAE doesn't support writing to "files" (probably) for security reasons.

So the way of currenty doing things:
	Manually check the online version every few months if there were any modifications made to the templated pages. If there was, paste the new version into this page.
	Yes, it's disgusting. If you can think of a better way please let me know.

- Janto

"""

names = [
	"header",
	"footer",
	"main",
	"about",
	"contribute",
	"package_info",
]

header_template = """

<html>
<head>
	<title>SciKits - {{ name }}</title>
	<script type="text/javascript" src="/static/jquery.js"></script>
	<script type="text/javascript" src="/static/jquery.corners.min.js"></script>

	<link href="/static/sphinxdoc.css" rel="stylesheet" type="text/css" />
	<link href="/static/images/download_32.png" rel="icon" type="image/png" />
	<link href="/rss.xml" rel="alternate" type="application/rss+xml" title="SciKits Releases" />

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

	{{ admin_sidebar_html }}

	{{ editor_sidebar_html }}

	{{ newest_packages_html }}

	<h3>Quick search</h3>
	{{ search_box_html }}

</div>
</div>

<div class="document">
<div class="documentwrapper">
<div class="bodywrapper">
<div class="body">

<div class="section" id="{{ name }}">

"""

footer_template = """

</div> <!-- section -->
</div> <!-- body -->
</div> <!-- bodywrapper -->
</div> <!-- documentwrapper -->
</div> <!-- document -->

<div class="clearer"></div>

<div class="footer">
See the <a href="http://bitbucket.org/janto/scikits_index/">source</a>.
Created page in {{ load_time }} seconds. {{login_logout_html}}
<br />
Designed by <a href="http://janto.blogspot.com/">Janto Dreijer</a>.
Appearance based on <a href="http://sphinx.pocoo.org/">Sphinx</a> and <a href="http://www.vistaicons.com/icon/i160s0/phuzion_icon_pack.htm">Phuzion icons</a>.
</div>

<script>
$(document).ready( function(){
	$('.rounded').corners();
});
</script>

{{ google_analytics }}

<!--
The following page request is vital to the working of the site.
If it's not called then (see Issue#2)
-->
<script type="text/javascript">
jQuery.get("/worker?name={{ name }}");
</script>

</body>
</html>

"""

# =======================================

main_template = """
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
	<img src="/static/images/download_32.png" width="32" style="float: left; padding-bottom: 20px; padding-right: 10px;"/>
	<a class="biglink" href="/scikits">Download a SciKit</a><br/>
	<span class="linkdescr">Index of all SciKits.</span>
	</p>

	<p class="biglink">
	<img src="/static/images/organize_32.png" width="32" style="float: left; padding-bottom: 20px; padding-right: 10px;"/>
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
SciKits (short for SciPy Toolkits), are add-on packages for <a href="http://www.scipy.org">SciPy</a>, hosted and developed separately from the main SciPy distribution.  All SciKits are available under the 'scikits' namespace and are licensed under <a href="http://www.opensource.org">OSI-approved licenses</a>.
</p>
<p>
Packages are packaged as toolkits (instead of in the main, monolithic SciPy distribution) when:
<ol>
<li>The package is deemed too specialized to live in SciPy itself or
<li>The package has a GPL (or similar) license which is incompatible with SciPy's BSD license or
<li>The package is meant to be included in SciPy, but development is still in progress.</li>

</ol>
</p>

"""

contribute_template = """
<h1>Contribute</h1>

<h3>Add your own package</h3>

<p>
Please refer to the <a href="http://projects.scipy.org/scikits">SciKits developer site</a>.
</p>

<p>
Note that scikits do not have to be hosted on the SciPy servers.  Any package named "scikits.xyz" on the Python Packaging Index will be included on this website automatically.
</p>

<p>
<!-- Register at PyPI or add to SVN repository -->
</p>

<!--
<h3>Join a project</h3>
<p>
Join a mailing list.
</p>

-->
"""

package_info_template = """
<a href="" style="text-decoration:none"><h1>{{ name }}</h1></a>
<i>{{ revision }}</i>
<p>
{{ shortdesc }}
</p>

<p>
{% if download_link %}
<img src="/static/images/download_32.png" width="16" border="0" /> Download:  {{ download_link }} <br />
{% endif %}
{% if homepage %}
Homepage: <a href="{{ homepage }}">{{ homepage }}</a> <br />
{% endif %}
{% if pypi_name %}
PyPI: <a href="http://pypi.python.org/pypi/{{ pypi_name }}">http://pypi.python.org/pypi/{{ pypi_name }}</a> <br />
{% endif %}
{% if repo_url %}
Source Repository: <a href="{{ repo_url }}">{{ repo_url }}</a> <br />
{% endif %}
{% if people %}
People: {{ people }} <br />
{% endif %}
</p>

{% if escaped_description %}
<h3>Description</h3>
<div style="background-color:#f0f0f0; padding:5px" class="rounded">
{{ escaped_description }}
</div>
{% endif %}

<h3>Installation</h3>

{% if pypi_name %}
<h4>PyPI</h4>
<p>
You can download the latest distribution from PyPI here: <a href="http://pypi.python.org/pypi/{{ name }}">http://pypi.python.org/pypi/{{ name }}</a>
</p>

<h4>Easy Install</h4>
<p>
Install the <a href="http://peak.telecommunity.com/DevCenter/EasyInstall">Easy Install</a> tools. Afterwards you can install {{ name }} from the terminal by executing:
<pre>sudo easy_install {{ pypi_name }}</pre>
</p>

<p>
If you prefer to do a local installation, specify an installation prefix:
<pre>easy_install --prefix=${HOME} {{ pypi_name }}</pre>
and ensure that your <code>PYTHONPATH</code> is up to date, e.g.:
<pre>export PYTHONPATH=$PYTHONPATH:${HOME}/lib/python2.5/site-packages</pre>
</p>
{% endif %}

{% if repo_url %}
<h4>Source code</h4>
<p>
You can get the latest sources from the repository using
<pre>svn checkout <a href="{{ repo_url }}">{{ repo_url }}</a></pre>
</p>
{% endif %}

{% if info_source %}
<p><i>This package was discovered in {{ info_source }}.</i></p>
{% endif %}

"""