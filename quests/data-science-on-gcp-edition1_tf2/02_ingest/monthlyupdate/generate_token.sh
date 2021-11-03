#!/bin/bash

openssl rand -base64 48 | tr -d /=+ | cut -c -32

