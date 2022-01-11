import sbt._
import Keys._

val scioVersion = "0.10.2"
val beamVersion = "2.28.0"

val dependencies = Seq(
  "com.spotify" %% "scio-core" % scioVersion,
  "com.spotify" %% "scio-google-cloud-platform" % scioVersion,
  "org.apache.beam" % "beam-runners-direct-java" % beamVersion,
  "org.apache.beam" % "beam-runners-google-cloud-dataflow-java" % beamVersion,
  "org.slf4j" % "slf4j-simple" % "1.7.30"
)

lazy val root: Project = project
  .in(file("."))
  .settings(
    name := "BasicETL-Lab",
    description := "Lab Tutorials",
    version := "0.1.0-SNAPSHOT",
    scalaVersion := "2.12.12",
    scalacOptions ++= Seq("-target:jvm-1.8",
      "-deprecation",
      "-feature",
      "-unchecked",
      "-language:higherKinds"),
    libraryDependencies ++=  dependencies
  ).enablePlugins(PackPlugin)