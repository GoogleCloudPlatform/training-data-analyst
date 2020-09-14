# Advanced Dataflow Quest Lab 4

## Pipeline

[StreamingMinuteTrafficPipeline](src/main/java/com/google/cloud/pso/pipeline/StreamingMinuteTrafficPipeline.java) -
A pipeline that ingests JSON messages from Pubsub, parses them, writes the raw messages to BigQuery, and then windows and aggregates to compute real-time traffic volume.

## Getting Started

### Requirements

* Java 8
* Maven 3

### Building the Project

Build the entire project using the maven compile command.
```sh
mvn clean && mvn compile
```
