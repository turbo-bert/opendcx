#!/bin/bash


docker buildx build --platform linux/arm64,linux/amd64 --no-cache -t `cat DTAG` .
