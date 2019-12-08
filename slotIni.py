import sys
import math
import random
import time
from tkinter import *
import tkinter.font

# Define my class


class SlotsIniApp:

    # Positions and actions
    canvasAction = "draw_slot"
    leftBtn = "up"
    xPos = None
    yPos = None
    x1, y1, x2, y2 = None, None, None, None
    canvasX, canvasY = None, None # full width and height

    # Window Elements
    btnContainer, canvas, slotPlaceholder = None, None, None
    scale = 1

    # Variables specific to the laser machine
    toolStartX = 0
    toolStartY = 0
    toolStartZ = 0
    toolTotalLegoX = 200
    toolTotalLegoY = 150

    # Current slots on the canvas
    slots = []

    # The definitive actual size of 1 lego (mm)
    LEGO_UNIT = 7.985
    # A one to one relation with lego unit to draw "snapping" lines
    CANVAS_UNIT = 12
    SCALE_UP = 1.1
    SCALE_DOWN = 0.9

# Catch Mouse Up
    def leftBtnUp(self, event=None):
        self.leftBtn = "up"

        self.xPos = None
        self.yPos = None

        self.x2 = self.canvas.canvasx(event.x)
        self.y2 = self.canvas.canvasy(event.y)

        if self.canvasAction == "draw_slot":
            self.addSlot(event)

# Catch Mouse Down
    def leftBtnDown(self, event=None):
        self.leftBtn = "down"

        self.x1 = self.canvas.canvasx(event.x)
        self.y1 = self.canvas.canvasy(event.y)

# Catch Mouse Move
    def motion(self, event=None):
        self.xPos = self.canvas.canvasx(event.x)
        self.yPos = self.canvas.canvasy(event.y)
        self.coords.delete(1.0,END)
        self.coords.insert(INSERT, "{x},{y}".format(x=self.xPos, y=self.yPos))
        if self.leftBtn == "down":
            if self.slotPlaceholder:
                self.canvas.delete(self.slotPlaceholder)
            self.slotPlaceholder = self.drawRectangle(
                self.x1, self.y1, self.xPos, self.yPos, "slot_placeholder")

# Calculate the nearest lego line
    def getLegoPos(self, xInput, yInput):
        canvasUnit = self.CANVAS_UNIT * self.scale
        legoX = round((xInput - canvasUnit) / canvasUnit)
        legoY = round(self.toolTotalLegoY - (yInput - canvasUnit) / canvasUnit)
        return legoX, legoY

    def getCanvasPos(self, xLego, yLego):
        canvasUnit = self.CANVAS_UNIT * self.scale
        x = xLego * canvasUnit + canvasUnit
        y = (self.canvasY + canvasUnit) - (yLego * canvasUnit)
        return x, y

# Add a new slot to this.slots
    def addSlot(self, event=None):
        # Snap x and y to nearest coordinates
        legoX1, legoY1 = self.getLegoPos(self.x1, self.y1)
        legoX2, legoY2 = self.getLegoPos(self.x2, self.y2)
        # Save slot in the slots array
        canvasX1, canvasY1 = self.getCanvasPos(legoX1, legoY1)
        canvasX2, canvasY2 = self.getCanvasPos(legoX2, legoY2)
        
        self.drawRectangle(canvasX1, canvasY1, canvasX2, canvasY2)

        # Delete placeholder rectangle
        if self.slotPlaceholder:
            self.canvas.delete(self.slotPlaceholder)

# Draw Rectangle by type
    def drawRectangle(self, x1, y1, x2, y2, type="slot"):
        border = "gray"
        borderWidth = 2
        stipple = "gray50" #transparency

        if type == "slot":
            border = "black"
            bkgColor = "magenta"

        elif type == "slot_placeholder":
            borderWidth = 0
            bkgColor = "cyan"

        return self.canvas.create_rectangle(
            x1, y1, x2, y2, fill=bkgColor, outline=border, width=borderWidth, stipple=stipple)

    def drawLine(self, x1, y1, x2, y2):
        self.canvas.create_line(x1, y1, x2, y2)

    def _initLegoGrid(self):
        unit = self.CANVAS_UNIT * self.scale
        x, y = unit, unit
        xCount, yCount = 0, 0

        # Horizantal lines
        while yCount < self.toolTotalLegoY + 1:
            self.drawLine(x, y, x + self.canvasX, y)
            yCount += 1
            y += unit

        y = unit
        # Vertical lines
        while xCount < self.toolTotalLegoX + 1:
            self.drawLine(x, y, x, y + self.canvasY)
            xCount += 1
            x += unit

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(-1*(event.delta/120), "units")

    def zoomIn(self):
        self.scale *= self.SCALE_UP
        self.canvasX *= self.SCALE_UP
        self.canvasY *= self.SCALE_UP
        self._initCanvas()
    
    def zoomOut(self):
        self.scale *= self.SCALE_DOWN
        self.canvasX *= self.SCALE_DOWN
        self.canvasY *= self.SCALE_DOWN
        self._initCanvas()
    
    def _initCanvas(self):
        unit = (self.CANVAS_UNIT * 2) * self.scale
        self.canvas.delete("all")
        self.canvas.config(
            width=self.canvasX + unit,
            height=self.canvasY + unit,
            scrollregion=(0, 0, self.canvasX + unit, self.canvasY + unit))
        self._initLegoGrid()
        self.drawSlots()
        self.canvas.yview_moveto( 1 )

    def drawSlots(self):
        return


# Initialize
    def __init__(self, root):

        self.master = root
        pad = 70
        fullX = root.winfo_screenwidth()
        fullY = root.winfo_screenheight()

        root.geometry("{0}x{1}+0+0".format(
            fullX-pad, fullY-pad))

        self.btnContainer = Frame(root)
        self.btnContainer.pack()

        self.button1 = Button(self.btnContainer)
        self.button1["text"] = "Save"
        self.button1.pack( side = LEFT)

        self.btnZoomOut = Button(self.btnContainer, command = self.zoomOut)
        self.btnZoomOut['text'] = "-"
        self.btnZoomOut.pack(side=LEFT)

        self.btnZoomIn = Button(self.btnContainer, command = self.zoomIn)
        self.btnZoomIn['text'] = "+"
        self.btnZoomIn.pack(side=LEFT)

        self.coords = Text(self.btnContainer, height=1, width=20)
        self.coords.pack(side=RIGHT)

        # Calc full size of canvas based on lego width and height
        self.canvasX = self.toolTotalLegoX * self.CANVAS_UNIT
        self.canvasY = self.toolTotalLegoY * self.CANVAS_UNIT
        self.canvas = Canvas(root, bg="white")

        scrollRight = Scrollbar(root, command=self.canvas.yview)
        scrollRight.pack(side=RIGHT, fill=Y)

        scrollBottom = Scrollbar(
            root, orient=HORIZONTAL, command=self.canvas.xview)
        scrollBottom.pack(side=BOTTOM, fill=X)

        self.canvas.config(
            xscrollcommand=scrollBottom.set,
            yscrollcommand=scrollRight.set)

        self.canvas.pack(side="top", fill="both", expand=True)
        self.canvas.bind("<Motion>", self.motion)
        self.canvas.bind("<ButtonPress-1>", self.leftBtnDown)
        self.canvas.bind("<ButtonRelease-1>", self.leftBtnUp)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self._initCanvas()


root = Tk()
paintApp = SlotsIniApp(root)
root.mainloop()
