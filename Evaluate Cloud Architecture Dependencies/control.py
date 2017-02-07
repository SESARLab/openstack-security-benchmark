__author__ = 'Patrizio Tufarolo'
__email__ = 'patrizio.tufarolo@moon-cloud.eu'

import paramiko
import re
import StringIO
from driver import Driver
from oslo_config import cfg

class SSHClient(object):
    def ssh_connect(self, hostname, port, username, password=None, private_key=None, private_key_passphrase=None):
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if private_key:
            private_key = paramiko.RSAKey.from_private_key(private_key, password=private_key_passphrase)
        ssh_client.connect(hostname, port, username=username, password=password, pkey=private_key)
        return ssh_client

class MyConfigParser(cfg.ConfigParser):
    def __init__(self, filename, ldap_config):
        super(cfg.ConfigParser, self).__init__()
        self.sections = {}
        self._normalized = None
        self.section = None
        self.ldap_config = ldap_config
        self.filename = filename

    def parse(self):
        return super(cfg.ConfigParser, self).parse(self.ldap_config)

class CinderNovaEncryptedFixedKey(Driver,
                 SSHClient):

    keystone_config_file = None
    # Step 1 - Check prerequisites
    def prerequisites(self, inputs):
        self.nova_config_file = "/etc/nova/nova.conf"
        self.cinder_config_file = "/etc/cinder/cinder.conf"

        retrieve_services_configurations_ti = self.testinstances.get("retrieve_services_configurations", None)

        if retrieve_services_configurations_ti is not None:
            self.nova_config_file = retrieve_nova_configuration_ti.get("nova_config_path", self.nova_config_file)
            self.cinder_config_file = retrieve_cinder_configuration_ti.get("cinder_config_path", self.cinder_config_file)

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

    # Retrieves nova configuration from remote server (OpenStack controller)
    def retrieve_nova_configuration(self):
        assert self.nova_config_file is not None
        _stdin, _stdout, _stderr = self.ssh_connection.exec_command("cat %s" % self.nova_config_file)
        lines = _stdout.readlines()
        return lines

    # Retrieves cinder configuration from remote server (OpenStack controller)
    def retrieve_cinder_configuration(self):
        assert self.cinder_config_file is not None
        _stdin, _stdout, _stderr = self.ssh_connection.exec_command("cat %s" % self.cinder_config_file)
        lines = _stdout.readlines()
        return lines

    def retrieve_services_configurations(self, inputs):
        return self.retrieve_nova_configuration(), self.retrieve_cinder_configuration()

    def check_strength(self, passphrase):
        classes = {}
        classes["alphabetic_class"] = "[A-z]"
        classes["numeric_class"] = "[0-9]"
        classes["symbol_class "]= "[!@#$%^&*()_\+\|\~\-=`\\\\{\}\[\]:\";'<>?,./]"
        count = 0
        for single_class in classes:
            if re.search(classes[single_class], passphrase) is not None:
                count += 1
        return len(passphrase) >= 9 and count >= 2

    def check_fixed_key_nova(self, nova_config):
        mcp = MyConfigParser(self.nova_config_file, nova_config)
        mcp.parse()
        section = mcp.sections.get("key_manager", mcp.sections.get("keymgr", None))
        assert section is not None
        fixed_key = section.get("fixed_key")[0]
        assert fixed_key is not None
        return self.check_strength(fixed_key)

    def check_fixed_key_cinder(self, cinder_config):
        mcp = MyConfigParser(self.cinder_config_file, cinder_config)
        mcp.parse()
        section = mcp.sections.get("key_manager", mcp.sections.get("keymgr", None))
        assert section is not None
        fixed_key = section.get("fixed_key")[0]
        assert fixed_key is not None
        return self.check_strength(fixed_key)

    def check_fixed_keys(self, inputs):
        nova_config, cinder_config = inputs
        return self.check_fixed_key_cinder(cinder_config) and self.check_fixed_key_nova(nova_config)

    def close_ssh_connection(self, inputs):
        try:
            self.ssh_connection.close()
        except:
            pass
        return inputs


    def appendAtomics(self):
        self.appendAtomic(self.prerequisites, lambda: None)
        self.appendAtomic(self.connect_to_server, self.close_ssh_connection)
        self.appendAtomic(self.retrieve_services_configurations, lambda:None)
        self.appendAtomic(self.check_fixed_keys, lambda: None)
        self.appendAtomic(self.close_ssh_connection, lambda: None)
