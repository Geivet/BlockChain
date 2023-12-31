import re
import sys
import math
import socket
import threading
import traceback
import blockchain

from os import _exit
from sys import stdout
from time import sleep
from blogApp import Blog
from blockchain import Blockchain, Block

# function that uses regex for command used for fixing and failing links
def check_command_letter_number(string, desired_command):
    pattern = r'({0})\(([A-Za-z])(\d+)\)'.format(desired_command)
    match = re.search(pattern, string)
    if match:
        command = match.group(1)
        letter = match.group(2)
        number = match.group(3)
        return command, letter, number
    return None

# function that uses regex for command used for extracting command and string
def extract_command_and_string(string, desired_command):
    pattern = r"({0})\((.*?)\)".format(desired_command)
    match = re.search(pattern, string)
    if match:
        command = match.group(1)
        extracted_string = match.group(2)
        return command, extracted_string
    return None

# function used for post and comment commands
def extract_fields_from_command(string, desired_command):
    pattern = r"({0})\((.*?), (.*?), (.*?)\)".format(desired_command)
    match = re.search(pattern, string)
    if match:
        command = match.group(1)
        username = match.group(2)
        title = match.group(3)
        content = match.group(4)
        return command, username, title, content
    return None

def get_userInput():
    # IMPLEMENT: file stuff goes here
    global leadID
    nodeBlockChainLogFileName = f"Node_{nodeID}_Blockchain_Log.txt"
    blogFile = f"Node_{nodeID}_Blog.txt"
        
    while True:
        userInput = input()                     # wait for user input
        splicedInput = userInput.split(" ")     # split user input into list of strings

        failLink = check_command_letter_number(userInput, "failLink")
        fixLink = check_command_letter_number(userInput, "fixLink")
        view = extract_command_and_string(userInput, "view")
        read = extract_command_and_string(userInput, "read")
        wait = extract_command_and_string(userInput, "wait")

        if  userInput == "crash":                       # crash the program
            inBoundSocket.close()                       # close all sockets before exiting
            print("Crashing Program...", flush=True)
            stdout.flush()                              # flush console output buffer in case there are remaining prints
            _exit(0)                                    # exit program with status 0

        if failLink != None:                                                                                                        # fail a link between desired nodes format: failLink(Nx)
            nodeToFail = failLink[-1]
            print("Failing connection from node: " + str(nodeID) + " to node: " + str(nodeToFail) + "...", flush=True)              # print message to console
            outBoundSockets[int(nodeToFail)].sendall(f"FAIL {nodeID}".encode())                                                     # send fail message to other node
            del outBoundSockets[int(nodeToFail)]                                                                                    # delete socket from outBoundSockets
            print("Connection from node: " + str(nodeID) + " to node: " + str(nodeToFail) + " failed\n", flush=True)                # print message to console

        if fixLink != None:                                                                                                         # fix a link between desired nodes format: finxLink(Nx)
            nodeToFix = fixLink[-1]
            print("Fixing connection from node: " + str(nodeID) + " to node: " + str(nodeToFix) + "...", flush=True)                # print message to console
            addConns(int(nodeToFix))                                                                                                # add socket back to outBoundSockets
            outBoundSockets[int(nodeToFix)].sendall(f"FIX {nodeID}".encode())                                                       # send fix message to other node
            print("Connection from node: " + str(nodeID) + " to node: " + str(nodeToFix) + " fixed\n", flush=True)                  # print message to console

        if userInput == "blockchain":                            # iterate through blockchain to append to history array
            if(blockchain.returnBlockLength() == 1):             # if blockchain is empty
                print("Blockchain is empty\n", flush=True)
            else:
                print("Printing blockchain...", flush=True)          # print message to console
                blockchainHistory = blockchain.getBlogChain()        # get blockchain history

                for block in blockchainHistory[1:]:                  # iterate through blockchain history
                    print(block, flush=True)                         # print each block to console

        if userInput == "queue":                              # print queue
            if(len(queue) == 0):                              # if queue is empty
                print("Queue is empty\n", flush=True)         # print message to console
            else:                                             # if queue is not empty
                print("Queue:", flush=True)
                print(queue, flush=True)                      # print queue to console
                print("\n", flush=True)

        if splicedInput[0] == "post" or splicedInput[0] == "comment":

            if splicedInput[0] == "post" and blockchain.isValidPost(splicedInput[2]) == True:
                print("DUPLICATE TITLE", flush=True)

            if splicedInput[0] == "comment" and blockchain.isValidPost(splicedInput[2]) == False:
                print("No such post with desired title. Cannot leave a comment.", flush=True)
           
            elif leadID == nodeID:                                # pseudo leader
                
                queue.append(userInput)

                operation = splicedInput[0]
                user = splicedInput[1]
                title = splicedInput[2]
                contents = splicedInput[3]

                blockToAdd = Block(blockchain.getLatestBlock().hash, operation, user, title, contents)
                blockToAdd.calcNonce()
                blockchain.appendBlock(blockToAdd, user, operation, title, contents)

                for node in outBoundSockets.values():
                    print("Sending Accept Message...", flush=True)                                                                                                                                       # print message to console
                    node.sendall(f"ACCEPT {nodeID} {blockchain.returnBlockLength()} {blockToAdd.operation} {blockToAdd.user} {blockToAdd.title} {blockToAdd.contents} {blockToAdd.nonce}".encode())      # send accept message to other nodes

            elif leadID == None:                                    # pseudo proposer
                
                for node in outBoundSockets.values():                                                          # iterate through outbound sockets
                    print("Sending Prepare Message...", flush=True)                                            # print message to console
                    node.sendall(f"PREPARE {nodeID} {blockchain.returnBlockLength()} {userInput}".encode())    # send prepare message to other nodes
        
            else:                                                  # pseudo acceptor
                outBoundSockets[int(leadID)].sendall(f"FORWARD {nodeID} {userInput}".encode())                 # forward message

        if userInput == "blog":
            if blockchain.returnBlockLength() == 1:
                print("BLOG EMPTY", flush=True)
            
            else:
                print("Printing blog...", flush=True)
                count = 0                                         # init count for skipping genesis block
                titleOfPosts = []                                 # init list of titles which contain the post Titles
                
                for block in blockchain.chain:                    # iterate through blockchain
                    if count == 0:                                # skip genesis block
                        count = count + 1
                        continue

                    if block.operation == "post":                 # if block operation is post
                        titleOfPosts.append(block.title)          # append block title to list of titles
    
                for title in titleOfPosts:                        # iterate through list of titles
                    print(str(title), flush=True)                 # print title to console

        if view != None:                                                                            # view post by username format: view(user)
            userContents = []                                                                       # init list of user contents
            desiredUser = view[-1]                                                                  # get username

            for block in blockchain.chain:                                                                                     # iterate through blockchain
                if desiredUser == block.user:                                                                                  # if block username is username
                    userContents.append(("Title: " + str(block.title), "Contents: " + str(block.contents)))                    # append block to list of user contents

            if len(userContents) == 0:
                print("NO POST", flush=True)
            else:
                print("Viewing posts by " + desiredUser + "...", flush=True)                                                   # print message to console
                for content in userContents:
                    print(str(content[0]) + " " + str(content[1]), flush=True)

        if read != None:                                                     # read post by title format read(title)
            titleContents = []                                               # init list of title contents
            desiredTitle = read[-1]                                          # get title

            for block in blockchain.chain:                                   # iterate through blockchain
                if desiredTitle == block.title:                              # if block title is title
                    titleContents.append((block.user, block.contents))       # append block to list of title contents

            if len(titleContents) == 0:                                      # if title not found
                print("POST NOT FOUND", flush=True)                          # print message to console
            else:
                for post in titleContents:                                   # iterate through list of title contents
                    print(str(post[0]) + ": " + str(post[1]), flush=True)    # print post to console

        if userInput == "load":
            content = open(nodeBlockChainLogFileName, 'r').readlines()

            for row in content:                                             # iterate through file
                row = row[:-1]                                             # ignore endlines
                splicedRow = row.split(" ")                                  
                blockToAdd = Block(blockchain.getLatestBlock().hash, splicedRow[1], splicedRow[0], splicedRow[2], splicedRow[3])  # create block
                blockToAdd.calcNonce()                                                                                        # calculate block nonce
                blockchain.appendBlock(blockToAdd,splicedRow[2], splicedRow[1], splicedRow[3], splicedRow[4] )                    # add block

            content = open(blogFile, 'r').readlines()
            for row in content:                                            # iterate through file
                row = row[:-1]                                             # ignore endlines
                splicedRow = row.split(" ")
                blogApp.add_post(splicedRow[0], splicedRow[1], splicedRow[2], splicedRow[3])            # add post to blog

        if userInput == "exit":
            inBoundSocket.close()                          # close all sockets before exiting
            print("Exiting Program...\n", flush=True)
            stdout.flush()                                 # flush console output buffer in case there are remaining prints
            _exit(0)                                       # exit program with status 0

        if userInput == "reconnect":                                # reconnect to all nodes
            for sock in outBoundSockets.values():                   # send reconnect message to all nodes
                sock.sendall(f"RECONNECT {nodeID}".encode())        

        if wait != None:                 # wait function used in autograder
            time = wait[-1]
            print("waiting " + str(time) + " seconds")
            sleep(int(time))

def handle_msg(data, conn, addr):                      # simulates network delay then handles received message
    global leadID
    global acceptCount
    global promiseCount

    nodeBlockChainLogFileName = f"Node_{nodeID}_Blockchain_Log.txt"
    blogFile = f"Node_{nodeID}_Blog.txt"

    sleep(3)

    data = data.decode()                        # decode byte data into a string

    try:
        data = data.split(" ")
        command = data[0]
        node_ID = data[1]
        blockchainLength = data[2]

        if command == "PREPARE" and int(blockchainLength) >= blockchain.returnBlockLength():
                print(f"recieved PREPARE from node: {node_ID}")

                logOfOperation = data[3] + " " + data[4] + " " + data[5] + " " + data[6]
                outBoundSockets[int(node_ID)].sendall(f"PROMISE {nodeID} {logOfOperation}".encode())
        
        if command == "PROMISE":
            print(f"recieved PROMISE from N{node_ID}")
            promiseCount += 1
            if promiseCount >= math.ceil((len(outBoundSockets) + 1)/2):
                promiseCount = 0
                leadID = nodeID
                logOfOperation = data[2] + " " + data[3] + " " + data[4] + " " + data[5]
                queue.append(logOfOperation)
                new_block = Block(blockchain.getLatestBlock().hash, data[2], data[3], data[4], data[5])
                new_block.calcNonce()
                for node in outBoundSockets.values():
                    node.sendall(f"ACCEPT {nodeID} {blockchain.returnBlockLength()} {new_block.operation} {new_block.user} {new_block.title} {new_block.contents} {new_block.nonce}".encode())

        if command == "ACCEPT" and int(blockchainLength) >= blockchain.returnBlockLength():
            print(f"recieved ACCEPT from N{node_ID}")
            leadID = int(node_ID)
            logOfOperation = data[3] + " " + data[4] + " " + data[5] + " " + data[6]
            outBoundSockets[int(node_ID)].sendall(f"ACCEPTED {nodeID} {logOfOperation}".encode())
            with open(nodeBlockChainLogFileName, "a") as log:
                    log.write(f"TENATIVE {logOfOperation}\n")

        if command == "ACCEPTED":
            sleep(0.5) # Chris: Added this bc lines were printing on top of each other
            print(f"recieved ACCEPTED from N{node_ID}")
            acceptCount += 1
            if acceptCount >= math.ceil((len(outBoundSockets) + 1)/2):
                acceptCount = 0
                new_block = Block(blockchain.getLatestBlock().hash, data[2], data[3], data[4], data[5])
                blockchain.appendBlock(new_block, data[3], data[2], data[4], data[5])
                with open(nodeBlockChainLogFileName, "a") as log:
                    log.write(f"CONFIRMED {new_block.operation} {new_block.user} {new_block.title} {new_block.contents}\n")
                blogApp.add_post(data[2], data[3], data[4], data[5])

                with open(blogFile, "a") as log:
                    log.write(f"{new_block.operation} {new_block.user} {new_block.title} {new_block.contents}\n")
                queue.pop(0)
                if data[2] == "post":
                    print(f"NEW POST: {data[4]} from {data[3]}")
                if data[2] == "comment":
                    print(f"NEW COMMENT: on {data[4]} from {data[3]}")
                for node in outBoundSockets.values():
                    node.sendall(f"DECIDE {nodeID} {new_block.operation} {new_block.user} {new_block.title} {new_block.contents}".encode())

        if command == "DECIDE":
            print(f"recieved DECIDE from N{node_ID}")
            new_block = Block(blockchain.getLatestBlock().hash, data[2], data[3], data[4], data[5])
            blockchain.appendBlock(new_block, data[3], data[2], data[4], data[5])
            content = open(nodeBlockChainLogFileName, 'r').readlines()
            content[-1] = f"CONFIRMED {new_block.operation} {new_block.user} {new_block.title} {new_block.contents}\n"
            out = open(nodeBlockChainLogFileName, 'w')
            out.writelines(content)
            out.close()
            blogApp.add_post(data[2], data[3], data[4], data[5])
            with open(blogFile, "a") as log:
                    log.write(f"{new_block.operation} {new_block.user} {new_block.title} {new_block.contents}\n")

            if data[2] == "post":
                print(f"NEW POST: {data[4]} from {data[3]}")

            if data[2] == "comment":
                print(f"NEW COMMENT: on {data[4]} from {data[3]}")

        if command == "FORWARD":
            print(f"recieved FORWARD from {node_ID}")
            if leadID == nodeID:
                logOfOperation = data[2] + " " + data[3] + " " + data[4] + " " + data[5]
                queue.append(logOfOperation)
                new_block = Block(blockchain.getLatestBlock().hash, data[2], data[3], data[4], data[5])
                new_block.calcNonce()
                for node in outBoundSockets.values():
                    node.sendall(f"ACCEPT {nodeID} {blockchain.returnBlockLength()} {new_block.operation} {new_block.user} {new_block.title} {new_block.contents} {new_block.nonce}".encode())
            else:
                outBoundSockets[leadID].sendall(f"FORWARD {nodeID} {logOfOperation}".encode())

        if command == "RECONNECT":
            print(f"reconnecting to N{node_ID}")
            addConns(int(node_ID))

        if command == "FAIL":
            del outBoundSockets[int(node_ID)]
            print(f"Connection to N{node_ID} failed", flush=True)

        if command == "FIX":
            addConns(int(node_ID))
            print(f"Connection to N{node_ID} fixed", flush=True)

    except Exception:
        traceback.print_exc()

def respond(conn, addr):                            # handle a new connection by waiting to receive from connection 

    while True:                                     # infinite loop to keep waiting to receive new data from this client
        try:
            data = conn.recv(1024)
        except:
            conn.close()
            delConns()
            print(f"Exception raised in receiving from {addr[1]}.", flush=True)
            break
        if not data:                                                                 # if client's socket closed, it will signal closing without any data
            conn.close()                                                             # close own socket to client since other end is closed
            print(f"Connection has been closed from {addr[1]}.", flush=True)
            break

        threading.Thread(target=handle_msg, args=(data,conn, addr)).start()           # new thread to handle message so simulated network delay and message handling don't block receive

def getConns():
    count = 0
    while True:
        try:
            conn, addr = inBoundSocket.accept()
        except:
            print("Exception in accept.", flush= True)
            break
        print("Connected to the inbound client", flush=True)
        count = count + 1

        if count == 2: #CHANGE TO 4 b4 demo
            print("All nodes have been connected...\n", flush=True)
        threading.Thread(target=respond, args=(conn,addr)).start()

def delConns():
    failedConns = []
    for id, node in outBoundSockets.items():
        try:
            node.sendall("ping".encode())
        except:
            failedConns.append(id)
    for id in failedConns:
        del outBoundSockets[id]

def addConns(nodeID):
    if id not in outBoundSockets:
        try:
            out_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            out_sock.connect((IP, 9000 + nodeID))
            outBoundSockets[nodeID] = out_sock
            print(f"Connected to outbound node: {nodeID}", flush=True)
        except:
            print(f"Failed to connect to outbound client node: {nodeID}", flush=True)

if __name__ == "__main__":
    nodeID = str(sys.argv[1])                   # get node ID from command line
    nodeID = nodeID.replace("N", "")            # remove N from node ID

    portNum = 9000 + int(nodeID)                # set port number
    queue = []                                  # queue to store messages
    IP = socket.gethostname()                   # get IP address

    blogApp = Blog()                            #initalize blog
    blockchain = Blockchain()                   #initalize blockchain
    outBoundSockets = {}                        # dictionary of outbound sockets

    # PAXOS VARIABLES
    leadID = None                               # leader ID
    promiseCount = 0                            # promise count
    acceptCount = 0                             # accept count

    inBoundSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)             # create a socket object, SOCK_STREAM specifies a TCP socket
    inBoundSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)           # when REUSEADDR is not set
    inBoundSocket.bind((IP, portNum))                                             # bind socket to address
    inBoundSocket.listen()                                                        # start listening for connections to the address
    threading.Thread(target=getConns).start()                                     # start thread to listen for new connections

    sleep(8)
    
    # outBoundSocket1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # outBoundSocket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # outBoundSocket3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # out_sock4 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    if int(nodeID) == 1:
        addConns(2)
        addConns(3)
        # outBoundSocket1.connect((IP, 9002))
        # outBoundSocket2.connect((IP, 9003))
        # outBoundSockets[2] = outBoundSocket1
        # outBoundSockets[3] = outBoundSocket2
 
    if int(nodeID) == 2:
        addConns(1)
        addConns(3)
        # outBoundSocket1.connect((IP, 9001))
        # outBoundSocket2.connect((IP, 9003))
        # outBoundSockets[1] = outBoundSocket1
        # outBoundSockets[3] = outBoundSocket2

    if int(nodeID) == 3:
        addConns(1)
        addConns(2)
        # outBoundSocket1.connect((IP, 9001))
        # outBoundSocket2.connect((IP, 9002))
        # outBoundSockets[1] = outBoundSocket1
        # outBoundSockets[2] = outBoundSocket2


    # if nodeID == 1:       CHANGE to all 5 servers
    #     out_sock1.connect((IP, 9002))
    #     out_sock2.connect((IP, 9003))
    #     out_sock3.connect((IP, 9004))
    #     out_sock4.connect((IP, 9005))
    #     out_socks[2] = out_sock1
    #     out_socks[3] = out_sock2
    #     out_socks[4] = out_sock3
    #     out_socks[5] = out_sock4
    # if nodeID == 2:
    #     out_sock1.connect((IP, 9001))
    #     out_sock2.connect((IP, 9003))
    #     out_sock3.connect((IP, 9004))
    #     out_sock4.connect((IP, 9005))
    #     out_socks[1] = out_sock1
    #     out_socks[3] = out_sock2
    #     out_socks[4] = out_sock3
    #     out_socks[5] = out_sock4
    # if idNum == 3:
    #     out_sock1.connect((IP, 9001))
    #     out_sock2.connect((IP, 9002))
    #     out_sock3.connect((IP, 9004))
    #     out_sock4.connect((IP, 9005))
    #     out_socks[1] = out_sock1
    #     out_socks[2] = out_sock2
    #     out_socks[4] = out_sock3
    #     out_socks[5] = out_sock4
    # if nodeID == 4:
    #     out_sock1.connect((IP, 9001))
    #     out_sock2.connect((IP, 9002))
    #     out_sock3.connect((IP, 9003))
    #     out_sock4.connect((IP, 9005))
    #     out_socks[1] = out_sock1
    #     out_socks[2] = out_sock2
    #     out_socks[3] = out_sock3
    #     out_socks[5] = out_sock4
    # if nodeID == 5:
    #     out_sock1.connect((IP, 9001))
    #     out_sock2.connect((IP, 9002))
    #     out_sock3.connect((IP, 9003))
    #     out_sock4.connect((IP, 9004))
    #     out_socks[1] = out_sock1
    #     out_socks[2] = out_sock2
    #     out_socks[3] = out_sock3
    #     out_socks[4] = out_sock4

    threading.Thread(target=get_userInput).start() 
    