# Moon Cloud - Do Not Use or Set Guest Customization Passwords for the User Profile

Profile: (Virtual)

ToE: All nodes that compose the OpenStack deployment. Control: The control needs to access every node and checks if the time synchronisation is enabled and if it is connected to the same server list as required. The control supports both crony and ntp.

The execution flow φ consists of three sequential opera- tions with the relative Parameters λ as follows.

	1. connect_to_server [username, password, private_key, private_key_passphrase,hostname, port]: control ac- cesses trough ssh the node;
	2. check_timesync_enabled [ntp,chrony]: control checks, using the init system, if crony or ntp is enabled;
	3. check_timesync_config [ntp_config_file (optional),chrony_config_file (optional),servers_list]: control checks that servers list in the crony or ntp config file are the same as passed in the parameters.
The Environmental settings π are the following:

	-Control must be executed with access to the internal network
	-The paramiko python library to let the control access through ssh.
