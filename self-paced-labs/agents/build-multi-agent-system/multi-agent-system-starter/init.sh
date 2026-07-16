#!/bin/bash

# --- Function for error handling ---
handle_error() {
  echo -e "\n\n*******************************************************"
  echo "Error: $1"
  echo "*******************************************************"
  exit 1
}

# --- Part 1: Find or Create Google Cloud Project ID ---
PROJECT_FILE="$HOME/project_id.txt"
PROJECT_ID_SET=false

# Check if a project ID file already exists and points to a valid project
if [ -s "$PROJECT_FILE" ]; then
    EXISTING_PROJECT_ID=$(cat "$PROJECT_FILE" | tr -d '[:space:]') # Read and trim whitespace
    echo "--- Found existing project ID in $PROJECT_FILE: $EXISTING_PROJECT_ID ---"
    echo "Verifying this project exists in Google Cloud..."

    # Check if the project actually exists in GCP and we have permission to see it
    if gcloud projects describe "$EXISTING_PROJECT_ID" --quiet >/dev/null 2>&1; then
        echo "Project '$EXISTING_PROJECT_ID' successfully verified."
        FINAL_PROJECT_ID=$EXISTING_PROJECT_ID
        PROJECT_ID_SET=true

        # Ensure gcloud config is set to this project for the current session
        gcloud config set project "$FINAL_PROJECT_ID" || handle_error "Failed to set active project to '$FINAL_PROJECT_ID'."
        echo "Set active gcloud project to '$FINAL_PROJECT_ID'."
    else
        echo "Warning: Project '$EXISTING_PROJECT_ID' from file does not exist or you lack permissions."
        echo "Removing invalid reference file and proceeding with new project creation."
        rm "$PROJECT_FILE"
    fi
fi

# If no valid existing project was found, start the interactive creation process
if [ "$PROJECT_ID_SET" = false ]; then
    echo "--- Creating and Setting New Google Cloud Project ID ---"
    CODELAB_PROJECT_PREFIX="production-ready-ai"

    # Dynamic Length Calculation
    PREFIX_LEN=${#CODELAB_PROJECT_PREFIX}
    if (( PREFIX_LEN > 25 )); then
      handle_error "The project prefix '$CODELAB_PROJECT_PREFIX' is too long (${PREFIX_LEN} chars). Maximum is 25."
    fi
    MAX_SUFFIX_LEN=$(( 30 - PREFIX_LEN - 1 ))
    echo "Project prefix '${CODELAB_PROJECT_PREFIX}' is ${PREFIX_LEN} chars. Suffix will be ${MAX_SUFFIX_LEN} chars."

    # Loop until a project is successfully created.
    while true; do
      RANDOM_SUFFIX=$(LC_ALL=C tr -dc 'a-z0-9' < /dev/urandom | head -c "$MAX_SUFFIX_LEN")
      SUGGESTED_PROJECT_ID="${CODELAB_PROJECT_PREFIX}-${RANDOM_SUFFIX}"

      read -p "Enter project ID or press Enter to use default: " -e -i "$SUGGESTED_PROJECT_ID" FINAL_PROJECT_ID

      if [[ -z "$FINAL_PROJECT_ID" ]]; then
          echo "Project ID cannot be empty. Please try again."
          continue
      fi

      echo "Attempting to create project with ID: $FINAL_PROJECT_ID"
      ERROR_OUTPUT=$(gcloud projects create "$FINAL_PROJECT_ID" --quiet 2>&1)
      CREATE_STATUS=$?

      if [[ $CREATE_STATUS -eq 0 ]]; then
        echo "Successfully created project: $FINAL_PROJECT_ID"
        gcloud config set project "$FINAL_PROJECT_ID" || handle_error "Failed to set active project to $FINAL_PROJECT_ID."
        echo "Set active gcloud project to $FINAL_PROJECT_ID."
        echo "$FINAL_PROJECT_ID" > "$PROJECT_FILE" || handle_error "Failed to save project ID to $PROJECT_FILE."
        echo "Successfully saved project ID to $PROJECT_FILE."
        break
      else
        echo "Could not create project '$FINAL_PROJECT_ID'."
        echo "Reason from gcloud: $ERROR_OUTPUT"
        echo -e "This ID may be taken. Please try a different project ID.\n"
      fi
    done
fi

# --- Part 2: Install Dependencies and Run Billing Setup ---
# This part runs for both existing and newly created projects.
echo -e "\n--- Installing Python dependencies ---"
pip install --upgrade --user google-cloud-billing || handle_error "Failed to install Python libraries."

echo -e "\n--- Running the Billing Enablement Script ---"
python3 billing-enablement.py || handle_error "The billing enablement script failed. See the output above for details."

echo -e "\n--- Full Setup Complete ---"
exit 0
