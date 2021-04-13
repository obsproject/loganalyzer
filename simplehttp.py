#!/usr/bin/env python3

from loganalyzer import *
from wsgiref.simple_server import *
import cgi
import html
import argparse

htmlTemplate = ""
with open("template.html", "r") as f:
    htmlTemplate = f.read()

htmlDetail = ""
with open("detail.html", "r") as f:
    htmlDetail = f.read()


def getSummaryHTML(messages):
    critical = ""
    warning = ""
    info = ""
    for i in messages:
        if(i[0] == 3):
            critical = critical + """<p><a href="#""" + \
                i[1] + """"><button type="button" class="btn btn-danger">""" + \
                i[1] + "</button></a></p>\n"
        elif(i[0] == 2):
            warning = warning + """<p><a href="#""" + \
                i[1] + """"><button type="button" class="btn btn-warning">""" + \
                i[1] + "</button></a></p>\n"
        elif(i[0] == 1):
            info = info + """<p><a href="#""" + \
                i[1] + """"><button type="button" class="btn btn-info">""" + \
                i[1] + "</button></a></p>\n"
    if(len(critical) == 0):
        critical = "No critical issues."
    if(len(warning) == 0):
        warning = "No warnings."
    if(len(info) == 0):
        info = "-"
    return critical, warning, info


def genBotResponse(url, detailed):
    msgs = []
    msgs = doAnalysis(url=url)
    critical = []
    warning = []
    info = []
    for i in msgs:
        entry = i[1]
        if(detailed and detailed.lower() == 'true'):
          entry = {"title": i[1], "details": i[2]}
        if(i[0] == 3):
            critical.append(entry)
        elif(i[0] == 2):
            warning.append(entry)
        elif(i[0] == 1):
            info.append(entry)

    return json.dumps({"critical": critical, "warning": warning, "info": info})


def getDetailsHTML(messages):
    res = ""
    for i in messages:
        if(i[0] == 3):
            res = res + htmlDetail.format(anchor=i[1],
                                          sev='danger',
                                          severity='Critical',
                                          title=i[1],
                                          text=i[2])
    for i in messages:
        if(i[0] == 2):
            res = res + htmlDetail.format(anchor=i[1],
                                          sev='warning',
                                          severity='Warning',
                                          title=i[1],
                                          text=i[2])
    for i in messages:
        if(i[0] == 1):
            res = res + htmlDetail.format(anchor=i[1],
                                          sev='info',
                                          severity='Info',
                                          title=i[1],
                                          text=i[2])

    return res


def getDescr(messages):
    res = ""
    for i in messages:
        if(i[0] == 0):
            res = i[2]
    return res


no_log = "Please analyze a log first."


def genEmptyResponse():
    response_body = htmlTemplate.format(ph="",
                                        description="no log",
                                        summary_critical=no_log,
                                        summary_warning=no_log,
                                        summary_info=no_log,
                                        details="""<p class="text-warning">""" + no_log + """</p>""")
    return response_body


def genFullResponse(url):
    msgs = []
    msgs = doAnalysis(url=url)
    crit, warn, info = getSummaryHTML(msgs)
    details = getDetailsHTML(msgs)
    response = htmlTemplate.format(ph=url,
                                   description="""<a href="{}">{}</a>""".format(
                                       url, getDescr(msgs)),
                                   summary_critical=crit,
                                   summary_warning=warn,
                                   summary_info=info,
                                   details=details)
    return response

# If you modify this regex, modify it in loganalyzer.py doAnalysis() too
def checkUrl(url):
    validity = False
    matchGist = re.match(
        r"(?i)\b((?:https?:(?:/{1,3}gist\.github\.com)/)(anonymous/)?([a-z0-9]{32}))", url)
    matchHaste = re.match(
        r"(?i)\b((?:https?:(?:/{1,3}(www\.)?hastebin\.com)/)([a-z0-9]{10}))", url)
    matchObs = re.match(
        r"(?i)\b((?:https?:(?:/{1,3}(www\.)?obsproject\.com)/logs/)(.{16}))", url)
    matchPastebin = re.match(
        r"(?i)\b((?:https?:(?:/{1,3}(www\.)?pastebin\.com/))(.{8}))", url)
    matchDiscord = re.match(
        r"(?i)\b((?:https?:(?:/{1,3}cdn\.discordapp\.com)/)(attachments/)([0-9]{18}/[0-9]{18}/([0-9\-\_]{19}|message).txt))", url)
    return any((matchGist, matchHaste, matchObs, matchPastebin, matchDiscord))


def application(environ, start_response):
    response_body = ""
    form = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ)
    if (('format' in form) and ('url' in form)):
        if('detailed' in form):
          detailed = html.escape(form['detailed'].value)
        else:
          detailed = False
        url = html.escape(form['url'].value)
        output_format = html.escape(form['format'].value)
        if((checkUrl(url)) and (output_format == 'json')):
            response_body = genBotResponse(url, detailed)
            response_headers = [
                ('Content-Type', 'application/json'),
                ('Content-Length', str(len(response_body)))
            ]
    elif 'url' in form:
        url = html.escape(form['url'].value)
        if(checkUrl(url)):
            response_body = genFullResponse(url)
        else:
            response_body = genEmptyResponse()
        response_headers = [
            ('Content-Type', 'text/html'),
            ('Content-Length', str(len(response_body)))
        ]
    else:
        response_body = genEmptyResponse()
        response_headers = [
            ('Content-Type', 'text/html'),
            ('Content-Length', str(len(response_body)))
        ]

    status = '200 OK'

    start_response(status, response_headers)
    return [response_body.encode()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", dest='host',
                        default="localhost", help="address to bind to")
    parser.add_argument("--port", dest='port',
                        default="8080", help="port to bind to")
    flags = parser.parse_args()
    try:
        from wsgiref.simple_server import make_server
        httpd = make_server(flags.host, int(flags.port), application)
        print("""Serving on "{}" with port "{}" """.format(flags.host, flags.port))
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('Goodbye.')


if __name__ == "__main__":
    main()
