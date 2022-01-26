import datetime
import re


winver_re = re.compile(r"""
    (?i)
    Windows\sVersion: \s+ (?P<version>[0-9.]+)
    \s+
    Build \s+ (?P<build>\d+)
    \s+
    \(
        (release: \s+ (?P<release>\d|\w+); \s+)?
        revision: \s+ (?P<revision>\d+);
        \s+
        (?P<arm>ARM)?\s?(?P<bits>\d+)-bit
    \)
    """, re.VERBOSE)


# Ref: https://docs.microsoft.com/en-us/lifecycle/products/windows-11-home-and-pro-version-21h2
win11versions = {
    22000: {
        "release": 2009,
        "name": "Windows 11 21H2",
        "date": datetime.date(2021, 10, 4),
        "EoS": datetime.date(2023, 10, 10),
    },
    # Note: 22622 is 22H2 but with additional features coming 2023
    22621: {
        "release": 2009,
        "name": "Windows 11 22H2",
        "date": datetime.date(2022, 9, 20),
        "EoS": datetime.date(2024, 10, 14),
    }
}


# I guess I'll call the Win10 sub-versions "releases", even though Microsoft
# calls them "versions" because Win10 is also "Version 10.0".
#
# We probably don't need all the info here, but it comes in handy
#
# Ref: https://docs.microsoft.com/en-us/lifecycle/products/windows-10-home-and-pro
win10versions = {
    10240: {
        "release": 1507,
        "name": "Windows 10 1507",
        "date": datetime.date(2015, 7, 29),
        "EoS": datetime.date(2017, 5, 9),
    },
    10586: {
        "release": 1511,
        "name": "Windows 10 1511",
        "date": datetime.date(2015, 11, 10),
        "EoS": datetime.date(2017, 10, 10),
    },
    14393: {
        "release": 1607,
        "name": "Windows 10 1607",
        "date": datetime.date(2016, 8, 2),
        "EoS": datetime.date(2018, 4, 10),
    },
    15063: {
        "release": 1703,
        "name": "Windows 10 1703",
        "date": datetime.date(2017, 4, 5),
        "EoS": datetime.date(2018, 10, 9),
    },
    16299: {
        "release": 1709,
        "name": "Windows 10 1709",
        "date": datetime.date(2017, 10, 17),
        "EoS": datetime.date(2019, 4, 9),
    },
    17134: {
        "release": 1803,
        "name": "Windows 10 1803",
        "date": datetime.date(2018, 4, 30),
        "EoS": datetime.date(2019, 11, 12),
    },
    17763: {
        "release": 1809,
        "name": "Windows 10 1809",
        "date": datetime.date(2018, 11, 13),
        "EoS": datetime.date(2020, 11, 10),
    },
    18362: {
        "release": 1903,
        "name": "Windows 10 1903",
        "date": datetime.date(2019, 5, 21),
        "EoS": datetime.date(2020, 12, 8),
    },
    18363: {
        "release": 1909,
        "name": "Windows 10 1909",
        "date": datetime.date(2019, 11, 12),
        "EoS": datetime.date(2021, 5, 11),
    },
    19041: {
        "release": 2004,
        "name": "Windows 10 2004",
        "date": datetime.date(2020, 5, 27),
        "EoS": datetime.date(2021, 12, 14),
    },
    19042: {
        "release": 2009,
        "name": "Windows 10 20H2",
        "date": datetime.date(2020, 10, 20),
        "EoS": datetime.date(2022, 5, 10),
    },
    19043: {
        "release": 2009,
        "name": "Windows 10 21H1",
        "date": datetime.date(2021, 5, 18),
        "EoS": datetime.date(2022, 12, 13),
    },
    19044: {
        "release": 2009,
        "name": "Windows 10 21H2",
        "date": datetime.date(2021, 11, 16),
        "EoS": datetime.date(2023, 6, 13),
    },
    19045: {
        "release": 2009,
        "name": "Windows 10 22H2",
        "date": datetime.date(2022, 10, 17),
        "EoS": datetime.date(2024, 5, 14),
    },
    **win11versions
}


winversions = {
    "6.1": {
        "name": "Windows 7",
        "date": datetime.date(2012, 10, 26),
        "EoS": datetime.date(2020, 1, 14),
    },
    "6.2": {
        "name": "Windows 8",
        "date": datetime.date(2013, 10, 17),
        "EoS": datetime.date(2016, 1, 12),
    },
    "6.3": {
        "name": "Windows 8.1",
        "date": datetime.date(2013, 10, 17),
        "EoS": datetime.date(2023, 1, 10),
    },
}
