#!/usr/bin/bash
pybabel extract -F babel.cfg -k msgid -o messages.pot .
pybabel update -i messages.pot -d web/translations
pybabel compile -d web/translations