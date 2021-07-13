#!/usr/bin/env python

from config import *

import math
import tkinter
import socket
import re
from PIL import Image, ImageTk

sizeRegex = re.compile("SIZE (\d+) (\d+)\n*")
pxRegex = re.compile("PX (\d+) (\d+) ([0-9A-F]{6})\n*")

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def send(msg):
    return s.sendall(msg.encode("utf-8"))

respBuffer = ""
def recv():
    global respBuffer
    resp = s.recv(512).decode("utf-8")
    respBuffer += resp

def matchResponse(r):
    global respBuffer
    match = r.match(respBuffer)
    if match != None:
        respBuffer = respBuffer[len(match[0]):]
    return match

print("Connecting to %s:%d" % (HOST, PORT))
s.connect((HOST, PORT))

print("Retrieving canvas size")
send("SIZE\n")
recv()
match = matchResponse(sizeRegex)
w, h = int(match[1]), int(match[2])
print("Canvas size is %dx%d" % (w, h))

win = tkinter.Tk();
can = tkinter.Canvas(win, bg="black", width=w, height=h);

def updatePixel(x, y, col):
    x = int(x)
    y = int(y)

    tag = "%d,%d" % (x, y)
    can.delete(tag)
    can.create_rectangle(x, y, x + PIXEL_SIZE, y + PIXEL_SIZE, fill="#"+col, outline="", tags=tag)

needRefresh = 0 # numer of pixels to be received
def refresh():
    global respBuffer, needRefresh
    
    while needRefresh > 0:
        recv()
        match = matchResponse(pxRegex)
        col = None
        while match != None:
            needRefresh -= 1
            updatePixel(match[1], match[2], match[3])
            match = matchResponse(pxRegex)

def requestRefresh():
    global needRefresh
    x, y = 0, 0

    req = ""
    while y < h:
        req += "PX %d %d\n" % (x, y)
        needRefresh += 1
        x += PIXEL_SIZE
        if x >= w:
            x = 0
            y += PIXEL_SIZE
    send(req)
    refresh()
    win.after(REFRESH_INTERVAL, requestRefresh)

colour = "FF0000"
clicklast = None
def onclick(event):
    global localPixels, needRefresh, colour, clicklast

    clickx, clicky = math.floor(event.x / PIXEL_SIZE) * PIXEL_SIZE, math.floor(event.y / PIXEL_SIZE) * PIXEL_SIZE

    # Don't repeat pixels
    if (clickx, clicky) == clicklast:
        return

    updatePixel(clickx, clicky, colour)

    req = ""
    for x in range(clickx, clickx + PIXEL_SIZE, 1):
        for y in range(clicky, clicky + PIXEL_SIZE, 1):
            req += "PX {0} {1} {2}\n".format(x, y, colour)
    send(req)

def onrelease(event):
    global clicklast
    clicklast = None

def keyPressed(event):
    global colour
    if event.char == '1':
        colour = "FF0000"
    elif event.char == '2':
        colour = "FF8000"
    elif event.char == '3':
        colour = "FFFF00"
    elif event.char == '4':
        colour = "00FF00"
    elif event.char == '5':
        colour = "00FFFF"
    elif event.char == '6':
        colour = "0000FF"
    elif event.char == '7':
        colour = "7F00FF"
    elif event.char == '8':
        colour = "FFFFFF"
    elif event.char == '9':
        colour = "808080"
    elif event.char == '0':
        colour = "000000"
    else:
        return
    print("Colour changed to #%s" % colour)

can.bind("<Button-1>", onclick)
can.bind("<B1-Motion>", onclick)
can.bind("ButtonRelease-1", onrelease)
win.bind_all("<KeyPress>", keyPressed)

can.pack()

win.after(1, requestRefresh)

win.mainloop()

print("See you next time!")
