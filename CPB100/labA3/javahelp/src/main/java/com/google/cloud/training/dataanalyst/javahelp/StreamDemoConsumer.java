/*
 * Copyright (C) 2016 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not
 * use this file except in compliance with the License. You may obtain a copy of
 * the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations under
 * the License.
 */

package com.google.cloud.training.dataanalyst.javahelp;

import org.joda.time.Duration;

import com.google.cloud.dataflow.sdk.Pipeline;
import com.google.cloud.dataflow.sdk.io.PubsubIO;
import com.google.cloud.dataflow.sdk.io.TextIO;
import com.google.cloud.dataflow.sdk.options.DataflowPipelineOptions;
import com.google.cloud.dataflow.sdk.options.Default;
import com.google.cloud.dataflow.sdk.options.Description;
import com.google.cloud.dataflow.sdk.options.PipelineOptions;
import com.google.cloud.dataflow.sdk.options.PipelineOptionsFactory;
import com.google.cloud.dataflow.sdk.runners.DataflowPipelineRunner;
import com.google.cloud.dataflow.sdk.transforms.DoFn;
import com.google.cloud.dataflow.sdk.transforms.Mean;
import com.google.cloud.dataflow.sdk.transforms.ParDo;
import com.google.cloud.dataflow.sdk.transforms.Sum;
import com.google.cloud.dataflow.sdk.transforms.windowing.SlidingWindows;
import com.google.cloud.dataflow.sdk.transforms.windowing.Window;
import com.google.cloud.dataflow.sdk.values.PCollection;

/**
 * A dataflow pipeline that listens to a PubSub topic
 * and writes out aggregates on windows
 * 
 * @author vlakshmanan
 *
 */
public class StreamDemoConsumer {

	public static interface MyOptions extends DataflowPipelineOptions {
		@Description("Output topic")
		@Default.String("projects/cloud-training-demos/topics/streamdemo2")
		String getOutput();

		void setOutput(String s);
		
		@Description("Input topic")
		@Default.String("projects/cloud-training-demos/topics/streamdemo")
		String getInput();

		void setInput(String s);
	}
	
	@SuppressWarnings("serial")
	public static void main(String[] args) {
		MyOptions options = PipelineOptionsFactory.fromArgs(args).withValidation().as(MyOptions.class);
		options.setRunner(DataflowPipelineRunner.class);
		options.setStreaming(true);
		
		Pipeline p = Pipeline.create(options);

		String topic = options.getInput();
		String output = options.getOutput();
		
		p //
				.apply("GetMessages", PubsubIO.Read.topic(topic)) //
				.apply("window", Window.into(SlidingWindows//
						.of(Duration.standardMinutes(2))//
						.every(Duration.standardSeconds(30)))) //
				.apply("LineLength", ParDo.of(new DoFn<String, Integer>() {
					@Override
					public void processElement(ProcessContext c) throws Exception {
						String line = c.element();
						c.output(line.length());
					}
				}))//
				.apply(Sum.integersGlobally().withoutDefaults()) //
				.apply("ToString", ParDo.of(new DoFn<Integer, String>() {

					@Override
					public void processElement(ProcessContext c) throws Exception {
						c.output(c.element().toString());
					}

				})) //
				.apply(PubsubIO.Write.topic(output));

		p.run();
	}
}
