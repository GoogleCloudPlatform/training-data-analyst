/*
 * Copyright (C) 2015 Google Inc.
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

package com.google.cloud.training.dataanalyst.dfr;

import java.io.FileReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.text.DecimalFormat;
import java.util.Random;

import javax.script.ScriptEngine;
import javax.script.ScriptEngineManager;

import org.renjin.sexp.ListVector;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.google.cloud.dataflow.sdk.Pipeline;
import com.google.cloud.dataflow.sdk.options.PipelineOptionsFactory;
import com.google.cloud.dataflow.sdk.transforms.Create;
import com.google.cloud.dataflow.sdk.transforms.DoFn;
import com.google.cloud.dataflow.sdk.transforms.ParDo;

/**
 * An example for calling R scripts from Dataflow jobs
 *
 * <p>
 * To run this starter example locally using DirectPipelineRunner, just execute
 * it without any additional parameters from your favorite development
 * environment.
 *
 * <p>
 * To run this starter example using managed resource in Google Cloud Platform,
 * you should specify the following command-line options: --project=
 * <YOUR_PROJECT_ID> --stagingLocation=
 * <STAGING_LOCATION_IN_CLOUD_STORAGE> --runner=BlockingDataflowPipelineRunner
 */
public class CallingRFromJava {
	private static final Logger LOG = LoggerFactory.getLogger(CallingRFromJava.class);

	@SuppressWarnings("serial")
	public static void main(String[] args) throws Exception {
		Pipeline p = Pipeline.create(PipelineOptionsFactory.fromArgs(args).withValidation().create());
				
		p //
				.apply(Create.of(generateUniformRandom(), generateExp())) // read input
				.apply(ParDo.of(new DoFn<double[], Double>() {
					@Override
					public void processElement(ProcessContext c) {
						// find the R program (it's packaged with this file)
						InputStream rprog = CallingRFromJava.class.getResourceAsStream("myprog.r");
						
						// to execute R code:
					    try {
						    ScriptEngineManager manager = new ScriptEngineManager();
						    ScriptEngine engine = manager.getEngineByName("Renjin");
						    
						    // get input from dataflow, send it to R
							double[] inputx = c.element(); // from input
						    engine.put("x", inputx);

							// run R program, get output from R, send to Dataflow
							ListVector result = (ListVector) engine.eval(new InputStreamReader(rprog));
							// see: https://cran.r-project.org/web/packages/exptest/exptest.pdf
							double pvalue = result.getElementAsDouble(1);
							
							c.output(pvalue);
						} catch (Exception e) {
							throw new RuntimeException(e);
						}
					}
				})) //
				.apply(ParDo.of(new DoFn<Double, Void>() {
					@Override
					public void processElement(ProcessContext c) {
						double pvalue = c.element();
						LOG.info("result.pvalue = " + new DecimalFormat(".00").format(pvalue));
					}
				}));

		p.run();
	}

	private static Random rand = new Random();
	private static double[] generateUniformRandom() {
		double[] x = new double[100];
		for (int i=0; i < x.length; ++i) {
			x[i] = rand.nextDouble();
		}
		return x;
	}
	
	private static double[] generateExp() {
		double lambda = 3;
		double[] x = new double[100];
		for (int i=0; i < x.length; ++i) {
			x[i] = Math.log(1-rand.nextDouble())/(-lambda);
		}
		return x;
	}	
}
