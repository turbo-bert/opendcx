#!/bin/bash


docker buildx build --load -t `cat DTAG` .
