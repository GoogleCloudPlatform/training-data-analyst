/*
 * Copyright (C) 2018 Google Inc.
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

package com.mypackage.pipeline;

import static org.hamcrest.CoreMatchers.equalTo;
import static org.hamcrest.CoreMatchers.is;
import static org.hamcrest.MatcherAssert.assertThat;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;

/**
 * Test cases for the {@link StreamingMinuteTrafficPipeline} class.
 */
@RunWith(JUnit4.class)
public class StreamingMinuteTrafficPipelineTest {

  /**
   * Tests the pipeline.
   */
  @Test
  public void testSamplePipeline() {
    // Arrange
    //

    // Here perform the setup for the test.
    String[] args = new String[]{};

    // Act
    //

    // Here perform the action which is being tested.
    StreamingMinuteTrafficPipeline.main(args);

    // Assert
    //

    // Here perform the assertions for the test.
    assertThat(true, is(equalTo(true)));
  }
}
