# Moon Cloud - Do Not Use or Set Guest Customization Passwords for the User Profile

Profile: Cloud.

ToE: Openstack Keystone. Keystone is the identity service and manages projects, users and groups.
Control Admin can’t be member of any projects, excepts her owns projects and can’t change users passords. Hence, the control is double: i) admin user is only member of a restricted list of project as specified in a list. The openstack policy doens’t allows to change user password and that should be changed only through the centralized identity system.

The execution flow φ of control i) consists of two sequen-
tial operations with the relative Parameters λ as follows.
	1. openstack_connection [os_username, os_password, os_project_id, os_auth_url, os_user_domain_name]: using the admin credentials, control connects to OpenStack API
	2. checkProject [project_list]: control parses all projects and control admin is member only of the passed projects.

The Environmental settings π are the following:

	- Control must be executed with access to the public OpenStack API.
	- The OpenStack client SDK to be able to communicate with its API.




The execution flow φ of control ii) consists of two sequen- tial operations with the relative Parameters λ as follows.
		1. connect_to_server [username, password, private_key, private_key_passphrase, hostname, port]: control ac- cesses through ssh the Keystone nodes.
		2. retrieve_policy_file[path]:controlreadsandparsesthe policy file.
		3. inspect_policy_file [key, expected_value]: control checks that identity:change_password action is disabled.

The Environmental settings π are the following:

	- Control must be executed with access to the internal
network.
	- The paramiko python library to let the control access
through ssh.