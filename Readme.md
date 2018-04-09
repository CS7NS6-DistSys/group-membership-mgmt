

# Group Membership Management for Distributed Systems

A group membership management service that provides the (remaining) members of 
a group with a consistent view of its membership at any time and that tolerates 
the full range of failures that commonly arise in distributed systems, e.g., 
node or process failure, loss messages, and/or network partitions etc, etc.

*CA - CS7NS6 Distributed Systems*

To Create the group:
python main.py --isCoordinator True --coordinatorPort <portNumber> --groupName <groupName>
eg.
python main.py --isCoordinator True --coordinatorPort 10000 --groupName G1

To Add member to Group:
python main.py --port <portNumber> --groupName <GroupName>
eg.
python main.py --port 10001 --groupName G1

To Leave member from Group
python leaveGroup.py --port <portNumber> --groupName <GroupName>
eg
python leaveGroup.py --port 10001 --groupName G1