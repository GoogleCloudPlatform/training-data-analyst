#!/bin/bash
gcloud sql instances patch flights \
	--authorized-networks $(wget -qO - http://ipecho.net/plain)/32
