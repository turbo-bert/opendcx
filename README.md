# OpenDCX

I had the idea for this a long time ago. To make it "pretty" enough, there's never enough time. So I made this in my free time. The name `DCX` derives from `daisy-chained-xpath` because when I was testing web application front ends it felt like going from xpath to xpath to xpath...

So `OpenDCX` basically gives a text interface to selenium for "non-programmers". All directives are written in JSON notation. All the logging pre and post test steps is automatically done for you and you can extend your test definition in some handy ways. It may not be perfect - but it makes things easier.

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

If you're running Apple Silicon the initial connection to the grid node will take at least 10 seconds due to selenium's images currently being only available for `linux/amd64` - emulation hits hard even on Apple Silicon.

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

# Known Issues / Restrictions

## Restriction: Firefox

Currently I focus on compatibility with `firefox`.

## Issue: Selenium on Apple Silicon

Sadly `Selenium` doesn't provide `arm64` images for `grid` yet.
