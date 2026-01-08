#!/usr/bin/env python3

import logging
import argparse
import concurrent.futures
import asyncio
from aiohttp import web
import loganalyzer as analyze

with open("templates/index.html", "r") as f:  # Grab main HTML page
    htmlTemplate = f.read()

with open("templates/detail.html", "r") as f:  # Grab details page
    htmlDetail = f.read()


def checkUrl(url):
    """Check if the incoming URL can be analyzed"""
    return any((analyze.matchGist(url), analyze.matchHaste(url), analyze.matchObs(url), analyze.matchPastebin(url), analyze.matchDiscord(url)))


def getSummaryHTML(messages):
    """Helper func. Generates the summary secion of the HTML page."""
    critical = ""
    warning = ""
    info = ""
    for i in messages:
        if (i[0] == 3):
            critical = critical + """<p><a href="#""" + \
                i[1] + """"><button type="button" class="btn btn-danger">""" + \
                i[1] + "</button></a></p>\n"
        elif (i[0] == 2):
            warning = warning + """<p><a href="#""" + \
                i[1] + """"><button type="button" class="btn btn-warning">""" + \
                i[1] + "</button></a></p>\n"
        elif (i[0] == 1):
            info = info + """<p><a href="#""" + \
                i[1] + """"><button type="button" class="btn btn-info">""" + \
                i[1] + "</button></a></p>\n"
    if (len(critical) == 0):
        critical = "No critical issues."
    if (len(warning) == 0):
        warning = "No warnings."
    if (len(info) == 0):
        info = "-"
    return critical, warning, info


def getDetailsHTML(messages):
    """Helper func. Generates detailes section of the HTML page."""
    res = ""
    for i in messages:
        if (i[0] == 3):
            res = res + htmlDetail.format(anchor=i[1],
                                          sev='danger',
                                          severity='Critical',
                                          title=i[1],
                                          text=i[2])
    for i in messages:
        if (i[0] == 2):
            res = res + htmlDetail.format(anchor=i[1],
                                          sev='warning',
                                          severity='Warning',
                                          title=i[1],
                                          text=i[2])
    for i in messages:
        if (i[0] == 1):
            res = res + htmlDetail.format(anchor=i[1],
                                          sev='info',
                                          severity='Info',
                                          title=i[1],
                                          text=i[2])
    return res


def getDescr(messages):
    """Helper func. Gets the desciption created by the analysis."""
    res = ""
    for i in messages:
        if (i[0] == 0):
            res = i[2]
    return res


def genFullHtmlResponse(url):
    """Runs an analysis and returns a full HTML page with the response."""
    msgs = analyze.doAnalysis(url=url)
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


def genEmptyHtmlResponse():
    """Generates a full HTML page with no analysis."""
    no_log = "Please analyze a log first."
    response_body = htmlTemplate.format(ph="",
                                        description="no log",
                                        summary_critical=no_log,
                                        summary_warning=no_log,
                                        summary_info=no_log,
                                        details="""<p class="text-warning">""" + no_log + """</p>""")
    return response_body


def genJsonResponse(url, detailed):
    """Runs an analysis and returns the results as JSON."""
    msgs = []
    msgs = analyze.doAnalysis(url=url)
    critical = []
    warning = []
    info = []
    for i in msgs:
        entry = i[1]
        if detailed:
            entry = {"title": i[1], "details": i[2]}
        if (i[0] == 3):
            critical.append(entry)
        elif (i[0] == 2):
            warning.append(entry)
        elif (i[0] == 1):
            info.append(entry)
    return {"critical": critical, "warning": warning, "info": info}


def sync_request_handler(request):
    """Non-async request handler processed within the thread pool. Do not share global resources without a Lock."""
    query = request.query  # Get HTTP query string as a MultiDict
    format = 'html'
    if 'format' in query:  # Check for requested response format
        format = query['format'].lower()

    logging.info('New HTTP Request | Remote: {} | Format: {} | Url: {}'.format(request.remote, format, 'url' in query))

    if 'url' in query:
        url = query['url']
        detailed = 'detailed' in query and query['detailed'] == 'true'
        if not checkUrl(url):  # Return empty data/page if URL is invalid
            logging.info('Invalid URL: {}'.format(url))
            if format == 'json':
                logging.info('Returning empty JSON response.')
                return web.json_response({})
            else:
                logging.info('Returning default HTML response.')
                return web.Response(text=genEmptyHtmlResponse(), content_type='text/html')
        if format == 'json':
            logging.info('Returning JSON response for url: {}'.format(url))
            response = genJsonResponse(url, detailed)
            return web.json_response(response)
        else:
            logging.info('Returning HTML response for url: {}'.format(url))
            return web.Response(text=genFullHtmlResponse(url), content_type='text/html')
    else:
        if format == 'json':
            logging.info('Returning empty JSON response.')
            return web.json_response({})
        else:
            logging.info('Returning default HTML response.')
            return web.Response(text=genEmptyHtmlResponse(), content_type='text/html')


async def request_handler(request):
    """Async request handler. Submits the incoming request to the thread pool to be handled."""
    return await asyncio.to_thread(sync_request_handler, request)  # Submits the request to a handler inside the threadpool


async def on_startup(app):
    threadPool = concurrent.futures.ThreadPoolExecutor(thread_name_prefix='loganalyzer: worker thread')
    loop = asyncio.get_running_loop()
    loop.set_default_executor(threadPool)  # Set the default executor to our thread pool


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [%(funcName)s] %(message)s")
    aiohttpLogger = logging.getLogger('aiohttp')
    aiohttpLogger.setLevel(logging.WARNING)

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost", type=str, help="address to bind to", dest='host')
    parser.add_argument("--port", default="8080", type=int, help="port to bind to", dest='port')
    flags = parser.parse_args()

    app = web.Application()
    app.on_startup.append(on_startup)
    app.router.add_get('/', request_handler)
    web.run_app(app, host=flags.host, port=flags.port)


if __name__ == '__main__':
    main()
