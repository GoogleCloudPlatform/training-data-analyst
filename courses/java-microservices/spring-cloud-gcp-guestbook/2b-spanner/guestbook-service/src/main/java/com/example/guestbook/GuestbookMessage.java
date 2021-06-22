
package com.example.guestbook;

import lombok.*;
import org.springframework.cloud.gcp.data.spanner.core.mapping.*;
import org.springframework.data.annotation.Id;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

@Data
@Table(name = "guestbook_message")
@JsonIgnoreProperties(value={"id"}, allowSetters = false)
public class GuestbookMessage {
	@PrimaryKey
	@Id
	private String id;

	private String name;
	
	private String message;

	@Column(name = "image_uri")
	private String imageUri;

	public GuestbookMessage() {
		this.id = java.util.UUID.randomUUID().toString();
	}
}
