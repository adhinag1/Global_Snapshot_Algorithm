import bank_pb2
import pickle
import sys
import socket
import time
import random

sys.path.append('/home/phao3/protobuf/protobuf-3.4.0/python')

BRANCH_LIST = []
SNAPSHOTS = {}

def parseBranchDetails(input_file):
    global BRANCH_LIST

    keys = ["name", "ip", "port"]
    with open("./" + input_file) as f:
        for line in f:
            if line.strip():
                pair = filter(None, line.strip().split(" "))
                d = {}
                for x in range(0, len(pair)):
                    if keys[x] == "port":
                        d[keys[x]] = int(pair[x])
                    else:
                        d[keys[x]] = str(pair[x])
                BRANCH_LIST.append(d)


if __name__ == '__main__':
    parseBranchDetails(str(sys.argv[2]))
    snap_id = 0
    try:
        while True:
            if len(SNAPSHOTS) == 0:
                remaining = int(sys.argv[1]) % len(BRANCH_LIST)
                for branch in BRANCH_LIST:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    print "Initializing Branch: %s\n" % str(branch["name"])
                    s.connect((branch['ip'], branch['port']))

                    initMsg = bank_pb2.InitBranch()
                    if remaining == 0:
                        initMsg.balance = int(sys.argv[1]) / len(BRANCH_LIST)
                    else:
                        initMsg.balance = int(sys.argv[1]) / len(BRANCH_LIST) + remaining
                        remaining = 0
                        
                    for b in BRANCH_LIST:
                        branches = initMsg.all_branches.add()
                        branches.name = b['name']
                        branches.ip = b['ip']
                        branches.port = b['port']

                    msg = bank_pb2.BranchMessage()
                    msg.init_branch.CopyFrom(initMsg)

                    s.sendall(pickle.dumps(msg))
                    s.close()

            time.sleep(2)

            random_entry = random.choice(BRANCH_LIST)
            print "Initiated snapshot message to %s\n" % str(random_entry["name"])
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((random_entry['ip'], random_entry['port']))
            initSnap = bank_pb2.InitSnapshot()
            initSnap.snapshot_id = snap_id + 1
            msg = bank_pb2.BranchMessage()
            msg.init_snapshot.CopyFrom(initSnap)
            s.sendall(pickle.dumps(msg))
            s.close()

            time.sleep(4)

            retrieveSnap = bank_pb2.RetrieveSnapshot()
            retrieveSnap.snapshot_id = snap_id + 1
            msg1 = bank_pb2.BranchMessage()
            msg1.retrieve_snapshot.CopyFrom(retrieveSnap)
            
            for b in BRANCH_LIST:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((b['ip'], b['port']))
                s.sendall(pickle.dumps(msg1))
                data = pickle.loads(s.recv(1024))

                if data.WhichOneof('branch_message') == 'return_snapshot':
                    d = {}
                    f = {}
                    l = []
                    to_branch = b['name']
                    for branch in BRANCH_LIST:
                        if branch["name"] != to_branch:
                            l.append(branch["name"])
                    for fields in data.return_snapshot.local_snapshot.ListFields():
                        if fields[0].name == 'channel_state':
                            for i in range(0, len(fields[1])):
                                d[l[i] + "->" + to_branch] = int(fields[1][i])
                        else:
                            d[fields[0].name] = fields[1]
                    f[to_branch] = d

                    try:
                        SNAPSHOTS[retrieveSnap.snapshot_id].update(f)
                    except KeyError:
                        SNAPSHOTS[retrieveSnap.snapshot_id] = f

            print "snapshot_id: %s" % str(retrieveSnap.snapshot_id)
            for key in SNAPSHOTS[retrieveSnap.snapshot_id].keys():
                format = ""
                format = format + str(key) + ": " + str(SNAPSHOTS[retrieveSnap.snapshot_id][key]['balance']) + ", "
                for key, val in SNAPSHOTS[retrieveSnap.snapshot_id][key].iteritems():
                    if key not in ["balance", "snapshot_id"]:
                        format = format + str(key) + ": " + str(val) + ", "
                print format.strip(", ")

            snap_id += 1
            print "\n\n"
    except KeyboardInterrupt:
        print "\nServer Stopped.....\n"
