import bank_pb2
import pickle
import sys
import socket
import random
import threading
import time

sys.path.append('/home/phao3/protobuf/protobuf-3.4.0/python')

BRANCH_NAME = ""
BRANCH_BALANCE = 0
BRANCH_LIST = []
doTransfer = False
SNAPSHOTS = {}
isCapturing = False
currentSnapId = 1
MARKER_MSG = 1
isUpdate = True


def sendTransactions():
    global BRANCH_NAME
    global BRANCH_BALANCE
    global BRANCH_LIST
    global isUpdate

    while doTransfer:
        random_entry = random.choice(BRANCH_LIST)
        if BRANCH_BALANCE > 50:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((random_entry["ip"], random_entry["port"]))
            transfer = bank_pb2.Transfer()
            transfer.money = (BRANCH_BALANCE * random.randrange(1, 5)) / 100
            msg = bank_pb2.BranchMessage()
            msg.transfer.CopyFrom(transfer)

            BRANCH_BALANCE = BRANCH_BALANCE - transfer.money

            s.sendall(pickle.dumps(msg))
            s.close()
            
            if MARKER_MSG > 1 or isCapturing:
                isUpdate = True
            print "TRANSFERRING %s to %s...Remainging Balance: %s\n" % (
            str(transfer.money), str(random_entry["name"]), str(BRANCH_BALANCE))
        time.sleep(random.randrange(1, 5))


def object_to_dict(repeatedObject):
    global BRANCH_LIST

    for object in repeatedObject:
        d = {}
        for fields in object.ListFields():
            d[fields[0].name] = fields[1]
        if d["port"] != int(sys.argv[2]):
            BRANCH_LIST.append(d)


def getDestBranchName(ip):
    for br in BRANCH_LIST:
        if br['ip'] == ip:
            return br["name"]


if __name__ == '__main__':

    ip = socket.gethostbyname(socket.getfqdn())
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((ip, int(sys.argv[2])))
    server_socket.listen(5)
    print '\nWaiting for connection... Listening on %s:%s\n' % (str(ip), sys.argv[2])
    try:
        while True:
            client_connection, client_address = server_socket.accept()
            data = pickle.loads(client_connection.recv(1024))

            if isCapturing and data.WhichOneof('branch_message') == 'transfer':
                SNAPSHOTS[currentSnapId][getDestBranchName(str(client_address[0])) + "->" + sys.argv[1]].append(
                    data.transfer.money)

            print "\nMessage : %s\n" % str(data.WhichOneof('branch_message'))

            if data.WhichOneof('branch_message') == 'init_branch':
                BRANCH_NAME = sys.argv[1]
                BRANCH_BALANCE = data.init_branch.balance
                object_to_dict(data.init_branch.all_branches)
                doTransfer = True

                if len(BRANCH_LIST) > 0:
                    t = threading.Thread(target=sendTransactions, args=())
                    t.setDaemon(True)
                    t.start()
            elif data.WhichOneof('branch_message') == 'transfer':
                BRANCH_BALANCE = BRANCH_BALANCE + data.transfer.money
                print "Received Amount %s from %s...Total Balance is %s\n" % (
                str(data.transfer.money), str(client_address[0]), str(BRANCH_BALANCE))
                
                if MARKER_MSG > 1 or isCapturing:
                    isUpdate = False
            elif data.WhichOneof('branch_message') == 'init_snapshot':
                currentSnapId = data.init_snapshot.snapshot_id
                SNAPSHOTS[currentSnapId] = {}
                SNAPSHOTS[currentSnapId][sys.argv[1]] = BRANCH_BALANCE

                for branch in BRANCH_LIST:
                    SNAPSHOTS[currentSnapId][branch["name"] + "->" + sys.argv[1]] = []

                marker_msg = bank_pb2.Marker()
                marker_msg.snapshot_id = data.init_snapshot.snapshot_id
                msg = bank_pb2.BranchMessage()
                msg.marker.CopyFrom(marker_msg)

                for branch in BRANCH_LIST:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect((branch["ip"], branch["port"]))
                    s.sendall(pickle.dumps(msg))
                    s.close()

                isCapturing = True
            elif data.WhichOneof('branch_message') == 'marker':
                if MARKER_MSG == 1:
                    MARKER_MSG = MARKER_MSG + 1
                    if not isCapturing:
                        currentSnapId = data.marker.snapshot_id
                        SNAPSHOTS[currentSnapId] = {}
                        SNAPSHOTS[currentSnapId][sys.argv[1]] = BRANCH_BALANCE

                        for branch in BRANCH_LIST:
                            SNAPSHOTS[currentSnapId][branch["name"] + "->" + sys.argv[1]] = []

                        marker_msg = bank_pb2.Marker()
                        marker_msg.snapshot_id = data.marker.snapshot_id
                        msg = bank_pb2.BranchMessage()
                        msg.marker.CopyFrom(marker_msg)

                        for branch in BRANCH_LIST:
                            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            s.connect((branch["ip"], branch["port"]))
                            s.sendall(pickle.dumps(msg))
                            s.close()

                        isCapturing = True
                elif MARKER_MSG == len(BRANCH_LIST):
                    isCapturing = False
                    MARKER_MSG = 1
                    isUpdate = False
                    print "\n\nSnapShots captured : %s \n\n" % str(SNAPSHOTS[data.marker.snapshot_id])
                else:
                    MARKER_MSG = MARKER_MSG + 1

                if isUpdate:
                    SNAPSHOTS[currentSnapId][sys.argv[1]] = BRANCH_BALANCE
            elif data.WhichOneof('branch_message') == 'retrieve_snapshot':
                snap_shot_obj = bank_pb2.ReturnSnapshot()
                snap_shot_obj.local_snapshot.snapshot_id = data.retrieve_snapshot.snapshot_id
                snap_shot_obj.local_snapshot.balance = SNAPSHOTS[data.retrieve_snapshot.snapshot_id][str(sys.argv[1])]
                for k, v in SNAPSHOTS[data.retrieve_snapshot.snapshot_id].iteritems():
                    if k != str(sys.argv[1]):
                        if len(v) == 0:
                            snap_shot_obj.local_snapshot.channel_state.append(0)
                        else:
                            for val in v:
                                snap_shot_obj.local_snapshot.channel_state.append(val)
                msg = bank_pb2.BranchMessage()
                msg.return_snapshot.CopyFrom(snap_shot_obj)
                print "Returning Snapshot : ", msg
                client_connection.sendall(pickle.dumps(msg))

    except KeyboardInterrupt:
        print "\nServer Stopped.....\n"
        doTransfer = False
        server_socket.close()
