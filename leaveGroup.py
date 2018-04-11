import model
import argparse
import sys

parser = argparse.ArgumentParser(description='Group Membership Management');
parser.add_argument('--port', type=int, default=None, help='port number to delete from the group')
parser.add_argument('--groupName', type=str, default=None, help='group name from which node should leave')

args = parser.parse_args()

if not args.port:
    print("please provide port number to delete")
    sys.exit()

if not args.groupName:
    print("group name to identify node should leave which group")
    sys.exit()
# --------------- delete the node from particular group ----------------
dbConn = model.PyMongoModel()
collection = dbConn.getCollection("process_" + str(args.port))
groupCollection = dbConn.getCollection(str(args.groupName))

groupDoc = groupCollection.find_one()
doc = collection.find_one()
if groupDoc is not None:
    for member in groupDoc['viewOfMembership']:
        if member['address'] != args.port:
            collection = dbConn.getCollection("process_" + str(member['address']))
            collection.update({}, {'$pull': {'viewOfMembership': {'address': args.port}}}, True)

    groupCollection.update({}, {'$pull': {'viewOfMembership': {'address': args.port}}}, True)
    # collection.drop()
    collection = dbConn.getCollection("process_" + str(args.port))
    collection.update({}, {'$pull': {'viewOfMembership': {'groupName': member['groupName']}}}, True, True)
    print("------- Node left the group successfully -------")
else:
    print("-----no group found with the given name " + args.groupName + " ------")
