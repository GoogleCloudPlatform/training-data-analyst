# Dockerfile required to generate a DataFlow flex template

FROM gcr.io/dataflow-templates-base/java11-template-launcher-base:latest

# Define the Java command options required by Dataflow Flex Templates.
ENV FLEX_TEMPLATE_JAVA_MAIN_CLASS="com.mypackage.pipeline.MyPipeline"
ENV FLEX_TEMPLATE_JAVA_CLASSPATH="/template/pipeline.jar"

# Make sure to package as a "fat JAR", including all dependencies.
COPY target/advanced-dataflow-lab-2-solution-1.0.jar ${FLEX_TEMPLATE_JAVA_CLASSPATH}
