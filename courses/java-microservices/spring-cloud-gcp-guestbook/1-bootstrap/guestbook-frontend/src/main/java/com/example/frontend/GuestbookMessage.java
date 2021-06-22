package com.example.frontend;

import lombok.Data;
import org.springframework.hateoas.RepresentationModel;

@Data
public class GuestbookMessage extends RepresentationModel<GuestbookMessage> {
  private String id;

  private String name;

  private String message;

  private String imageUri;

}
