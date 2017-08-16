#!/bin/bash
set -ue

WORK_DIR="$(dirname "$(readlink -f "${0}")")/"
isPep8="0"
isUTest="0"

for opt in "${@}"; do
    case "${opt}" in
        "--pep8"|"-p" )
            isPep8="1"
            ;;
        "--unittest"|"-u" )
            isUTest="1"
            ;;
        "--all"|"-a" )
            isPep8="1"
            isUTest="1"
            ;;
        * )
            printf "[ERR] unknown option: %s\n" "${opt}" >&2
            ;;
    esac
done

if test "$((isPep8 + isUTest))" -eq "0"; then
    printf "Usage: %s [-p|--pep8] [-u|--unittest]\n" "${0}"
fi

if test "${isPep8}" -eq "1"; then
    find "${WORK_DIR}" -name "*.py" -type f -print0 | xargs -0 pep8 -v --show-source || :
fi

if test "${isUTest}" -eq "1"; then
    cd "${WORK_DIR}"
    /usr/bin/env python3 -m unittest tests/test.py || :
fi
