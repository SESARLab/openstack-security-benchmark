__author__ = 'Filippo Gaudenzi'
__email__ = 'filippo.gaudenzi@moon-cloud.eu'


from novaclient.client import Client as NovaClient
from keystoneauth1.identity import v3 as KeystoneClient
from keystoneauth1 import session as KeystoneSession
from keystoneclient.v3 import client
from driver import Driver






class members(Driver):
    def openstackConfig(self, inputs):
        self.keystonecl = KeystoneClient.Password(auth_url=self.testinstances["openstackConfig"]["OS_AUTH_URL"],
						username=self.testinstances["openstackConfig"]["OS_USERNAME"],
						password=self.testinstances["openstackConfig"]["OS_PASSWORD"],
						project_id=self.testinstances["openstackConfig"]["OS_PROJECT_ID"],
						user_domain_name=self.testinstances["openstackConfig"]["OS_USER_DOMAIN_NAME"])
        sess = KeystoneSession.Session(auth=self.keystonecl)
        keystone = client.Client(session=sess)
        return keystone

    def checkProject(self,keystone):
        elem=self.testinstances["checkProject"]
        members=elem.get("members")
        project=elem.get("project")
        users=keystone.users.list(default_project=project)
        m=0
        for u in users:
            projects = keystone.projects.list(user=u.id)
            for p in projects:
                if p.name == project:
                    if not u.id in members:
                        return False
                    else:
                        m=m+1
        if m == len(members):
            return True
        else:
            return False


    def appendAtomics(self):
        self.appendAtomic(self.openstackConfig, lambda:None)
        self.appendAtomic(self.checkProject,lambda:None)