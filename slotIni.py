import sys
import math
import random
import time
from tkinter import *
import tkinter.font
import tkinter.simpledialog

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
    master = None
    btnContainer, canvas, slotPlaceholder = None, None, None
    scale = 1

    # Variables specific to the laser machine
    toolStartX = 0
    toolStartY = 0
    toolStartZ = 0
    toolTotalLegoX = 200
    toolTotalLegoY = 150

    # Current slots on the canvas
    slots = {}
    # Key of the currrently focused slot
    focusedSlot = None

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
        elif self.canvasAction == "edit_slot":
            self.editSlot()

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

# Calculate the nearest lego position
    def getLegoPos(self, xInput, yInput):
        canvasUnit = self.CANVAS_UNIT * self.scale
        legoX = round((xInput - canvasUnit) / canvasUnit)
        legoY = round(self.toolTotalLegoY - (yInput - canvasUnit) / canvasUnit)
        return legoX, legoY

# Converts lego units to a position on the canvas
    def getCanvasPos(self, xLego, yLego):
        canvasUnit = self.CANVAS_UNIT * self.scale
        x = xLego * canvasUnit + canvasUnit
        y = (self.canvasY + canvasUnit) - (yLego * canvasUnit)
        return x, y

# Asks the user to input a slot name and checks if it's already used.
    def getSlotName(self, dialog = "Enter slot name"):
        name = tkinter.simpledialog.askstring("Name Slot", dialog)
        if name in self.slots:
            name = self.getSlotName("Name already exists, enter a new name")
        return name

    def editSlot(self, event=None):
        self.editDialog = SlotEditDialogue(self)

# Add a new slot to this.slots
    def addSlot(self, event=None):
        name = self.getSlotName()
        if not name:
            # Delete placeholder rectangle
            if self.slotPlaceholder:
                self.canvas.delete(self.slotPlaceholder)
            return

        # Snap x and y to nearest coordinates
        legoX1, legoY1 = self.getLegoPos(self.x1, self.y1)
        legoX2, legoY2 = self.getLegoPos(self.x2, self.y2)

        # Draw the rectangle
        canvasX1, canvasY1 = self.getCanvasPos(legoX1, legoY1)
        canvasX2, canvasY2 = self.getCanvasPos(legoX2, legoY2)
        rectangle = self.drawRectangle(canvasX1, canvasY1, canvasX2, canvasY2)

        # Add a new Frame on the canvas over the new slot
        buttonBg, buttonTxt = self.drawSlotExtras(
            name, canvasX1, canvasY1, canvasX2, canvasY2)

        # Save slot in the slots array
        self.slots[name] = {
            "canvasElements" : {
                "button" : buttonBg,
                "button_text" : buttonTxt,
                "rectangle" : rectangle,
                "lego_text" : None, #TODO
                "rl_size" : None #TODO, real life size in mm
            },
            "legoPos" : {
                "lowX" : min(legoX1, legoX2),
                "lowY" : min(legoY1, legoY2),
                "highX" : max(legoX1, legoX2),
                "highY" : max(legoY1, legoY2)
            },
            "numberX" : 1,
            "numberY" : 1,
            "innerSlots" : []
        }

        # Delete placeholder rectangle
        if self.slotPlaceholder:
            self.canvas.delete(self.slotPlaceholder)

    def drawSlotExtras(self, name, x1, y1, x2, y2):
        lowerX = min(x1, x2)
        lowerY = min(y1, y2)
        slotMiddleX = abs(x1 - x2) / 2 + lowerX
        def setEditSlot(self):
            self.canvasAction = "edit_slot"
            self.focusedSlot = name

        buttonBg = self.canvas.create_rectangle(
            slotMiddleX - 20, lowerY + 40,
            slotMiddleX + 20, lowerY + 20, 
            fill="grey40", outline="grey60")
        buttonTxt = self.canvas.create_text(
            slotMiddleX, lowerY + 30, text=name)
        self.canvas.tag_bind(buttonBg, "<Button-1>", setEditSlot(self))
        self.canvas.tag_bind(buttonTxt, "<Button-1>", setEditSlot(self))
        return buttonBg, buttonTxt

# Draw Rectangle by type
    def drawRectangle(self, x1, y1, x2, y2, type="slot"):
        border = "gray"
        borderWidth = 2
        stipple = "gray50" #transparency

        if type == "slot":
            border = "black"
            bkgColor = "magenta"

        elif type == "slot_inner":
            borderWidth = 0
            bkgColor = "green"

        elif type == "slot_placeholder":
            borderWidth = 0
            bkgColor = "cyan"

        return self.canvas.create_rectangle(
            x1, y1, x2, y2, fill=bkgColor, outline=border, width=borderWidth, stipple=stipple)

# Draw a simple line, nothing fancy
    def drawLine(self, x1, y1, x2, y2):
        self.canvas.create_line(x1, y1, x2, y2)


# Draw the "background" lego grid based on current scale
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

# Draw all the slot from the this.slots dictionary.
    def drawSlots(self):
        for key, value in self.slots.items():

            lego = value['legoPos']
            x1, y1 = self.getCanvasPos(lego['lowX'], lego['lowY'])
            x2, y2 = self.getCanvasPos(lego['highX'], lego['highY'])

            self.drawRectangle(x1, y1, x2, y2)

            if value['innerSlots']:
                for inner in value['innerSlots']:
                    ix1, iy1 = self.getCanvasPos(inner['x1'], inner['y1'])
                    ix2, iy2 = self.getCanvasPos(inner['x2'], inner['y2'])
                    self.drawRectangle(ix1, iy1, ix2, iy2, "slot_inner")
            
            self.drawSlotExtras(key, x1, y1, x2, y2)

    def parseIniFile(self):
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

class SlotEditDialogue:
    def __init__(self, appInstance):
        self.appInstance = appInstance
        self.root = appInstance.master
        slot = appInstance.slots[appInstance.focusedSlot]
        self.slot = slot

        self.window = Toplevel(self.root)

        self.inputs = {
            "numCellsX" : {
                "name" : "X Number Cells",
                "value" : slot['numberX']
            },
            "numCellsY" : {
                "name" : "Y Number Cells",
                "value" : slot['numberY']
            },
            "legoWidth" : {
                "name" : "Cell Lego Width",
                "value" : slot['highX'] - slot['lowX']
            },
            "legoHeight" : {
                "name" : "Cell Lego Height",
                "value" : slot['highY'] - slot['lowY']
            },
            "startX" : {
                "name" : "X Start",
                "value" : slot['lowX']
            },
            "endX" : {
                "name" : "X End",
                "value" : slot['highX']
            },
            "startY" : {
                "name" : "Y Start",
                "value" : slot['lowY']
            },
            "endY" : {
                "name" : "Y End",
                "value" : slot['highY']
            }
        }

        count = 0
        for i in self.inputs.items():
            print(i)
            count += 1

    def save(self):
        return

    def createInput(self, name, value, count):
        Label(self.window, text = name).grid(row = count)
        entry = Entry(self.window)
        entry.grid(row = count, column = 1)
        return entry


root = Tk()
paintApp = SlotsIniApp(root)
root.mainloop()
