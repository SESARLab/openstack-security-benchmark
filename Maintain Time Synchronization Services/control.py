__author__ = 'Patrizio Tufarolo'
__email__ = 'patrizio.tufarolo@moon-cloud.eu'

import paramiko
import StringIO
from driver import Driver


class SSHClient(object):
    def ssh_connect(self, hostname, port, username, password=None, private_key=None, private_key_passphrase=None):
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if private_key:
            private_key = paramiko.RSAKey.from_private_key(private_key, password=private_key_passphrase)
        ssh_client.connect(hostname, port, username=username, password=password, pkey=private_key)
        return ssh_client


class NtpControl(Driver,
                 SSHClient):
    def check_init_system(self, init_system):
        """
        Returns the command to check whether init process is systemd, upstart or system 5 init
        """
        if init_system == "systemd":
            return """ bash -c "[[ `systemctl` =~ -\.mount ]] && echo 1 || echo 0 " """
        elif init_system == "upstart":
            return """ bash -c "[[ `/sbin/init --version` =~ upstart ]] && echo 1 || echo 0 " """
        elif init_system == "sysvinit":
            return """ bash -c "[[ -f /sbin/init && ! -L /sbin/init ]] && echo 1 || echo 0 " """
        return None

    def check_daemon_enabled(self, init_system, daemon):
        """
        If the init system is systemd, then returns systemctl is-enabled
        Else if the init system is upstart or sysvinit, then grabs the service status from service --status-all
        """
        if init_system == "systemd":
            return """ bash -c "systemctl is-enabled {}" """.format(daemon)
        elif init_system == "upstart" or init_system == "sysvinit":
            return """ bash -c "[[ $(/usr/sbin/service --status-all 2>1 | awk '/%s$/ {print $2}') == "+" ]] && echo 1 || echo 0" """ % daemon
        return None

    def check_service(self, connection, init_system, daemon):
        command = self.check_daemon_enabled(init_system, daemon)
        _stdin, _stdout, _stderr = connection.exec_command(command)
        out = _stdout.readlines()
        return len(out) > 0 and out[0].strip() == "1"

    def retrieve_time_servers_cmd(self, daemon="ntp", config_file=None):
        if not config_file:
            if daemon == "ntp":
                config_file = "/etc/ntp.conf"
            elif daemon == "chrony":
                config_file = "/etc/chrony.conf"

        return """ awk '/^server/ {print $2}' %s """ % config_file

    def retrieve_time_servers(self, connection, daemon="ntp", config_file=None):
        command = self.retrieve_time_servers_cmd(daemon, config_file)
        _stdin, _stdout, _stderr = connection.exec_command(command)
        out = _stdout.readlines()

        for line, s in enumerate(out):
            out[line] = str(s).strip()
        return out

    # Step 1 - Verify Preconditions
    def preconditions(self, inputs):
        # Verifies that the user has provided the list of the expected time servers

        expected_servers_list = []
        expected_ti = self.testinstances.get("check_timesync_config", None)
        if expected_ti is not None:
            expected_servers_list = expected_ti.get("servers_list")
        assert len(expected_servers_list) > 0
        self.expected_servers_list = expected_servers_list

        # Decides whether to check ntp or chrony. If no preference is provided in the config file, checks both of them
        check_ntp = False
        check_chrony = False

        # Grabs the testinstance for ntp settings
        ntp_settings_ti = self.testinstances.get("check_timesync_enabled", None)
        # Grabs the value of "check" for ntp
        if ntp_settings_ti is not None:
            check_ntp = ntp_settings_ti.get("check_ntp", False)

        # Grabs the testinstance for chrony settings
        chrony_settings_ti = self.testinstances.get("check_timesync_enabled", None)
        # Grabs the value of "check" for chrony
        if chrony_settings_ti is not None:
            check_chrony = chrony_settings_ti.get("check_chrony", False)

        # If both are false, it checks both.
        if check_ntp == False and check_chrony == False:
            check_ntp = True
            check_chrony = True

        self.check_ntp = check_ntp or False
        self.check_chrony = check_chrony or False
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

    # Step 3 - Identifies the init system used by the remote server
    def identify_init_system(self, inputs):
        assert inputs is True

        _stdin, _stdout, _stderr = self.ssh_connection.exec_command(self.check_init_system("systemd"))
        out = _stdout.readlines()
        if len(out) > 0 and out[0].strip() == "1":
            return "systemd"

        """
        Checks if init system is upstart
        """
        _stdin, _stdout, _stderr = self.ssh_connection.exec_command(self.check_init_system("upstart"))
        out = _stdout.readlines()

        if len(out) > 0 and out[0].strip() == "1":
            return "upstart"

        """
        Checks if init system is sysvinit
        """
        _stdin, _stdout, _stderr = self.ssh_connection.exec_command(self.check_init_system("sysvinit"))
        out = _stdout.readlines()
        if len(out) > 0 and out[0].strip() == "1":
            return "sysvinit"

    # Step 4 - Verifies that the init system is one of the supported ones (step2 returns a valid value)
    def verify_init_system(self, init_system):
        assert init_system in ("sysvinit", "systemd", "upstart", )
        return init_system

    def check_ntp_enabled(self, init_system):
        self.has_ntp = False
        if self.check_ntp:
            self.has_ntp = self.check_service(self.ssh_connection, init_system, "ntp")
        return init_system

    def check_chrony_enabled(self, init_system):
        self.has_chrony = False
        if self.check_chrony:
            self.has_chrony = self.check_service(self.ssh_connection, init_system, "chrony")
    
    def assert_ntp_or_chrony(self, inputs):
        assert self.has_chrony ^ self.has_ntp
        return True

    # Step 5 - Checks that at least one timesync service is enabled

    def check_timesync_enabled(self, init_system):
        self.check_ntp_enabled(init_system)
        self.check_chrony_enabled(init_system)
        return self.assert_ntp_or_chrony(None)


    def check_ntp_config(self, inputs):
        if self.has_ntp:
            ntp_settings_ti = self.testinstances.get("check_timesync_config", None)
            if ntp_settings_ti is not None:
                config_file = ntp_settings_ti.get("ntp_config_file", None)
                servers = self.retrieve_time_servers(self.ssh_connection, daemon="ntp", config_file=config_file)
                print(servers)
                return inputs and len(set(servers) & set(self.expected_servers_list)) == len(set(servers))
        
        return inputs

    def check_chrony_config(self, inputs):
        if self.has_chrony:
            chrony_settings_ti = self.testinstances.get("check_timesync_config", None)
            if chrony_settings_ti is not None:
                config_file = chrony_settings_ti.get("chrony_config_file", None)
                servers = self.retrieve_time_servers(self.ssh_connection , daemon="chrony", config_file=config_file)
                return inputs and len(set(servers) & set(self.expected_servers_list)) == len(set(servers))
        return inputs

    # Step 6 - Checks configurations for timesync services and compares the list with the provided one
    def check_timesync_config(self, inputs):
        ntp_config = self.check_ntp_config(inputs)
        return self.check_chrony_config(ntp_config)

    # Step 7 - Closes connection
    def close_ssh_connection(self, inputs):
        try:
            self.ssh_connection.close()
        except:
            pass
        return inputs


    def appendAtomics(self):
        self.appendAtomic(self.preconditions, lambda:None)
        self.appendAtomic(self.connect_to_server, self.close_ssh_connection)
        self.appendAtomic(self.identify_init_system, lambda: None)
        self.appendAtomic(self.verify_init_system, lambda: None)
        self.appendAtomic(self.check_timesync_enabled, lambda: None)
        self.appendAtomic(self.check_timesync_config, lambda: None)
        self.appendAtomic(self.close_ssh_connection, lambda: None)