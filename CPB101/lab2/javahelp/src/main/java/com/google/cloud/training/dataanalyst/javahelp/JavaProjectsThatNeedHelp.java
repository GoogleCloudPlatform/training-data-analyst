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
import java.util.Collections;
import java.util.List;
import java.util.Map;

import com.google.api.services.bigquery.model.TableRow;
import com.google.cloud.dataflow.sdk.Pipeline;
import com.google.cloud.dataflow.sdk.io.BigQueryIO;
import com.google.cloud.dataflow.sdk.io.TextIO;
import com.google.cloud.dataflow.sdk.options.Default;
import com.google.cloud.dataflow.sdk.options.Description;
import com.google.cloud.dataflow.sdk.options.PipelineOptions;
import com.google.cloud.dataflow.sdk.options.PipelineOptionsFactory;
import com.google.cloud.dataflow.sdk.transforms.DoFn;
import com.google.cloud.dataflow.sdk.transforms.ParDo;
import com.google.cloud.dataflow.sdk.transforms.Sum;
import com.google.cloud.dataflow.sdk.transforms.Top;
import com.google.cloud.dataflow.sdk.transforms.View;
import com.google.cloud.dataflow.sdk.values.KV;
import com.google.cloud.dataflow.sdk.values.PCollection;
import com.google.cloud.dataflow.sdk.values.PCollectionView;

/**
 * A dataflow pipeline that finds Java packages on github that are: (a) used a
 * lot by other projects (we count the number of times this package appears in
 * imports elsewhere) (b) needs help (count the number of times this package has
 * the words FIXME or TODO in its source)
 * 
 * @author vlakshmanan
 *
 */
public class JavaProjectsThatNeedHelp {

	private static final int TOPN = 1000; // how many packages to write out

	public static interface MyOptions extends PipelineOptions {
		@Description("Output prefix")
		@Default.String("gs://cloud-training-demos/javahelp/output")
		String getOutputPrefix();

		void setOutputPrefix(String s);
	}

	@SuppressWarnings("serial")
	public static void main(String[] args) {
		MyOptions options = PipelineOptionsFactory.fromArgs(args).withValidation().as(MyOptions.class);
		Pipeline p = Pipeline.create(options);

		String javaQuery = "SELECT content FROM [fh-bigquery:github_extracts.contents_java_2016]";
		PCollection<String[]> javaContent = p.apply("GetJava", BigQueryIO.Read.fromQuery(javaQuery)) //
				.apply("ToLines", ParDo.of(new DoFn<TableRow, String[]>() {
					@Override
					public void processElement(ProcessContext c) throws Exception {
						TableRow row = c.element();
						String content = (String) row.get("content");
						if (content != null) {
							String[] lines = content.split("\n");
							if (lines.length > 0) {
								c.output(lines);
							}
						}
					}
				}));

		// packages that need help
		PCollectionView<Map<String, Integer>> packagesThatNeedHelp = javaContent
				.apply("NeedsHelp", ParDo.of(new DoFn<String[], KV<String, Integer>>() {

					@Override
					public void processElement(ProcessContext c) throws Exception {
						String[] lines = c.element();
						String[] packages = parsePackageStatement(lines);
						int numHelpNeeded = countCallsForHelp(lines);
						if (numHelpNeeded > 0) {
							for (String packageName : packages) {
								c.output(KV.of(packageName, numHelpNeeded));
							}
						}
					}

				})) //
				.apply(Sum.integersPerKey()) // package -> number-of-help-wanted
				.apply("ToView", View.asMap());

		// packages in terms of use and which need help
		javaContent //
				.apply("IsPopular", ParDo.of(new DoFn<String[], KV<String, Integer>>() {
					@Override
					public void processElement(ProcessContext c) throws Exception {
						String[] lines = c.element();
						String[] packages = parseImportStatement(lines);
						for (String packageName : packages) {
							c.output(KV.of(packageName, 1)); // used once
						}
					}
				})) //
				.apply(Sum.integersPerKey()) // package -> number-of-uses
				.apply("CompositeScore", ParDo.withSideInputs(packagesThatNeedHelp) //
						.of(new DoFn<KV<String, Integer>, KV<String, Double>>() {

							@Override
							public void processElement(ProcessContext c) throws Exception {
								String packageName = c.element().getKey();
								int numTimesUsed = c.element().getValue();
								Integer numHelpNeeded = c.sideInput(packagesThatNeedHelp).get(packageName);
								if (numHelpNeeded != null) {
									// multiply to get composite score
									// log() because these measures are subject to tournament effects
									c.output(KV.of(packageName, Math.log(numTimesUsed) * Math.log(numHelpNeeded)));
								}
							}

						})) //
				.apply("Top_" + TOPN, Top.of(TOPN, new KV.OrderByValue<>())) //
				.apply("ToString", ParDo.of(new DoFn<List<KV<String, Double>>, String>() {

					@Override
					public void processElement(ProcessContext c) throws Exception {
						List<KV<String, Double>> sorted = new ArrayList<>(c.element());
						Collections.sort(sorted, new KV.OrderByValue<>());
						Collections.reverse(sorted);
						for (KV<String, Double> kv : c.element()) {
							c.output(kv.getKey() + "," + kv.getValue());
						}
					}

				})) //
				.apply(TextIO.Write.to(options.getOutputPrefix()).withSuffix(".csv").withoutSharding());

		p.run();
	}

	protected static String[] parseImportStatement(String[] lines) {
		final String keyword = "import";
		List<String> result = new ArrayList<>();
		for (String line : lines) {
			if (line.startsWith(keyword)) {
				result.addAll(getPackages(line, keyword));
			}
		}
		return result.toArray(new String[0]);
	}

	// e.g: import java.util.List; --> java.util.List, java.util, java
	private static List<String> getPackages(String line, String keyword) {
		int start = line.indexOf(keyword) + keyword.length();
		int end = line.indexOf(";", start);
		if (start < end) {
			String packageName = line.substring(start, end).trim();
			return splitPackageName(packageName);
		}
		return new ArrayList<String>();
	}

	private static int countCallsForHelp(String[] lines) {
		int count = 0;
		for (String line : lines) {
			if (line.contains("FIXME") || line.contains("TODO")) {
				++count;
			}
		}
		return count;
	}

	private static String[] parsePackageStatement(String[] lines) {
		final String keyword = "package";
		for (String line : lines) {
			if (line.startsWith(keyword)) {
				// only one package statement per file
				return getPackages(line, keyword).toArray(new String[0]);
			}
		}
		return new String[0];
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
