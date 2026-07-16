import os
import subprocess
import time
from google.cloud import billing_v1
from google.api_core import exceptions

# --- No changes to the functions in this section ---

def get_project_id_from_file():
    """Reads the project ID from the file created by the init.sh script."""
    project_file = os.path.expanduser("~/project_id.txt")
    if not os.path.exists(project_file):
        print(f"Error: Project ID file not found at {project_file}")
        return None
    try:
        with open(project_file, 'r') as f:
            project_id = f.read().strip()
        if not project_id:
            print("Error: Project ID file is empty.")
            return None
        print(f"--- Found Project ID from file: {project_id} ---")
        return project_id
    except Exception as e:
        print(f"Error reading project ID from file: {e}")
        return None

def enable_billing_api(project_id):
    """Enables the Cloud Billing API using a gcloud command."""
    print("\nAttempting to enable the Cloud Billing API...")
    try:
        subprocess.run(
            ["gcloud", "services", "enable", "cloudbilling.googleapis.com", "--project", project_id],
            check=True, capture_output=True, text=True
        )
        print("Successfully sent request to enable the Cloud Billing API.")
        return True
    except FileNotFoundError:
        print("\nError: 'gcloud' command not found.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"\nError enabling Cloud Billing API: {e.stderr}")
        return False

def get_billing_accounts(client):
    """Fetches a list of billing accounts with improved error handling."""
    print("Fetching billing accounts...")
    try:
        accounts = client.list_billing_accounts()
        return list(accounts)
    except exceptions.PermissionDenied as e:
        error_message = e.message.lower()
        if "api has not been used" in error_message or "service is disabled" in error_message:
            print("\nWarning: Received a 'Permission Denied' error that looks like a disabled API.")
            print("This can be a temporary propagation delay OR a permanent IAM permissions issue.")
            return "API_DISABLED_OR_NO_PERMISSION"
        else:
            print(f"\nError: A clear Permission Denied error occurred. Message: {e.message}")
            return "PERMISSION_DENIED"
    except Exception as e:
        print(f"\nAn unexpected error occurred while fetching accounts: {e}")
        return "UNEXPECTED_ERROR"

def link_project_to_billing(client, target_project_id, billing_account_info):
    """Links a project and then verifies that the link is active."""
    if not target_project_id:
        print("\nError: Cannot link project to billing. The provided Project ID is empty.")
        return
    project_name = f"projects/{target_project_id}"
    billing_account_name = billing_account_info.name
    try:
        print(f"\nChecking current billing status for project '{target_project_id}'...")
        current_billing_info = client.get_project_billing_info(name=project_name)
        if current_billing_info.billing_account_name == billing_account_name:
            print(f"Success: Project is already linked to the target billing account '{billing_account_info.display_name}'.")
            return
        if current_billing_info.billing_enabled:
             print(f"Project is currently linked to a different billing account: '{current_billing_info.billing_account_name}'")
    except exceptions.NotFound:
        print("Project is not currently linked to any billing account.")

    print(f"Proceeding to link project to '{billing_account_info.display_name}' ({billing_account_name}).")
    project_billing_info = billing_v1.ProjectBillingInfo(billing_account_name=billing_account_name)

    try:
        client.update_project_billing_info(name=project_name, project_billing_info=project_billing_info)
        print(f"\nSuccessfully sent link request.")
    except exceptions.PermissionDenied as e:
        print(f"\nError: Permission Denied. You may not have 'roles/billing.projectManager' on the project. Message: {e.message}")
        return
    except Exception as e:
        print(f"\nAn unexpected error occurred during the linking process: {e}")
        return

    print("Now, verifying that the billing link is active...")
    max_retries = 6
    wait_seconds = 10
    for i in range(max_retries):
        try:
            verified_info = client.get_project_billing_info(name=project_name)
            if verified_info.billing_account_name == billing_account_name and verified_info.billing_enabled:
                print(f"Success! Billing link for project '{target_project_id}' is confirmed active.")
                return
            print(f"Verification attempt {i+1}/{max_retries}: Link not active yet.")
        except Exception as e:
            print(f"An unexpected error occurred during verification: {e}")
        time.sleep(wait_seconds)
    print(f"\nWarning: Could not verify billing link was active after {max_retries} attempts.")


# --- MAIN BLOCK ---

if __name__ == "__main__":
    print("--- Starting GCP Billing Management Script ---")
    project_id = get_project_id_from_file()

    if not project_id:
        print("\nScript finished with a critical error: Could not determine Project ID.")
    else:
        billing_client = billing_v1.CloudBillingClient()
        accounts_result = get_billing_accounts(billing_client)

        if accounts_result == "API_DISABLED_OR_NO_PERMISSION":
            print("\nAttempting to enable the Billing API and retry...")
            if enable_billing_api(project_id):
                max_retries = 5
                wait_seconds = 15
                for i in range(max_retries):
                    print(f"\nWaiting for API/permissions to propagate. Retrying in {wait_seconds} seconds... (Attempt {i+1}/{max_retries})")
                    time.sleep(wait_seconds)
                    accounts_result = get_billing_accounts(billing_client)
                    if accounts_result != "API_DISABLED_OR_NO_PERMISSION":
                        print("API is now active!")
                        break
                    wait_seconds *= 1.5

        if isinstance(accounts_result, list) and not accounts_result:
            print("\nNo billing accounts found immediately. This might be a propagation delay.")
            print("Will check again every 20 seconds for 2 minutes...")
            max_wait_retries = 6
            for i in range(max_wait_retries):
                print(f"Waiting... (Attempt {i+1}/{max_wait_retries})")
                time.sleep(20)
                accounts_result = get_billing_accounts(billing_client)
                if isinstance(accounts_result, list) and accounts_result:
                    print("Success! Found billing accounts after a delay.")
                    break

        if isinstance(accounts_result, list):
            if not accounts_result:
                # --- THIS IS THE NEW, CODELAB-SPECIFIC MESSAGE ---
                print("\n----------------- ACTION REQUIRED -----------------")
                print("Waited for 2 minutes, but no active billing account was found for your user.")
                print("This usually happens if the free trial credit for this event has not been")
                print("activated or is still being processed.")
                print("\n**Next Steps:**")
                print("  1. Please double-check the instructions from the event organizer and ensure")
                print("     you have CLAIMED YOUR CREDIT.")
                print("  2. If you have just claimed it, please wait another minute for it to apply.")
                print("  3. Once confirmed, please run the `./init.sh` script again.")
                print("---------------------------------------------------")
            else:
                open_accounts = [acc for acc in accounts_result if acc.open]
                if not open_accounts:
                    print("\nFound billing accounts, but none are currently open.")
                else:
                    target_account = open_accounts[0]
                    print("\n--- Found Active Billing Accounts ---")
                    print(f"Selected the first open account as the target: '{target_account.display_name}'")
                    link_project_to_billing(billing_client, project_id, target_account)

        elif accounts_result == "API_DISABLED_OR_NO_PERMISSION":
            print("\nScript finished with an unrecoverable error: The Billing API did not become active or you have a permissions issue.")
            print("Please manually verify the IAM role 'Billing Account User' is granted on the Organization.")
        else:
            print("\nScript finished with an unrecoverable error. Please review the logs above.")
