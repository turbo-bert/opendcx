# OpenDCX

I had the idea for this a long time ago. To make it "pretty" enough, there's never enough time. So I made this my hobby...

OpenDCX basically gives an easy interface to selenium web testing for "non-programmers", it reads its directives from text/json defined commands and comes with some handy tools on the way to automation. It may not be perfect - but it makes things easier.

# Quickstart

Let's just open google.com and that's it.

You already should have installed+running Docker.

Kickstart a selenium firefox instance into background by running...

    docker run --rm -d --name firefox --shm-size 2g -p 7900:7900 -p 4444:4444 $OPTS selenium/standalone-firefox:latest

Create an empty directory and put a file `playbook.js` right there with:

    [["", "get", "https://www.google.de"]]

`CHDIR` into that folder and run

    # for mac
    docker run --rm -v `pwd`:/work -it turbobert/opendcx
    
    # for linux
    docker run --add-host=host.docker.internal:host-gateway --rm -v `pwd`:/work -it turbobert/opendcx

If you're running Apple silicon the initial connection to the grid node will take at least 10 seconds, due to selenium being only available for linux/amd64.

Take a look at the `run-XXXXX...` folder that has emerged to see your test results.

# Reference

## Docker Runtime Parameters

    OPENDCX_SELENIUM_HOST
    OPENDCX_SELENIUM_PORT
    OPENDCX_VERBOSE

## OpenDCX Dialect

    get
    relget
    storget

# Installation/Download

# Support

# License

# Known Issues

## Selenium on Apple Silicon

Sadly `Selenium` doesn't provide `arm64` images for `grid` yet.
