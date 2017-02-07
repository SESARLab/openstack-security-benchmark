__author__ = 'Patrizio Tufarolo'
__email__ = 'patrizio.tufarolo@moon-cloud.eu'

import paramiko
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


class KeystoneLdapControl(Driver,
                 SSHClient):

    keystone_config_file = None
    # Step 1 - Check prerequisites
    def prerequisites(self, inputs):
        self.keystone_config_file = "/etc/keystone/keystone.conf"
        retrieve_keystone_configuration_ti = self.testinstances.get("retrieve_keystone_configuration", None)
        if retrieve_keystone_configuration_ti is not None:
            self.keystone_config_file = retrieve_keystone_configuration_ti.get("keystone_config_path", self.keystone_config_file)
        check_ldap_ti = self.testinstances.get("check_ldap")
        assert check_ldap_ti is not None
        self.ldap_url = check_ldap_ti.get("ldap_url")
        assert self.ldap_url is not None
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
    def retrieve_keystone_configuration(self, inputs):
        assert self.keystone_config_file is not None
        _stdin, _stdout, _stderr = self.ssh_connection.exec_command("cat %s" % self.keystone_config_file)
        lines = _stdout.readlines()
        return lines

    # Checks the identity driver specified to be ldap, and that the url of ldap
    # in the [ldap] section is the one specified in the control input
    # More checks can be added such as ldap query string
    def check_ldap(self, ldap_config):
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

        mcp = MyConfigParser(self.keystone_config_file, ldap_config)
        mcp.parse()
        assert mcp.sections.get("identity", None) is not None
        assert mcp.sections.get("ldap", None) is not None
        return mcp.sections.get("identity").get("driver") == "ldap" and mcp.sections.get("ldap").get("url") == self.ldap_url

    def close_ssh_connection(self, inputs):
        try:
            self.ssh_connection.close()
        except:
            pass
        return inputs


    def appendAtomics(self):
        self.appendAtomic(self.prerequisites, lambda: None)
        self.appendAtomic(self.connect_to_server, self.close_ssh_connection)
        self.appendAtomic(self.retrieve_keystone_configuration, lambda: None)
        self.appendAtomic(self.check_ldap, lambda: None)
        self.appendAtomic(self.close_ssh_connection, lambda: None)
