## -*- coding: utf-8 -*-
<%inherit file="/base.mako"/>

<%block name="title_text">Performance job results</%block>

<%block name="css">
    li { margin:2px 0 }
    a, a:visited { color:#039 }
    code { padding:0 5px; color:#888 }
    .columns li { position:relative }
    .columns li > :first-child { display:block }
    .columns li > :nth-child(2) { display:block; position:static; left:165px; top:0; white-space:nowrap }
</%block>

<%block name="css_content_wrap">margin:0 auto; padding:0 5px</%block>

<%block name="media_queries">
    @media only screen and (min-width: 320px) { .content-wrap { width:400px } }
    @media only screen and (min-width: 520px) { .content-wrap { width:500px } }
    @media only screen and (min-width: 620px) { .content-wrap { width:90% } .columns li > :nth-child(2) { position:absolute } }
    @media only screen and (min-width: 720px) { .content-wrap { width:70% } }
</%block>

<%block name="header_text">performance job results</%block>

<%block name="content">
    <h2>Logs and files</h2>
    <ul class="columns">
      <li><a href="console.html" class="rich">Benchmarking logs</a> <code>console.html</code>
      <li><a href="logs/">Logs of all services</a> <code>logs/</code>
      <li><a href="rally-plot/">Rally files</a> <code>rally-plot/</code>
    </ul>

    <h2>Job results, in different formats</h2>
    <ul class="columns">
      <li><a href="rally-plot/results.html.gz" class="rich">HTML report</a> <code>$ rally task report</code>
      <li><a href="rally-plot/detailed.txt.gz">Text report</a> <code>$ rally task detailed</code>
      <li><a href="rally-plot/detailed_with_iterations.txt.gz">Text report detailed</a> <code>$ rally task detailed --iterations-data</code>
      <li><a href="rally-plot/sla.txt">Success criteria (SLA)</a> <code>$ rally task sla_check</code>
      <li><a href="rally-plot/results.json.gz">Raw results (JSON)</a> <code>$ rally task results</code>
    </ul>

    <h2>About Rally</h2>
    <p>Rally is benchmark system for OpenStack:</p>
    <ul>
      <li><a href="https://github.com/openstack/rally">Git repository</a>
      <li><a href="https://rally.readthedocs.org/en/latest/">Documentation</a>
      <li><a href="https://wiki.openstack.org/wiki/Rally/HowTo">How to use Rally (locally)</a>
      <li><a href="https://wiki.openstack.org/wiki/Rally/RallyGates">How to add Rally job to your project</a>
    </ul>

    <h2>Steps to repeat locally</h2>
    <ol>
      <li>Fetch rally task from <a href="rally-plot/task.txt">here</a></li>
      <li>Fetch rally plugins from <a href="rally-plot/plugins.tar.gz">here</a></li>
      <li>Install OpenStack and Rally using <a href="https://github.com/openstack/rally/tree/master/contrib/devstack">this instruction</a></li>
      <li>Unzip plugins and put to <code>.rally/plugins/</code> directory</li>
      <li>Run rally task: <code>$ rally task start task.txt</code></li>
    </ol>
</%block>
