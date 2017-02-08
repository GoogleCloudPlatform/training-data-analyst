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

package com.google.cloud.training.dataanalyst.flights;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.google.cloud.dataflow.sdk.Pipeline;
import com.google.cloud.dataflow.sdk.io.TextIO;
import com.google.cloud.dataflow.sdk.options.PipelineOptionsFactory;
import com.google.cloud.dataflow.sdk.transforms.DoFn;
import com.google.cloud.dataflow.sdk.transforms.ParDo;

/**
 * A dataflow pipeline to create the training dataset to predict whether a
 * flight will be delayed by 15 or more minutes. The key thing that this
 * pipeline does is to add the average delays for the from & to airports at this
 * hour to the set of training features.
 * 
 * @author vlakshmanan
 *
 */
public class CreateTrainingDataset1 {
	private static final Logger LOG = LoggerFactory.getLogger(CreateTrainingDataset1.class);

	@SuppressWarnings("serial")
	public static void main(String[] args) {
		Pipeline p = Pipeline.create(PipelineOptionsFactory.fromArgs(args).withValidation().create());

		p //
				.apply(TextIO.Read.from("/Users/vlakshmanan/data/flights/small.csv")) //
				.apply(ParDo.of(new DoFn<String, String>() {

					@Override
					public void processElement(ProcessContext c) throws Exception {
						String input = c.element();
						if (input.contains("DFW")) {
							c.output(input);
						}
					}
				})) //
				.apply(TextIO.Write.to("/tmp/output/flights1").withSuffix(".txt"));

		p.run();
	}
}
