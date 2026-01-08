from collections import namedtuple
import re


class ObsVersion():
    """ Bespoke OBS version parser
    Follows the semver 2.0.0 spec at https://semver.org/

    Pre-release versioning is stricter than the full semver spec
    and MUST have the following formatting : `<type><patch>`
    with `<type>` being one of `alpha`, `beta`, or `rc`
    and `<patch>` (optional) being any number of digits, optionally preceded by a dot
    """
    _nan = float('nan')
    _regex = re.compile(r"(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)(-(?P<beta_type>alpha|beta|rc)\.?(?P<beta_patch>\d*))?(-(?P<modified>modified))?((-|\+)(?P<trail>[0-9A-Za-z-]+))?")
    _VersionNum = namedtuple('VersionNum', 'major, minor, patch, beta_type, beta_patch')
    _beta_types = {"alpha": 0,
                   "beta": 1,
                   "rc": 2,
                   None: 3}

    def __init__(self, version_string):
        self.string = str(version_string)
        self.parsed = False
        self.version = self._VersionNum(self._nan, self._nan, self._nan, 3, 0)
        # NaN for false comparisons
        self.modified = None
        self.trail = None
        self.beta = False

        try:
            match = self._regex.fullmatch(version_string)
            if match:
                self.version = self._VersionNum(int(match.group('major')),
                                                int(match.group('minor')),
                                                int(match.group('patch')),
                                                self._beta_types[match.group('beta_type')],
                                                int(match.group('beta_patch')) if match.group('beta_patch') else 0
                                                )
                self.modified = match.group('modified')
                self.trail = match.group('trail')
                self.beta = self.version.beta_type != self._beta_types[None]
                self.parsed = True

        except TypeError:
            return

    def __str__(self):
        return self.string

    def __repr__(self):
        return f"OBS version {self.string}{'' if self.parsed else ' (unparseable)'}"

    def __eq__(self, other):
        try:
            return self.version == other.version
        except AttributeError:
            return self == ObsVersion(other)

    def __lt__(self, other):
        try:
            return self.version < other.version
        except AttributeError:
            return self < ObsVersion(other)

    def __le__(self, other):
        try:
            return self.version <= other.version
        except AttributeError:
            return self <= ObsVersion(other)

    def __gt__(self, other):
        try:
            return self.version > other.version
        except AttributeError:
            return self > ObsVersion(other)

    def __ge__(self, other):
        try:
            return self.version >= other.version
        except AttributeError:
            return self >= ObsVersion(other)
