#!/bin/sh
set -e

# ignore long lines (prefer tesult text in sinle line)
pycodestyle --ignore=E501 .
