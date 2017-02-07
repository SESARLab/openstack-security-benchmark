# Moon Cloud - Evaluate Cloud Architecture Dependencies

Profile: User.

ToE: Nova computing and user VMs
Control User can mitigate the dependencies from single point of failure of a cloud by deploying her VMs in different availability zone; hence, the control checks that a set of VM are at least deployed in two different availability zone.

The execution flow φ of the first Controls C1 consists of three sequential operations with the relative Parameters λ as follows.

	1. openstack-connection [user credentials]: using user credentials to access OpenStack API
	2. retrieve-zone []: control retrieves all availability zones in OpenStack.
	3. check-deployment[vm-list]:controlchecksthatatleast one VM from vm-list is deployed in a different avail- ability zone.
The Environmental settings π are the following:

	- Control must be executed with access to the public OpenStack API.
	- The OpenStack client SDK to be able to communicate with its API.