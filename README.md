# Lambda-Failover-DX-VPN-AWS

This code is designed to run on AWS Lambda to act as a failover from a Direct Connect connection to a VPN that terminates at a third-party firewall (the VPN terminates at the appliance).

Since the infrastructure used has a default route that goes through a gateway load balancer—which in turn uses GENEVE for all communication—the VPN, when using this path and being encapsulated by GENEVE, causes the packet to arrive with an issue.

Therefore, the script monitors the status of the Direct Connect in a specific region (in my case, sa-east-1) and updates the routing table in another region (us-east-1). Before the packet is sent to the GENEVE tunnel and then to the Direct Connect, it changes the target and directs it to another endpoint (in this case, the appliance that terminates the VPN).
