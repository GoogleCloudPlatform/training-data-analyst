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
import org.apache.beam.sdk.Pipeline;
import org.apache.beam.sdk.io.gcp.bigquery.BigQueryIO;
import org.apache.beam.sdk.io.TextIO;
import org.apache.beam.sdk.options.Default;
import org.apache.beam.sdk.options.Description;
import org.apache.beam.sdk.options.PipelineOptions;
import org.apache.beam.sdk.options.PipelineOptionsFactory;
import org.apache.beam.sdk.transforms.DoFn;
import org.apache.beam.sdk.transforms.ParDo;
import org.apache.beam.sdk.transforms.Sum;
import org.apache.beam.sdk.transforms.Top;
import org.apache.beam.sdk.transforms.View;
import org.apache.beam.sdk.values.KV;
import org.apache.beam.sdk.values.PCollection;
import org.apache.beam.sdk.values.PCollectionView;

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
		PCollection<String[]> javaContent = p.apply("GetJava", BigQueryIO.read().fromQuery(javaQuery)) //
				.apply("ToLines", ParDo.of(new DoFn<TableRow, String[]>() {
					@ProcessElement
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

					@ProcessElement
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
					@ProcessElement
					public void processElement(ProcessContext c) throws Exception {
						String[] lines = c.element();
						String[] packages = parseImportStatement(lines);
						for (String packageName : packages) {
							c.output(KV.of(packageName, 1)); // used once
						}
					}
				})) //
				.apply(Sum.integersPerKey()) // package -> number-of-uses
				.apply("CompositeScore", ParDo //
						.of(new DoFn<KV<String, Integer>, KV<String, Double>>() {

							@ProcessElement
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

						}).withSideInputs(packagesThatNeedHelp)) //
				.apply("Top_" + TOPN, Top.of(TOPN, new KV.OrderByValue<>())) //
				.apply("ToString", ParDo.of(new DoFn<List<KV<String, Double>>, String>() {

					@ProcessElement
					public void processElement(ProcessContext c) throws Exception {
						List<KV<String, Double>> sorted = new ArrayList<>(c.element());
						Collections.sort(sorted, new KV.OrderByValue<>());
						Collections.reverse(sorted);
						
						StringBuffer sb = new StringBuffer();
						for (KV<String, Double> kv : c.element()) {
							sb.append(kv.getKey() + "," + kv.getValue() + '\n');
						}
						c.output(sb.toString());
					}

				})) //
				.apply(TextIO.write().to(options.getOutputPrefix()).withSuffix(".csv").withoutSharding());

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
