#!/bin/bash
set -ue


WORK_DIR="$(dirname "$(readlink -f "${0}")")/"
isPep8="0"
isUTest="0"
isMypy="0"

cmdPep8="pep8"
cmdMypy="mypy"


for opt in "${@}"; do
    case "${opt}" in
        "--pep8"|"-p" )
            isPep8="1"
            ;;
        "--unittest"|"-u" )
            isUTest="1"
            ;;
        "--mypy"|"-m" )
            isMypy="1"
            ;;
        "--all"|"-a" )
            isPep8="1"
            isUTest="1"
            isMypy="1"
            ;;
        * )
            printf "[ERR] unknown option: %s\n" "${opt}" >&2
            ;;
    esac
done


if test "$((isPep8 + isUTest + isMypy))" -eq "0"; then
    printf "Usage: %s [-p|--pep8] [-u|--unittest] [-m|--mypy]\n" "${0}"
fi


if test "${isPep8}" -eq "1"; then
    if command -v "${cmdPep8}" >/dev/null 2>&1; then
        find "${WORK_DIR}" -name "*.py" -type f -print0 | xargs -0 pep8 -v --show-source || :
    else
        printf "[ERR] not installed: %s\n" "${cmdPep8}"
    fi
fi


if test "${isUTest}" -eq "1"; then
    cd "${WORK_DIR}"
    /usr/bin/env python3 -m unittest tests/test.py || :
fi


if test "${isMypy}" -eq "1"; then
    if command -v "${cmdMypy}" >/dev/null 2>&1; then
        cd "${WORK_DIR}"
        mypy ncv-py.py || :
    else
        printf "[ERR] not installed: %s\n" "${cmdMypy}"
    fi
fi
