#!/bin/sh
# uso: sh soknl/run.sh <tests|freeze|corre|evalua>   (SOKNL_SCRIPT=audit_soknl1.py para la auditoría)
cd "$(dirname "$0")/.." || exit 1
docker run --rm --network none -m 12g -u "$(id -u):$(id -g)" -e SOKNL_PROCS -e PYTHONDONTWRITEBYTECODE=1 -e HOME=/tmp -v "$PWD":/w -w /w pfuera:env python3 -W ignore soknl/"${SOKNL_SCRIPT:-soknl1.py}" "$@"
