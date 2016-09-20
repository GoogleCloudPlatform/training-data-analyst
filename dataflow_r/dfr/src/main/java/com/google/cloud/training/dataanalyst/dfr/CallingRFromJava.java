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

import java.io.DataInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.text.DecimalFormat;

import javax.script.ScriptEngine;
import javax.script.ScriptEngineManager;

import org.renjin.sexp.ListVector;

import com.google.cloud.dataflow.sdk.Pipeline;
import com.google.cloud.dataflow.sdk.io.TextIO;
import com.google.cloud.dataflow.sdk.options.Default;
import com.google.cloud.dataflow.sdk.options.Description;
import com.google.cloud.dataflow.sdk.options.PipelineOptions;
import com.google.cloud.dataflow.sdk.options.PipelineOptionsFactory;
import com.google.cloud.dataflow.sdk.transforms.DoFn;
import com.google.cloud.dataflow.sdk.transforms.ParDo;

/**
 * An example for calling R scripts from Dataflow jobs
 * 
 */
public class CallingRFromJava {
	public static interface MyOptions extends PipelineOptions {
		@Description("Output prefix")
		@Default.String("/tmp/output")
		String getOutputPrefix();

		void setOutputPrefix(String s);
		
		@Description("Input file")
		@Default.String("numbers.csv")
		String getInput();

		void setInput(String s);
	}
	
	@SuppressWarnings("serial")
	public static void main(String[] args) throws Exception {
		MyOptions options = PipelineOptionsFactory.fromArgs(args).withValidation().as(MyOptions.class);
		Pipeline p = Pipeline.create(options);

		// read program
		String rprog = getFileContent(CallingRFromJava.class.getResourceAsStream("myprog.r"));
		
		p //
				.apply(TextIO.Read.from(options.getInput())) //
				.apply(ParDo.of(new DoFn<String, String>() {
					@Override
					public void processElement(ProcessContext c) {
						// extract numbers from input
						String[] fields = c.element().split(",");
						String type = fields[0];
						double[] inputx = new double[fields.length - 1];
						for (int i = 1; i < fields.length; ++i) {
							inputx[i - 1] = Double.parseDouble(fields[i]);
						}

						// to execute R code:
						try {
							ScriptEngineManager manager = new ScriptEngineManager();
							ScriptEngine engine = manager.getEngineByName("Renjin");

							// get input from dataflow, send it to R
							engine.put("x", inputx);

							// run R program, get output from R, send to
							// Dataflow
							ListVector result = (ListVector) engine.eval(rprog);
							// see:
							// https://cran.r-project.org/web/packages/exptest/exptest.pdf
							double pvalue = result.getElementAsDouble(1);

							c.output(type + "," + new DecimalFormat(".00").format(pvalue));
						} catch (Exception e) {
							throw new RuntimeException(e);
						}
					}
				})) //
				.apply(TextIO.Write.to(options.getOutputPrefix()));

		p.run();
	}
	
	public static String getFileContent(InputStream is) throws IOException {    
	    StringBuffer sb = new StringBuffer();
	    try (DataInputStream dis = new DataInputStream(is)) {
	        while (dis.available() > 0) {
	            byte[] buffer = new byte[dis.available()];
	            dis.read(buffer);
	            sb.append(new String(buffer, "ISO-8859-1"));
	        }
	    }
	    return sb.toString();
	}

}
