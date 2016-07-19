package com.google.cloud.training.dataanalyst.flights;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.Serializable;
import java.nio.FloatBuffer;

import org.bytedeco.javacpp.tensorflow;
import org.bytedeco.javacpp.helper.tensorflow.StringArray;
import org.bytedeco.javacpp.tensorflow.Env;
import org.bytedeco.javacpp.tensorflow.GraphDef;
import org.bytedeco.javacpp.tensorflow.Session;
import org.bytedeco.javacpp.tensorflow.SessionOptions;
import org.bytedeco.javacpp.tensorflow.Status;
import org.bytedeco.javacpp.tensorflow.StringTensorPairVector;
import org.bytedeco.javacpp.tensorflow.StringVector;
import org.bytedeco.javacpp.tensorflow.Tensor;
import org.bytedeco.javacpp.tensorflow.TensorShape;
import org.bytedeco.javacpp.tensorflow.TensorVector;

public class TensorflowModel {
	private final Session session;
	
	public TensorflowModel(String modelFile, String graphFile) {
		// download to local machine
		try {
			modelFile = gsDownload(modelFile);
			graphFile = gsDownload(graphFile);
		} catch (Exception e) {
			throw new RuntimeException(e);
		}
		
		// read tensorflow graph
		session = new Session(new SessionOptions());
		//GraphDef def = createTensorFlowModel();
		GraphDef def = new GraphDef();
		tensorflow.ReadBinaryProto(Env.Default(), graphFile, def);
		Status s = session.Create(def);
		if (!s.ok()) {
			throw new RuntimeException(s.error_message().getString());
		}
		
		// restore tensorflow model
		Tensor fn = createTensorFromString(modelFile);
		s = session.Run(new StringTensorPairVector(new String[]{"save/Const:0"}, new Tensor[]{fn}),
				new StringVector(), new StringVector("save/restore_all"), new TensorVector());
		if (!s.ok()) {
			throw new RuntimeException(s.error_message().getString());
		}
	}
	
	private static String CACHE_PREFIX = "/tmp/cachetf_";
	private static String gsDownload(String modelFile) throws IOException, InterruptedException {
		if (!modelFile.startsWith("gs://")) {
			return modelFile; // already local
		}
		
		File localFile = new File(CACHE_PREFIX + new File(modelFile).getName());
		if (!localFile.exists()) {
			int exitCode = Runtime.getRuntime().exec("gsutil cp " + modelFile + " " + localFile).waitFor();
			if (exitCode != 0) {
				throw new FileNotFoundException(modelFile + " could not be downloaded. Does it exist?");
			}
		}
		return localFile.getAbsolutePath();
	}

	public float predict(float[] predictors) {
		final int npatterns = 1;

		// placeholders for inputs
		Tensor inputs = new Tensor(tensorflow.DT_FLOAT, new TensorShape(npatterns,predictors.length));
		FloatBuffer x = inputs.createBuffer();
		x.put(predictors);
		Tensor keepall = new Tensor(tensorflow.DT_FLOAT, new TensorShape(npatterns,1));
		((FloatBuffer)keepall.createBuffer()).put(new float[]{1f, 1f});

		// placeholder for output
		TensorVector outputs = new TensorVector();
		outputs.resize(0);
		
		// run prediction
		Status s = session.Run(new StringTensorPairVector(new String[] {"Placeholder", "Placeholder_2"}, new Tensor[] {inputs, keepall}),
                new StringVector("Sigmoid"), new StringVector(), outputs);
		if (!s.ok()) {
			throw new RuntimeException(s.error_message().getString());
		}
		FloatBuffer output = outputs.get(0).createBuffer();
		return output.get(0);
	}
	
	private static Tensor createTensorFromString(String data) {
		Tensor fn = new Tensor(tensorflow.DT_STRING, new TensorShape(1));
		StringArray a = fn.createStringArray();
		a.position(0).put(data);
		return fn;
	}

}
