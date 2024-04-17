#!/usr/bin/env bash
CURPATH=`dirname $0`
cat > "$CURPATH/kcevent/settings_local.py" << EOF
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCALE_PATHS = [
    os.path.join(BASE_DIR, "i18n")
]
EOF

env DJANGO_SETTINGS_MODULE="kcevent.settings_local" python3 -m django makemessages --all
env DJANGO_SETTINGS_MODULE="kcevent.settings_local" python3 -m django makemessages -d djangojs --all
