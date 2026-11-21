#!/bin/sh
# Uso (desde la raíz del proyecto): sh sam/run.sh prueba|congela|corre|evalua   ·   SAM_SCRIPT=audit_sam1.py sh sam/run.sh
exec docker run --rm --network none -u "$(id -u):$(id -g)" -e HOME=/tmp -v "$(pwd)":/w -w /w pfuera:env python sam/${SAM_SCRIPT:-sam1.py} "$@"
