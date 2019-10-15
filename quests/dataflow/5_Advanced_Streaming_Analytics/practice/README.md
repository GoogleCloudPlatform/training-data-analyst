# Advanced Dataflow Quest Lab 4

## Pipeline

[StreamingMinuteTrafficPipeline](src/main/java/com/google/cloud/pso/pipeline/StreamingMinuteTrafficPipeline.java) -
A pipeline that ingests JSON messages from Pubsub, parses them, writes the successfully-parsed messages to BigQuery and the remainder to Cloud Storage.

## Getting Started

### Requirements

* Java 8
* Maven 3

### Building the Project

Build the entire project using the maven compile command.
```sh
mvn clean && mvn compile
```
