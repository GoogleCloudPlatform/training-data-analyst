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

import java.util.ArrayList;
import java.util.List;

import org.apache.beam.sdk.Pipeline;
import org.apache.beam.sdk.io.TextIO;
import org.apache.beam.sdk.options.Default;
import org.apache.beam.sdk.options.Description;
import org.apache.beam.sdk.options.PipelineOptions;
import org.apache.beam.sdk.options.PipelineOptionsFactory;
import org.apache.beam.sdk.transforms.DoFn;
import org.apache.beam.sdk.transforms.ParDo;
import org.apache.beam.sdk.transforms.Sum;
import org.apache.beam.sdk.transforms.Top;
import org.apache.beam.sdk.values.KV;

/**
 * A dataflow pipeline that finds the most commonly imported packages
 * 
 * @author vlakshmanan
 *
 */
public class IsPopular {

	public static interface MyOptions extends PipelineOptions {
		@Description("Output prefix")
		@Default.String("/tmp/output")
		String getOutputPrefix();

		void setOutputPrefix(String s);
		
		@Description("Input directory")
		@Default.String("src/main/java/com/google/cloud/training/dataanalyst/javahelp/")
		String getInput();

		void setInput(String s);
	}
	
	@SuppressWarnings("serial")
	public static void main(String[] args) {
		MyOptions options = PipelineOptionsFactory.fromArgs(args).withValidation().as(MyOptions.class);
		Pipeline p = Pipeline.create(options);

		String input = options.getInput() + "*.java";
		String outputPrefix = options.getOutputPrefix();
		final String keyword = "import";
		
		p //
				.apply("GetJava", TextIO.read().from(input)) //
				.apply("GetImports", ParDo.of(new DoFn<String, String>() {
					@ProcessElement
					public void processElement(ProcessContext c) throws Exception {
						String line = c.element();
						if (line.startsWith(keyword)) {
							c.output(line);
						}
					}
				})) //
				.apply("PackageUse", ParDo.of(new DoFn<String, KV<String,Integer>>() {
					@ProcessElement
					public void processElement(ProcessContext c) throws Exception {
						List<String> packages = getPackages(c.element(), keyword);
						for (String p : packages) {
							c.output(KV.of(p, 1));
						}
					}
				})) //
				.apply(Sum.integersPerKey())
				.apply("Top_5", Top.of(5, new KV.OrderByValue<>())) //
				.apply("ToString", ParDo.of(new DoFn<List<KV<String, Integer>>, String>() {

					@ProcessElement
					public void processElement(ProcessContext c) throws Exception {
						StringBuffer sb = new StringBuffer();
						for (KV<String, Integer> kv : c.element()) {
							sb.append(kv.getKey() + "," + kv.getValue() + '\n');
						}
						c.output(sb.toString());
					}

				})) //
				.apply(TextIO.write().to(outputPrefix).withSuffix(".csv").withoutSharding());

		p.run();
	}
	
	private static List<String> getPackages(String line, String keyword) {
		int start = line.indexOf(keyword) + keyword.length();
		int end = line.indexOf(";", start);
		if (start < end) {
			String packageName = line.substring(start, end).trim();
			return splitPackageName(packageName);
		}
		return new ArrayList<String>();
	}
	
	private static List<String> splitPackageName(String packageName) {
		// e.g. given com.example.appname.library.widgetname
		// returns com
		// com.example
		// com.example.appname
		// etc.
		List<String> result = new ArrayList<>();
		int end = packageName.indexOf('.');
		while (end > 0) {
			result.add(packageName.substring(0, end));
			end = packageName.indexOf('.', end + 1);
		}
		result.add(packageName);
		return result;
	}
}
