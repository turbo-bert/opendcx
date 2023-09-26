test:
	make clean
	make build
	${HOME}/bin/opendcx -v

tnb:
	${HOME}/bin/opendcx -v

build:
	/bin/bash -c 'cd .. && bash DOCKER_BUILD.sh'

clean:
	/bin/bash -c 'gfind . -type d -name "run-*" -print0 | gxargs -r0n1 rm -fr; exit 0'
