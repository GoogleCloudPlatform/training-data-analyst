~/apache-maven*/bin/mvn archetype:generate \
      -DarchetypeGroupId=org.apache.beam \
      -DarchetypeArtifactId=beam-sdks-java-maven-archetypes-starter \
      -DarchetypeVersion=2.16.0 \
      -DgroupId=com.google.cloud.training.dataflowsql \
      -DartifactId=bq_in_df2 \
      -Dversion="1.1" \
      -DinteractiveMode=false
