test:
	/bin/bash -c 'gfind . -type d -name "run-*" -print0 | gxargs -r0n1 rm -fr; exit 0'
	/bin/bash -c 'cd .. && bash DOCKER_BUILD.sh'
	${HOME}/bin/opendcx -v
