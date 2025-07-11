# oci_bastion_session_connector
This tool makes the OCI Bastion service simple to use - no console login required - just run the interactive script from your terminal, then paste the ssh command that is copied to your clipboard!

## Configuration
To begin, ensure there is a bastion in the target subnet.

In the python code, edit values in the --- Configuration --- section
- TARGET_SERVERS list: replace "ocid1.instance.oc1...." with the OCID of the server you want to connect to through the bastion. Multiple servers can be added
- BASTION_OCID: replace "ocid1.bastion.oc1...." with the OCID of your created bastion
- DEFAULT_SSH_USER: linux user to ssh as
  - Oracle Linux default is "opc"
  - Ubuntu default is "ubuntu"
- PUBLIC_KEY_PATH: replace "~/path/to/public_key.pub" with the path to your public key
- PRIVATE_KEY_PATH: replace "~/path/to/private_key" with the path to your private key


## Python Environment Setup
To setup a virtual environment and install the requirements:

- python3 -m venv bastion_env
- source bastion_env/bin/activate
- pip install -r requirements.txt
- python3 bastion_session_creator.py
