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

import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.Random;

public class Simulate {
	private static Random rand = new Random();
	static double[] generateUniformRandom() {
		double[] x = new double[100];
		for (int i=0; i < x.length; ++i) {
			x[i] = rand.nextDouble();
		}
		return x;
	}
	
	static double[] generateExp() {
		double lambda = 3;
		double[] x = new double[100];
		for (int i=0; i < x.length; ++i) {
			x[i] = Math.log(1-rand.nextDouble())/(-lambda);
		}
		return x;
	}
	
	public static void main(String[] args) throws Exception {
		try (PrintWriter writer = new PrintWriter(new FileWriter("numbers.csv"))) {
			int N = 100; // how many records?
			for (int i=0; i < N; ++i) {
				boolean exp = rand.nextBoolean();
				double[] inputs = (exp)? generateExp() : generateUniformRandom();
				StringBuilder line = new StringBuilder();
				line.append(exp + ",");
				for (double d : inputs) {
					line.append(d + ",");
				}
				writer.println(line.substring(0, line.length()-1)); // take out last comma
			}
		}
		System.out.println("Created numbers.csv; upload this to cloud storage");
	}
}
