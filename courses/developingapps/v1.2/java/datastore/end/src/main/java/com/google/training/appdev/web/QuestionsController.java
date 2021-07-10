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
package com.google.training.appdev.web;

import com.google.training.appdev.services.gcp.domain.Question;
import com.google.training.appdev.services.gcp.datastore.QuestionService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;

import java.io.IOException;

@Controller
public class QuestionsController {

    @Autowired
    private QuestionService questionService;

    @GetMapping("/questions/add")
    public String getForm(Model model) {
        model.addAttribute("quizquestion", new Question());
        return "new_question";
    }

    @PostMapping("/questions/add")
    public String submitQuestion(Question question) throws IOException {
        questionService.createQuestion(question);
        return "redirect:/";
    }
}