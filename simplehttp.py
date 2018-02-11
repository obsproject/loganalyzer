#!/usr/bin/env python3

from loganalyzer import *
from wsgiref.simple_server import *
import cgi

html = """
<html>
<body>
    <form method="post" action="">
    <h1>Input</h1>
    <p>
        Log URL: <input type="text" name="url" value="{url_input}">
    </p>
    <p>
        <input type="submit" value="Submit">
    </p>
    <h1>Output</h1>
    <p>
        {results_field}
    </p>

</body>
</html>
"""

def getSummaryHTML(messages):
    critical = ""
    warning = ""
    info = ""
    score = 0
    for i in messages:
        if(i[0]==3):
            critical = critical + i[1] +", "
        elif(i[0]==2):
            warning = warning + i[1] +", "
        elif(i[0]==1):
            info = info + i[1] +", "
        score = score + i[0]
    summary="""<p>Log Score {} </p>\n""".format(score)
    summary+="""<p class="text-danger">Critical:{}</p>\n""".format(critical)
    summary+="""<p class="text-warning">Warning:{}</p>\n""".format(warning)
    summary+="""<p class="text-info">Info: {}\n""".format(info)
    return summary

def application(environ, start_response):
    response_body=html
    
    if environ['REQUEST_METHOD'] == 'POST':
        post_env = environ.copy()
        post_env['QUERY_STRING'] = ''
        post = cgi.FieldStorage(fp=environ['wsgi.input'],environ=post_env,
            keep_blank_values=True)

        post['url'].value
        msgs = doAnalysis(post['url'].value)
        results = getResults(msgs)
 
        response_body = html.format(url_input=post['url'].value,results_field=results)

    status = '200 OK'
    response_headers = [
        ('Content-Type', 'text/html'),
        ('Content-Length', str(len(response_body)))
    ]

    start_response(status, response_headers)
    return [response_body.encode()]

httpd = make_server('localhost', 8051, application)
httpd.serve_forever()


