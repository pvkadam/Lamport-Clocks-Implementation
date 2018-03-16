# -*- coding: utf-8 -*-
#Created on Thu Oct 5 14:07:10 2017


from socket import *
from _thread import *
import json
import socialmedia
import threading
from heapq import *
import time
import sys
import lamportclock

class Client:
    hostname = ''
    port = 0
    s = None
    processID = 0
    replyList = []
    time =0

# Initializing Client and its attributes
    def __init__(self, ID):
        print("System running: "+ ID)
        port = configdata["systems"][ID][1]
        self.port = port
        self.processID = int(self.port) - 4000
        self.hostname = gethostname()
        self.reqQueue = []
        self.lc = lamportclock.LamportClock(time, self.processID, self.reqQueue)
        self.replyList = []
        self.lock = threading.RLock()
        self.s = socket(AF_INET, SOCK_STREAM)
        print("Post: \n" + str(sm.post) + "\nCurrent like count " + str(sm.numofLikes))
        start_new_thread(self.startListening, ())
        start_new_thread(self.awaitInput, ())

        while True:
            pass

    def receiveMessages(self, conn, addr):
            msg = conn.recv(1024).decode()
            time.sleep(delay)
            if "release" in msg:
                removed = self.removefromRequestQ(self.reqQueue)
                print("Current Lamport time " + self.lc.getLamportTime())
                self.lc.incrementTime()
                self.printRequestQ(self.reqQueue)
                print("Enter 1 to like: ")
            if "Reply" in msg:
                lamtime = msg.split()[3]
                lamtime = lamtime[0]
                seen = set(self.replyList)  # Checking for duplicate replies if any
                if msg.split()[2] not in seen:
                    seen.add(msg.split()[2])
                    self.replyList.append(msg.split()[2])
                self.lc.compareTime(int(lamtime))
                print("Current Lamport time "+ self.lc.getLamportTime())
                print("Reply list is ")
                self.printReplyList(self.replyList)
            if "Add" in msg:
                port = msg.split()[3]
                ltime = msg.split()[4]
                self.addtoRequestQueue(self.reqQueue, float(ltime), "S"+str(port[-1:]))
                ltime = ltime[0]
                self.lc.incrementTime()
                self.lc.compareTime(int(ltime))
                print("Current Lamport time " + self.lc.getLamportTime())
                self.sendReply(configdata["systems"]["S"+str(port[-1:])][1])
                self.printRequestQ(self.reqQueue)
            if "Post" in msg:
                likes = msg.split()[-1]
                sm.numofLikes = int(likes)
            print(msg)

    def awaitInput(self):
        while True:
            message = input('Enter 1 to like: ')
            message = int(message)
            if (message == 1):
                start_new_thread(self.whenLiked, ())
            else:
                print('Invalid input')

    def whenLiked(self):

        systemName = "S" + str(self.processID)
        lamporttime = float(self.lc.getLamportTime())
        self.addtoRequestQueue(self.reqQueue, lamporttime, systemName)
        self.printRequestQ(self.reqQueue)
        time.sleep(delay)
        addMessage = "Added to queue " + str(self.port) + " " + str(lamporttime)
        print(addMessage)
        self.sendToAll(addMessage)  # Add to all request Queues
        self.printRequestQ(self.reqQueue)
        time.sleep(delay)
        topofQ = self.reqQueue[0][1]
        print("Top of Queue is " + str(topofQ))

        while True:
            topofQ = self.reqQueue[0][1]
            if topofQ == ("S" + str(self.processID)) and len(self.replyList) == 3:
                break
            else:
                time.sleep(delay)

        time.sleep(delay)
        self.lock.acquire(sm.numofLikes)
        sm.numofLikes = sm.numofLikes + 1
        tosend = "Post: \n" + str(sm.post) + "\nCurrent like count " + str(sm.numofLikes)
        print(tosend)
        self.sendToAll(tosend)
        time.sleep(delay)
        releaseMessage = "Resource release message from port " + str(self.port)
        self.sendToAll(releaseMessage)
        print("Current Lamport time " + self.lc.getLamportTime())
        self.removefromRequestQ(self.reqQueue)
        self.replyList.clear()
        self.lock.release()

    def startListening(self):
        try:
            self.s.bind((self.hostname, int(self.port)))
            self.s.listen(4)
            print("server started on port " + str(self.port))
            while True:
                c, addr = self.s.accept()
                conn = c
                print('Got connection from')
                print(addr)
                start_new_thread(self.receiveMessages, (conn, addr)) # connection dictionary
        except(gaierror):
            print('There was an error connecting to the host')
            self.s.close()
            sys.exit()

    def sendReply(self, port):
        rSocket = socket(AF_INET, SOCK_STREAM)
        rSocket.connect((gethostname(), int(port)))
        reply = "Reply from " + str(self.port) + " " + self.lc.getLamportTime()
        rSocket.send(reply.encode())
        print("Sent reply to port " + str(port))
        rSocket.close()

# To send messages to everyone
    def sendToAll(self, message):
        for i in configdata["systems"]:
            if (configdata["systems"][i][1] == self.port):
                continue
            else:
                cSocket = socket(AF_INET, SOCK_STREAM)
                ip, port = configdata["systems"][i]
                port = int(port)
                cSocket.connect((gethostname(), port))
                print('Connected to port number ' + configdata["systems"][i][1])
                cSocket.send(message.encode())
                time.sleep(delay)
                print('Message sent to Client at port '+ str(port))
                cSocket.close()

    def addtoRequestQueue(self, reqQueue, time, item):
        heappush(reqQueue, (time, item))

    def removefromRequestQ(self, queue):
        return heappop(queue)

    def printRequestQ(self, queue):
        print("Current Request Queue is")
        sorted = nsmallest(len(queue), queue)
        for i in sorted:
            print(i)

    def printReplyList(self, rlist):
        for i in rlist:
            print(i)

    def closeSocket(self):
        self.s.close()

######## MAIN #########

with open('config.json') as configfile:
    configdata = json.load(configfile)

sm = socialmedia.Socialmedia(0)
delay = configdata["delay"]
ID = sys.argv[1]
c = Client(ID)
