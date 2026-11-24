#!/bin/bash
# NOT A SUPERVISOR: hands the command straight to the shell, so nothing bounds it. Used once, to show what the
# driver does when its turn leaves processes behind.
exec /bin/bash -c "$1"
