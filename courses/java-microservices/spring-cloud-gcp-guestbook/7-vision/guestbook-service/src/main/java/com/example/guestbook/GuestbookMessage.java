package com.example.guestbook;

import javax.persistence.*;
import lombok.*;

@Entity
@Data
public class GuestbookMessage {
	@Id
	@GeneratedValue(strategy = GenerationType.IDENTITY)
	private Long id;
	
	private String name;
	
	private String message;
	
	private String imageUri;
}

