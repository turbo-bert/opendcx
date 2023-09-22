#!/bin/bash


# traverse source for usage of os.gentenv for OPENDCX_ variables to collect a unique list for documentation
egrep -R "os.getenv" opendcx | grep OPENDCX_ | gsed -E 's/^.*os.getenv\(//g' | tr '"' "'" | cut -d "'" -f 2 | sort | uniq >list_of_env.txt
