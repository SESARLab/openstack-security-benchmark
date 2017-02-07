# Moon Cloud - Central Directory for Authentication and Authorization for the cloud profile	

Profile: Cloud

ToE: OpenStack Keystone. We note that Keystone offers
the possibility to be integrated with an external identity access management.
Control: The control verify that Keystone is configured to use the company internal LDAP. The Keystone configuration is defined in every node where keystone is running. Keystone nodes can be retrieved by OpenStack API or specifying manually their IP addresses. The control needs to access to all nodes running Keystone and control that the key- stone.configuration contains all necessary key-value to be connected to the internal authentication system.

The execution flow φ consists of three sequential opera- tions with the relative Parameters λ as follows.

	1. connect_to_server [username, password, private_key, private_key_passphrase, hostname, port]: connect ssh to the Keystone nodes.
	2. retrieve_keystone_configuration [keystone_config_file(optional)]: read from the Keystone conifig placed in /etc/keystone/keystone.conf if keystone_config_file is not passed.
	3. textitcheck_ldap [ldap_url]: the control check the the ldap driver is enabled and check the the required ldap is configured correctly

The Environmental settings π are the following:

	- The control must be executed with access to the internal network.
	- The OpenStack python configuration library to be able to parse OpenStack configurations.
	- The paramiko python library to let the control access through ssh.