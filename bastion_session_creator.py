"""
Finds or creates an OCI Bastion session for a target compute instance.

This script performs the following actions:
1.  Checks for an existing, active, bastion session for the specified target server.
2.  If an active session is found, it is reused.
3.  If not, a new session is created.
4.  Once the new session is active, the SSH command is retrieved.
5.  Constructs the full SSH command to connect to the instance.
5.  Copies the SSH command to the clipboard and prints it to the console.
"""

import oci
import pyperclip
import sys
import os

# --- Configuration ---
# Add friendly names and OCIDs for your servers here.
TARGET_SERVERS = {
    "server1": "ocid1.instance.oc1....",
    "server2": "ocid1.instance.oc1....",
}

BASTION_OCID = "ocid1.bastion.oc1...."
DEFAULT_SSH_USER = ""
SESSION_TTL_SECONDS = 1800

PRIVATE_KEY_PATH = os.path.expanduser("~/path/to/private_key")
PUBLIC_KEY_PATH = os.path.expanduser("~/path/to/public_key.pub")
# --- End Configuration ---

def read_public_key(path):
    """Reads the public key content from a file."""
    try:
        with open(path, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"❌ Error: Public key file not found at {path}")
        print("Please ensure an SSH key pair exists at the specified location.")
        sys.exit(1)


def find_active_session(bastion_client, bastion_ocid, target_ocid):
    """Checks for an existing, active session for the target server."""
    print(f"Checking for active bastion sessions for server: {target_ocid}...")
    try:
        active_sessions = bastion_client.list_sessions(
            bastion_id=bastion_ocid,
            session_lifecycle_state='ACTIVE'
        ).data

        for session in active_sessions:
            if session.target_resource_details.target_resource_id == target_ocid:
                print(f"✅ Found active session: {session.id}")
                return bastion_client.get_session(session_id=session.id).data
        return None
    except oci.exceptions.ServiceError as e:
        print(f"❌ Error checking for sessions: {e.message}")
        sys.exit(1)

def create_new_session(bastion_client:oci.bastion.BastionClient, bastion_ocid, target_ocid, public_key, user, ttl):
    """Creates a new session and waits for it to become active."""
    print("No active session found. Creating a new session...")
    try:
        create_details = oci.bastion.models.CreateSessionDetails(
            bastion_id=bastion_ocid,
            target_resource_details=oci.bastion.models.CreateManagedSshSessionTargetResourceDetails(
                session_type="MANAGED_SSH",
                target_resource_id=target_ocid,
                target_resource_operating_system_user_name=user
            ),
            key_details=oci.bastion.models.PublicKeyDetails(public_key_content=public_key),
            session_ttl_in_seconds=ttl,
        )
        bastion_response:oci.response.Response = bastion_client.create_session(create_session_details=create_details)
        new_session_id = bastion_response.data.id

        print(f"Waiting for new session {new_session_id} to become active...")
        get_session_info = bastion_client.get_session(session_id=new_session_id)
        wait_until_session_available_response = oci.wait_until(
            bastion_client,
            get_session_info,
            'lifecycle_state',
            'ACTIVE',
            max_interval_seconds=10,
            max_wait_seconds=120
            )
        active_session = wait_until_session_available_response.data
        print(f"✅ New session {active_session.id} is active.")
        return active_session
    except oci.exceptions.ServiceError as e:
        print(f"❌ Error creating session: {e.message}")
        sys.exit(1)


def select_target_server():
    """Prompts the user to select a target server from a numbered list."""
    print("Please select a server to connect to:")
    server_list = list(TARGET_SERVERS.keys())
    for i, server_name in enumerate(server_list):
        print(f"  {i + 1}: {server_name}")

    while True:
        try:
            choice = input(f"\nEnter a number (1-{len(server_list)}): ")
            choice_index = int(choice) - 1
            if 0 <= choice_index < len(server_list):
                selected_server_name = server_list[choice_index]
                print(f"--> You selected: {selected_server_name}\n")
                return TARGET_SERVERS[selected_server_name]
            else:
                print(f"❌ Invalid selection. Please enter a number between 1 and {len(server_list)}.")
        except ValueError:
            print("❌ Invalid input. Please enter a number.")
        except (KeyboardInterrupt, EOFError):
            print("\n\nSelection cancelled. Exiting.")
            sys.exit(0)


def main():
    """Main function to orchestrate bastion session creation."""
    target_server_ocid = select_target_server()

    try:
        config = oci.config.from_file()
        bastion_client = oci.bastion.BastionClient(config)
    except oci.exceptions.ConfigFileNotFound:
        print("❌ Error: Default OCI config file not found at ~/.oci/config")
        print("Please run 'oci setup config' to configure your environment.")
        sys.exit(1)

    session = find_active_session(bastion_client, BASTION_OCID, target_server_ocid)

    if not session:
        public_key_content = read_public_key(PUBLIC_KEY_PATH)
        session = create_new_session(
            bastion_client, BASTION_OCID, target_server_ocid,
            public_key_content, DEFAULT_SSH_USER, SESSION_TTL_SECONDS
        )

    if not session or "command" not in session.ssh_metadata:
        print("❌ Error: Could not retrieve SSH command from the session.")
        sys.exit(1)

    ssh_command = session.ssh_metadata["command"]
    ssh_command = ssh_command.replace("<privateKey>", PRIVATE_KEY_PATH)

    pyperclip.copy(ssh_command)

    print("\n" + "="*60)
    print("🎉 Success! Your SSH command is ready.")
    print("✅ It has been copied to your clipboard.")
    print("="*60)
    print("\nPaste it into your terminal to connect:\n")
    print(f"{ssh_command}\n")


if __name__ == "__main__":
    main()
