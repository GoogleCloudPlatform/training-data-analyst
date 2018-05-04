#!/bin/bash
mvn compile exec:java -Dexec.mainClass=com.google.cloud.bigtable.training.Ex0 -Dbigtable.project=<your project id> -Dbigtable.instance=<your instance id> -Dbigtable.table=Ex0Table
