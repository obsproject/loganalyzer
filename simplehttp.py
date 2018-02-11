#!/usr/bin/env python3

from loganalyzer import *
from wsgiref.simple_server import *
import cgi

html=""
with open("template.html","r") as f:
    html=f.read()

detail=""
with open("detail.html","r") as f:
    detail=f.read()


def getSummaryHTML(messages):
    critical = ""
    warning = ""
    info = ""
    for i in messages:
        if(i[0]==3):
            critical = critical + "<li>" + i[1] + "</li>"
        elif(i[0]==2):
            warning = warning + "<li>"+ i[1] + "</li>"
        elif(i[0]==1):
            info = info + "<li>" + i[1] + "</li>"
    return critical,warning,info

def getDetailsHTML(messages):
    res=""
    for i in messages:
        if(i[0]==3):
            res = res + detail.format(sev='danger',
                    severity='Critical',
                    title=i[1],
                    text=i[2])
    for i in messages:
        if(i[0]==2):
            res = res + detail.format(sev='warning',
                    severity='Warning',
                    title=i[1],
                    text=i[2])
    for i in messages:
        if(i[0]==1):
            res= res + detail.format(sev='info',
                    severity='Info',
                    title=i[1],
                    text=i[2])

    return res


def application(environ, start_response):
    response_body=html
    if(environ['REQUEST_METHOD'] == 'POST'):
        post_env = environ.copy()
        post_env['QUERY_STRING'] = ''
        post = cgi.FieldStorage(fp=environ['wsgi.input'],environ=post_env,
            keep_blank_values=True)
        post['url'].value
        msgs=[]
        msgs = doAnalysis(post['url'].value)
        crit,warn,info = getSummaryHTML(msgs)
        details = getDetailsHTML(msgs)
        response_body = html.format(url_input=post['url'].value,
                summary_critical=crit,
                summary_warning=warn,
                summary_info=info,
                details=details)
    else:
        response_body = html.format(url_input="Paste log url here",
                summary_critical="Please analyse log",
                summary_warning="<li>none</li>",
                summary_info="<li>none</li>",
                details="""<p class="text-warning">Please analyze log first.</p>""")


    status = '200 OK'
    response_headers = [
        ('Content-Type', 'text/html'),
        ('Content-Length', str(len(response_body)))
    ]

    start_response(status, response_headers)
    return [response_body.encode()]


if __name__ == '__main__':
    try:
        from wsgiref.simple_server import make_server
        httpd = make_server('', 8080, application)
        print('Serving on port 8080...')
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('Goodbye.')

