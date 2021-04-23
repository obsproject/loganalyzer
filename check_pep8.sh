#!/bin/sh
set -e

# ignore long lines (prefer result text in sinle line)
pycodestyle --ignore=E501,E722 .
