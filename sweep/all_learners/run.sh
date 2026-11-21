#!/bin/sh
# Uso (desde la raíz del proyecto): sh barrido/run.sh prueba|congela|corre|evalua   ·   BARRIDO_SCRIPT=audit_barrido1.py sh barrido/run.sh
exec docker run --rm --network none -u "$(id -u):$(id -g)" -e HOME=/tmp -v "$(pwd)":/w -w /w pfuera:env python barrido/${BARRIDO_SCRIPT:-barrido1.py} "$@"
