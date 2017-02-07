__author__ = 'Patrizio Tufarolo'
__email__ = 'patrizio.tufarolo@moon-cloud.eu'

import paramiko
import StringIO
from driver import Driver
import json

class SSHClient(object):
    def ssh_connect(self, hostname, port, username, password=None, private_key=None, private_key_passphrase=None):
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if private_key:
            private_key = paramiko.RSAKey.from_private_key(private_key, password=private_key_passphrase)
        ssh_client.connect(hostname, port, username=username, password=password, pkey=private_key)
        return ssh_client


class OpenstackPolicyControl(Driver,
                 SSHClient):

    policy_file = None
    policy_key = None
    policy_expected_value = None

    # Step 1 - Check prerequisites
    def prerequisites(self, inputs):
        retrieve_policy_configuration_ti = self.testinstances.get("retrieve_policy_file", None)
        if retrieve_policy_configuration_ti is not None:
            self.policy_file = retrieve_policy_configuration_ti.get("path", None)

        expected_ti = self.testinstances.get("inspect_policy_file", None)
        if expected_ti is not None:
            self.policy_key = expected_ti.get("key", None)
            self.policy_expected_value = expected_ti.get("expected_value", None)

        assert self.policy_file is not None and self.policy_key is not None
        return True

    # Step 2 - Connects to the remote server
    def connect_to_server(self, inputs):
        assert inputs is True
        ssh_connection_ti = self.testinstances.get("connect_to_server", None)

        assert not ssh_connection_ti is None

        hostname = ssh_connection_ti.get("hostname")
        port = ssh_connection_ti.get("port")
        username = ssh_connection_ti.get("username")
        password = ssh_connection_ti.get("password", None)
        private_key = ssh_connection_ti.get("private_key", None)
        if private_key is not None:
            private_key = StringIO.StringIO(private_key)
            private_key_passphrase = ssh_connection_ti.get("private_key_passphrase", None)

        assert not password is None or not private_key is None


        self.ssh_connection = self.ssh_connect(
            hostname=hostname,
            username=username,
            port=port,
            password=password,
            private_key=private_key,
            private_key_passphrase=private_key_passphrase
            )
        return True

    # Retrieves keystone configuration from remote server (OpenStack controller)
    def retrieve_policy_file(self, inputs):
        assert self.policy_file is not None
        _stdin, _stdout, _stderr = self.ssh_connection.exec_command("cat %s" % self.policy_file)
        lines = _stdout.readlines()
        return lines

    def inspect_policy_file(self, lines):
        policies = '\n'.join(lines)
        parsed_policies = json.loads(policies)
        return parsed_policies.get(self.policy_key) == self.policy_expected_value

    def close_ssh_connection(self, inputs):
        try:
            self.ssh_connection.close()
        except:
            pass
        return inputs


    def appendAtomics(self):
        self.appendAtomic(self.prerequisites, lambda: None)
        self.appendAtomic(self.connect_to_server, self.close_ssh_connection)
        self.appendAtomic(self.retrieve_policy_file, lambda: None)
        self.appendAtomic(self.inspect_policy_file, lambda: None)
        self.appendAtomic(self.close_ssh_connection, lambda: None)