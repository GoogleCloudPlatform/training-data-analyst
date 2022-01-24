/*
 * Copyright (C) 2021 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package scio.mypackage.pipeline

//TODO: Add imports

/**
 * The {@link MyPipelineOptions} class provides the custom execution options passed by the
 * executor at the command-line.
 */
trait MyPipelineOptions extends PipelineOptions {

}

//TODO: Add CommonLog Class

//TODO: Add JsonToCommonLog DoFn

object MyPipeline {

  /**
   * The logger to output status messages to.
   */
  private val LOG = LoggerFactory.getLogger(this.getClass)

  /**
   * The main entry-point for pipeline execution. This method will start the
   * pipeline but will not wait for it's execution to finish. If blocking
   * execution is required, use the {@link MyPipeline# run ( MyPipelineOptions )} method to
   * start the pipeline.
   *
   * @param args The command-line args passed by the executor.
   */
  def main(cmdlineArgs: Array[String]): Unit = {

    // Setting up the Beam pipeline options
    val pipelineOptions = PipelineOptionsFactory
      .fromArgs(cmdlineArgs: _*)
      .withValidation
      .as(classOf[MyPipelineOptions])

    // Create the pipeline
    val sc = ScioContext(pipelineOptions)

    /*
     * Steps:
     * 1) Read something
     * 2) Transform something
     * 3) Write something
     */

    // Runs the pipeline to completion with the specified options.
    sc.run()
  }
}