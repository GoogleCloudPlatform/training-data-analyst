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

import static org.bytedeco.javacpp.tensorflow.Const;
import static org.bytedeco.javacpp.tensorflow.Variable;

import java.nio.ByteBuffer;
import java.nio.FloatBuffer;
import java.util.Map;

import org.bytedeco.javacpp.tensorflow;
import org.bytedeco.javacpp.tensorflow.GraphDef;
import org.bytedeco.javacpp.tensorflow.GraphDefBuilder;
import org.bytedeco.javacpp.tensorflow.Node;
import org.bytedeco.javacpp.tensorflow.Session;
import org.bytedeco.javacpp.tensorflow.SessionOptions;
import org.bytedeco.javacpp.tensorflow.Status;
import org.bytedeco.javacpp.tensorflow.StringTensorPairVector;
import org.bytedeco.javacpp.tensorflow.StringVector;
import org.bytedeco.javacpp.tensorflow.Tensor;
import org.bytedeco.javacpp.tensorflow.TensorShape;
import org.bytedeco.javacpp.tensorflow.TensorVector;
import org.joda.time.Duration;
import org.joda.time.Instant;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.google.cloud.dataflow.sdk.Pipeline;
import com.google.cloud.dataflow.sdk.io.TextIO;
import com.google.cloud.dataflow.sdk.options.Default;
import com.google.cloud.dataflow.sdk.options.Description;
import com.google.cloud.dataflow.sdk.options.PipelineOptions;
import com.google.cloud.dataflow.sdk.options.PipelineOptionsFactory;
import com.google.cloud.dataflow.sdk.transforms.DoFn;
import com.google.cloud.dataflow.sdk.transforms.Mean;
import com.google.cloud.dataflow.sdk.transforms.ParDo;
import com.google.cloud.dataflow.sdk.transforms.View;
import com.google.cloud.dataflow.sdk.values.KV;
import com.google.cloud.dataflow.sdk.values.PCollection;
import com.google.cloud.dataflow.sdk.values.PCollectionView;

/**
 * A dataflow pipeline to predict whether a flight will be delayed by 15 or more
 * minutes.
 * 
 * @author vlakshmanan
 *
 */
public class PredictRealtime {
	@SuppressWarnings("serial")
	public static class ParseFlights extends DoFn<String, Flight> {
		public static final int INVALID_HOUR = -1000;
		private final PCollectionView<Map<String, Double>> delays;

		public ParseFlights(PCollectionView<Map<String, Double>> delays) {
			super();
			this.delays = delays;
		}

		@Override
		public void processElement(ProcessContext c) throws Exception {
			String line = c.element();
			try {
				String[] fields = line.split(",");
				if (fields[22].length() == 0 || fields[0].equals("FL_DATE")) {
					return; // delayed/canceled
				}

				Flight f = new Flight();
				f.line = line;
				f.date = fields[0];
				f.fromAirport = fields[8];
				f.toAirport = fields[12];
				f.depHour = Integer.parseInt(fields[13]) / 100; // 2358 -> 23
				f.arrHour = INVALID_HOUR;
				f.departureDelay = Double.parseDouble(fields[15]);
				f.taxiOutTime = Double.parseDouble(fields[16]);
				f.distance = Double.parseDouble(fields[26]);
				f.arrivalDelay = Double.NaN;
				Double d = c.sideInput(delays).get(f.fromAirport + ":" + f.depHour);
				f.averageDepartureDelay = (d == null) ? 0 : d;
				f.averageArrivalDelay = Double.NaN;
				// without arrival time: for prediction
				c.outputWithTimestamp(f, toInstant(fields[0], fields[13]));

				// with arrival time: for computing avg arrival delay
				f.arrHour = Integer.parseInt(fields[21]) / 100;
				f.arrivalDelay = Double.parseDouble(fields[22]);
				c.outputWithTimestamp(f, toInstant(fields[0], fields[21]));

			} catch (Exception e) {
				LOG.warn("Malformed line {" + line + "} skipped", e);
			}
		}

	}

	private static final Logger LOG = LoggerFactory.getLogger(PredictRealtime.class);

	public static interface MyOptions extends PipelineOptions {
		@Description("Path of the file to read from")
		@Default.String("/Users/vlakshmanan/data/flights/small.csv")
		String getInput();

		void setInput(String s);

		@Description("Path of the output directory")
		@Default.String("/tmp/output/")
		String getOutput();

		void setOutput(String s);

		@Description("Path of delay files")
		@Default.String("/Users/vlakshmanan/data/flights/")
		// @Default.String("gs://cloud-training-demos/flights/chapter07/")
		String getDelayPath();

		void setDelayPath(String s);

		@Description("Path of tensorflow model")
		@Default.String(// "gs://cloud-training-demos/flights/chapter07/trained_model.tf")
		"/Users/vlakshmanan/code/training-data-analyst/flights-data-analysis/09_realtime/trained_model.tf")
		String getModelfile();

		void setModelfile(String s);
	}

	@SuppressWarnings("serial")
	public static void main(String[] args) {
		MyOptions options = PipelineOptionsFactory.fromArgs(args).withValidation().as(MyOptions.class);
		Pipeline p = Pipeline.create(options);

		// read tensorflow modelfile ...
		final Session session = new Session(new SessionOptions());
		GraphDef def = createTensorFlowModel();
		Status s = session.Create(def);
		if (!s.ok()) {
			throw new RuntimeException(s.error_message().getString());
		}
		Tensor fn = createTensorFromString(options.getModelfile());
		// StringTensorPairVector inputs, StringVector output_tensornames,
		// StringVector target_node_names, TensorVector outputs
		s = session.Run(new StringTensorPairVector(new String[] { "save/Const:0" }, new Tensor[] { fn }),
				new StringVector(),
				new StringVector("save/restore_all"), new TensorVector());
		if (!s.ok()) {
			throw new RuntimeException(s.error_message().getString());
		}
		
		// try to predict some value
		Tensor inputs = new Tensor(tensorflow.DT_FLOAT, new TensorShape(1,5));
		FloatBuffer x = inputs.createBuffer();
		x.put(new float[]{-6.0f,22.0f,383.0f,27.781754111198122f,-6.5f});
		TensorVector outputs = new TensorVector();
		outputs.resize(0);
		s = session.Run(new StringTensorPairVector(new String[] {"feature_ph"}, new Tensor[] {inputs}),
                new StringVector("model"), new StringVector(), outputs);
		if (!s.ok()) {
			throw new RuntimeException(s.error_message().getString());
		}
		System.out.println(outputs.size());
		System.out.println("Read model file ...");
		System.exit(0);
		
		// read delays-*.csv into memory for use as a side-input
		PCollectionView<Map<String, Double>> delays = getAverageDelays(p, options.getDelayPath());

		PCollection<Flight> flights = p //
				.apply("ReadLines", TextIO.Read.from(options.getInput())) //
				.apply("ParseFlights", ParDo.withSideInputs(delays).of(new ParseFlights(delays))) //
		;

		PCollectionView<Map<String, Double>> arrDelay = flights
				.apply("airport:hour", ParDo.of(new DoFn<Flight, KV<String, Double>>() {

					@Override
					public void processElement(ProcessContext c) throws Exception {
						Flight f = c.element();
						if (f.arrHour != ParseFlights.INVALID_HOUR) {
							String key = "arr_" + f.toAirport + ":" + f.date + ":" + f.arrHour;
							double value = f.arrivalDelay;
							c.output(KV.of(key, value));
						}
					}

				})) //
				.apply(Mean.perKey()) //
				.apply(View.asMap());

		flights.apply("Predict", ParDo.withSideInputs(arrDelay).of(new DoFn<Flight, String>() {

			@Override
			public void processElement(ProcessContext c) throws Exception {
				Flight f = c.element();
				if (f.arrHour == ParseFlights.INVALID_HOUR) {
					// don't know when this flight is arriving, so predict ...
					f = f.newCopy();
					// get average arrival delay
					String key = "arr_" + f.toAirport + ":" + f.date + ":" + (f.depHour - 1);
					Double delay = c.sideInput(arrDelay).get(key);
					f.averageArrivalDelay = (delay == null) ? 0 : delay;

					// form inputs to TensorFlow model
					double[] inputs = f.getInputFeatures();

					// compute it
					boolean ontime = true;

					// output
					c.output(f.line + "," + ontime);
				}
			}
		})) //
				.apply("WriteFlights", TextIO.Write.to(options.getOutput() + "flights").withSuffix(".csv"));

		p.run();
	}

	private static Tensor createTensorFromString(String data) {
		System.out.println("Reading model from " + data);
		Tensor fn = new Tensor(tensorflow.DT_STRING, new TensorShape(1));
		// StringArray a = fn.createStringArray();
		ByteBuffer buffer = fn.createBuffer(); // FIXME
		buffer.put(data.getBytes());
		return fn;
	}

	private static GraphDef createTensorFlowModel() {
		GraphDefBuilder b = new GraphDefBuilder();

		// Java version of the Python graph
		int npredictors = 5;
		int[] nhidden = { 50, 10 };
		int noutputs = 1;

		// number of nodes in each layer
		int[] numnodes = new int[2 + nhidden.length];
		numnodes[0] = npredictors;
		for (int i = 0; i < nhidden.length; ++i) {
			numnodes[i + 1] = nhidden[i];
		}
		numnodes[numnodes.length - 1] = noutputs;

		// input and output placeholders
		Node feature_ph = Const(new float[] { 0f }, new TensorShape(0, npredictors), b.opts().WithName("feature_ph"));
		// Node target_ph = Const(new float[] {0f}, new TensorShape(-1,
		// noutputs), b.opts().WithName("target_ph"));

		// weights and biases. weights for each input; bias for each output
		Node[] weights = new Node[numnodes.length - 1];
		Node[] biases = new Node[numnodes.length - 1];
		for (int i = 0; i < numnodes.length - 1; ++i) {
			// no need to initialize these to random variables ...
			weights[i] = Variable(new TensorShape(numnodes[i], numnodes[i + 1]), tensorflow.DT_FLOAT,
					b.opts().WithName("weight_" + i));
			biases[i] = Variable(new TensorShape(numnodes[i + 1]), tensorflow.DT_FLOAT, b.opts().WithName("bias_" + i));
			;
		}

		// matrix multiplication at each layer
		// activation function = tanh for input, relu for each hidden layer,
		// sigmoid for output layer
		Node model = tensorflow.Tanh( // model = tf.tanh(tf.matmul(feature_ph,
										// weights[0]) + biases[0])
				tensorflow.Add(//
						tensorflow.MatMul(feature_ph, weights[0], b.opts()), biases[0], b.opts()),
				b.opts());
		for (int layer = 1; layer < weights.length - 1; ++layer) {
			// ignore drop-out in prediction
			model = tensorflow
					.Relu(//
							tensorflow.Add(//
									tensorflow.MatMul(model, weights[layer], b.opts()), biases[layer], b.opts()),
							b.opts());// tf.nn.relu(tf.matmul(model,
										// weights[layer]) + biases[layer]
		}
		model = tensorflow.Sigmoid( // model = tf.sigmoid(tf.matmul(model,
									// weights[-1]) + biases[-1])
				tensorflow.Add( //
						tensorflow.MatMul(model, weights[weights.length - 1], b.opts()), biases[biases.length - 1],
						b.opts()),
				b.opts().WithName("model"));

		// for saving and restoring
		Node[] allvars = new Node[weights.length + biases.length];
		for (int i = 0; i < weights.length; ++i) {
			allvars[i] = weights[i];
		}
		for (int i = 0; i < biases.length; ++i) {
			allvars[weights.length + i] = biases[i];
		}

		// graph def
		GraphDef def = new GraphDef();
		Status s = b.ToGraphDef(def);
		if (!s.ok()) {
			throw new RuntimeException(s.error_message().getString());
		}
		return def;
	}

	public static Instant toInstant(String date, String hourmin) {
		// e.g: 2015-01-01 and 0837
		int hrmin = Integer.parseInt(hourmin);
		int hr = hrmin / 100;
		int min = hrmin % 100;
		return Instant.parse(date) //
				.plus(Duration.standardHours(hr)) //
				.plus(Duration.standardMinutes(min));
	}

	@SuppressWarnings("serial")
	private static PCollectionView<Map<String, Double>> getAverageDelays(Pipeline p, String path) {
		return p.apply("Read delays-*.csv", TextIO.Read.from(path + "delays-*.csv")) //
				.apply("Parse delays-*.csv", ParDo.of(new DoFn<String, KV<String, Double>>() {
					@Override
					public void processElement(ProcessContext c) throws Exception {
						String line = c.element();
						String[] fields = line.split(",");
						c.output(KV.of(fields[0], Double.parseDouble(fields[1])));
					}
				})) //
				.apply("toView", View.asMap());
	}
}
