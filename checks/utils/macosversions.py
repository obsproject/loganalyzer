import datetime
import re


macver_re = re.compile(r"""
    (?i)
    OS\sVersion:\sVersion\s
    (?P<major>[0-9]+)
    \.
    (?P<minor>[0-9]+)
    """, re.VERBOSE)


macversions = {
    "13": {
        "name": "Ventura",
        "date": datetime.date(2022, 10, 24),
        "latest": True
    },
    "12": {
        "name": "Monterey",
        "date": datetime.date(2021, 10, 25),
        "latest": True
    },
    "11": {
        "name": "Big Sur",
        "date": datetime.date(2020, 11, 12),
        "latest": True
    },
    # Old versions of OBS read Big Sur as 10.16, so document it too
    "10.16": {
        "name": "Big Sur",
        "date": datetime.date(2020, 11, 12),
        "latest": True
    },
    "10.15": {
        "name": "Catalina",
        "date": datetime.date(2019, 10, 7),
        "max": "29.0"
    },
    "10.14": {
        "name": "Mojave",
        "date": datetime.date(2018, 9, 24),
        "max": "27.2"
    },
    "10.13": {
        "name": "High Sierra",
        "date": datetime.date(2017, 9, 25),
        "max": "27.2"
    },
    "10.12": {
        "name": "Sierra",
        "date": datetime.date(2016, 9, 20),
        "max": "24.0"
    }
}
