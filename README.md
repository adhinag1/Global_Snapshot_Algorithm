# Global_Snapshot_Algorithm

Implement a distributed banking application based on Chandy Lamport Snapshot Algorithm using Google ProtoBuf and Sockets in python. The distributed bank has multiple branches. Every branch knows about all other branches. A single TCP connection is setup between every pair of branches. Each branch starts with an initial balance. The branch then randomly selects another destination branch and sends a random amount of money to this destination branch at unpredictable times.

A controller to set a branch’s initial balance and notify every branch of all branches in the distributed bank. This controller takes two command line inputs: the total amount of money in the distributed bank and a local file that stores the names, IP addresses, and port numbers of all branches. An example of how the controller program should operate is provided below:

> ./controller 4000 branches.txt

The file (branches.txt) should contain a list of names, IP addresses, and ports, in the format “<name> <public-ip-address> <port>”, of all of the running branches.

I used the Chandy-Lamport global snapshot algorithm take global snapshots of your bank. In case of the distributed bank, a global snapshot will contain both the local state of each branch (i.e., its balance) and the amount of money in transit on all communication channels. Each branch will be responsible for recording and reporting its own local state (balance) as well as the total money in transit on each of its incoming channels. It does so by sending a message indicating the InitSnapshot operation to the selected branch. The selected branch will then initiate the snapshot by first recording its own local state and send out Marker messages to all other branches. After some time (long enough for the snapshot algorithm to finish), the controller sends RetrieveSnapshot messages to all branches to retrieve their recorded local and channel states. If the snapshot is correct, the total amount of money in all branches and in transit should equal to the command line argument given to the controller.

For simplicity, in this assignment, the controller will contact one of the branches to initiate the global snapshot

## Steps to run:
1) Run the branch server using "./branch <branch_name> <port_arg>" script.
2) Run the controller using "./controller <total_balance> <input_file>" script.
3) Branch and Controller will start
4) Controller will automatically initiate the branches and capture snapshot periodically.
5) Captured Snapshot will be printed on controller's syso.

