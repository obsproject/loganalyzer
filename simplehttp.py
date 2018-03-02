#!/usr/bin/env python3

from loganalyzer import *
from wsgiref.simple_server import *
import cgi
import html

htmlTemplate=""
with open("template.html","r") as f:
    htmlTemplate=f.read()

htmlDetail=""
with open("detail.html","r") as f:
    htmlDetail=f.read()


def getSummaryHTML(messages):
    critical = ""
    warning = ""
    info = ""
    for i in messages:
        if(i[0]==3):
            critical = critical + """<p><a href="#"""+ i[1] +""""><button type="button" class="btn btn-danger">""" + i[1] + "</button></a></p>\n"
        elif(i[0]==2):
            warning = warning + """<p><a href="#"""+ i[1] +""""><button type="button" class="btn btn-warning">""" + i[1] + "</button></a></p>\n"
        elif(i[0]==1):
            info = info + """<p><a href="#"""+ i[1] +""""><button type="button" class="btn btn-info">""" + i[1] + "</button></a></p>\n"
    return critical,warning,info

def getDetailsHTML(messages):
    res=""
    for i in messages:
        if(i[0]==3):
            res = res + htmlDetail.format(anchor=i[1],
                    sev='danger',
                    severity='Critical',
                    title=i[1],
                    text=i[2])
    for i in messages:
        if(i[0]==2):
            res = res + htmlDetail.format(anchor=i[1],
                    sev='warning',
                    severity='Warning',
                    title=i[1],
                    text=i[2])
    for i in messages:
        if(i[0]==1):
            res= res + htmlDetail.format(anchor=i[1],
                    sev='info',
                    severity='Info',
                    title=i[1],
                    text=i[2])

    return res

def getDescr(messages):
    res = ""
    for i in messages:
        if(i[0]==0):
            res=i[2]
    return res


def genEmptyResponse():
    response_body = htmlTemplate.format(ph="",
            description="no log",
            summary_critical="Please analyze log first.",
            summary_warning="Please analyze log first.",
            summary_info="Please analyze log first.",
            details="""<p class="text-warning">Please analyze log first.</p>""")
    return response_body

def genFullResponse(url):
    msgs=[]
    msgs = doAnalysis(url)
    crit,warn,info = getSummaryHTML(msgs)
    details = getDetailsHTML(msgs)
    response = htmlTemplate.format(ph=url,
            description="""<a href="{}">{}</a>""".format(url,getDescr(msgs)),
            summary_critical=crit,
            summary_warning=warn,
            summary_info=info,
            details=details)
    return response



def application(environ, start_response):
    response_body=""
    form = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ)
    if 'url' in form:
        url = html.escape(form['url'].value)
        matchGist = re.match(r"(?i)\b((?:https?:(?:/{1,3}gist\.github\.com)/)(anonymous/)?([a-z0-9]{32}))",url)
        matchHaste = re.match(r"(?i)\b((?:https?:(?:/{1,3}(www\.)?hastebin\.com)/)([a-z0-9]{10}))",url)
        if(matchGist != None):
            response_body = genFullResponse(url)
        elif(matchHaste != None):
            response_body = genFullResponse(url)
        else:
            response_body = genEmptyResponse()
    else:
        response_body = genEmptyResponse()


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

