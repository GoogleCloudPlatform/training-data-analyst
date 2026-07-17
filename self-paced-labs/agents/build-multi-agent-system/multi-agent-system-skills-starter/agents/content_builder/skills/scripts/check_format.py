def check_format(text: str) -> dict:
    # Perform basic heading checks
    has_h1 = text.strip().startswith("# ")
    has_h2 = "## " in text
    
    # TODO: Return a dictionary with "success" (bool) and "message" (str) keys.
    # Return success=True if both headings exist, otherwise return success=False with a message explaining what is missing.
    pass
