/*
 * Copyright 2018 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.google.training.appdev.services.gcp.spanner;

import com.google.cloud.spanner.*;
import com.google.training.appdev.services.gcp.domain.Answer;
import com.google.training.appdev.services.gcp.domain.Feedback;
import com.google.training.appdev.services.gcp.domain.LeaderBoardEntry;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

@Service
public class SpannerService {
    private static final SpannerService spannerService= new SpannerService(){};

    public static SpannerService create(){
        return spannerService;
    }

    public void insertFeedback(Feedback feedback){
        SpannerOptions options = SpannerOptions.newBuilder().build();
        Spanner spanner = options.getService();
        try {
            DatabaseId db = DatabaseId.of(options.getProjectId(), "quiz-instance", "quiz-database");
            DatabaseClient dbClient = spanner.getDatabaseClient(db);

            List<Mutation> mutations = new ArrayList<>();

            mutations.add(
                    Mutation.newInsertBuilder("Feedback")
                            .set("feedbackId")
                            .to(feedback.getEmail()+'_'+feedback.getQuiz()+"_"+feedback.getTimestamp())
                            .set("email")
                            .to(feedback.getEmail())
                            .set("quiz")
                            .to(feedback.getQuiz())
                            .set("feedback")
                            .to(feedback.getFeedback())
                            .set("rating")
                            .to(feedback.getRating())
                            .set("score")
                            .to(feedback.getSentimentScore())
                            .set("timestamp")
                            .to(feedback.getTimestamp())
                            .build());

            dbClient.write(mutations);
        }catch(Exception e){
            e.printStackTrace();
        }
    }

    public void insertAnswer(Answer answer) {
        SpannerOptions options = SpannerOptions.newBuilder().build();
        Spanner spanner = options.getService();
        try {
            DatabaseId db = DatabaseId.of(options.getProjectId(), "quiz-instance", "quiz-database");
            DatabaseClient dbClient = spanner.getDatabaseClient(db);

            List<Mutation> mutations = new ArrayList<>();

            mutations.add(
                    Mutation.newInsertBuilder("Answers")
                            .set("answerId")
                            .to(answer.getEmail()+'_'+answer.getQuiz()+"_"+answer.getTimestamp())
                            .set("id")
                            .to(answer.getId())
                            .set("email")
                            .to(answer.getEmail())
                            .set("quiz")
                            .to(answer.getQuiz())
                            .set("answer")
                            .to(answer.getAnswer())
                            .set("correct")
                            .to(answer.getCorrectAnswer())
                            .set("timestamp")
                            .to(answer.getTimestamp())
                            .build());

            dbClient.write(mutations);
        }catch(Exception e){
            e.printStackTrace();
        }
    }

    public List<LeaderBoardEntry> getQuizLeaders(){
        SpannerOptions options = SpannerOptions.newBuilder().build();
        Spanner spanner = options.getService();
        List<LeaderBoardEntry> leaderBoardEntries = new ArrayList<>();
        try {
            DatabaseId db = DatabaseId.of(options.getProjectId(), "quiz-instance", "quiz-database");
            DatabaseClient dbClient = spanner.getDatabaseClient(db);


            String query = "SELECT quiz, email, COUNT(*) AS score FROM Answers WHERE correct = answer GROUP BY quiz, email ORDER BY quiz, score DESC";

            ResultSet resultSet = dbClient
                                    .singleUse()
                                        .executeQuery(Statement.of(query));
            while (resultSet.next()) {
                LeaderBoardEntry leaderBoardEntry = new LeaderBoardEntry();
                leaderBoardEntry.setQuiz(resultSet.getString(0));
                leaderBoardEntry.setEmail(resultSet.getString(1));
                leaderBoardEntry.setScore(resultSet.getLong(2));
                leaderBoardEntries.add(leaderBoardEntry);
            }
        }catch(Exception e){
            e.printStackTrace();
        }
        return leaderBoardEntries;
    }
}
