#!/bin/bash
autopep8 --in-place -r .

./check_pep8.sh
if [ $? != 0 ]
then
    echo "Code couldn't be formatted correctly. Try fixing the issue(s) above yourself."
    exit 1
fi
