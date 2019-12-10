import sys
import math
import random
import time
import re
from functools import partial
from tkinter import *
import tkinter.font
import tkinter.simpledialog
import tkinter.messagebox

# Define my class


class SlotsIniApp:

    iniFile = None

    # Positions and actions
    canvasAction = "draw_slot"
    leftBtn = "up"
    xPos = None
    yPos = None
    x1, y1, x2, y2 = None, None, None, None
    legoX1, legoY1 = 0, 0
    canvasX, canvasY = None, None # full width and height

    # Window Elements
    master = None
    btnContainer, canvas, slotPlaceholder, drawDistance = None, None, None, None
    editDialog = None #Object created when editing a slot
    scale = 1

    # Variables specific to the laser machine, pulled from slotApp.ini
    toolStartX = None
    toolStartY = None
    toolStartZ = None
    toolTotalLegoX = None
    toolTotalLegoY = None
    toolLegoUnit = None
    machineName = "Change Me"

    # Current slots on the canvas
    slots = {}
    # Key of the currrently focused slot
    focusedSlot = None

    boldFont = None
    # The definitive actual size of 1 lego (mm)
    LEGO_UNIT = 7.985
    # A one to one relation with lego unit to draw "snapping" lines
    CANVAS_UNIT = 12
    SCALE_UP = 1.1
    SCALE_DOWN = 0.9

    INI_FILE = "slots.ini"

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
        self.legoX1, self.legoY1 = self.getLegoPos(self.x1, self.y1)

# Catch Mouse Move
    def motion(self, event=None):
        self.xPos = self.canvas.canvasx(event.x)
        self.yPos = self.canvas.canvasy(event.y)
        # Print lego position on the menu
        legoX, legoY = self.getLegoPos(self.xPos, self.yPos)
        self.coords.delete(1.0,END)
        self.coords.insert(INSERT, "{x},{y}".format(x=legoX, y=legoY))

        if self.leftBtn == "down":
            self.clearPlaceholders()
            # Draw a placeholder rectangle as a visual element
            self.slotPlaceholder = self.drawRectangle(
                self.x1, self.y1, self.xPos, self.yPos, "slot_placeholder")
            # Print the length and width of the cell that will be drawn
            difX = abs(self.legoX1 - legoX)
            difY = abs(self.legoY1 - legoY)
            self.drawDistance = self.canvas.create_text(
                self.xPos, self.yPos - 10, text = "{x}, {y}".format(x=difX, y=difY), font=self.boldFont, fill="green")

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

# Opens the slots.ini file and transposes the info into this.slots
    def parseIniFile(self):
        file = open(self.INI_FILE, "r")

        block = None
        slots = {} # Temp Bin to throw slot information into
        for line in file:
            if re.match(r'^\[', line): # Are we on a block line
                block = re.search(r'\[(.*?)\]', line).group(1)
            elif block == 'Machine_Name': # Next line is machine name
                self.machineName = line.split('=')[1].strip()
                block = None
            elif block and line.strip() != "": # We have information to parse
                setting = line.split('=')
                if not block in slots:
                    slots[block] = {}
                key = setting[0].strip()
                slots[block][key] = float(setting[1].strip())

        # Iterate over newly created slots and build slots for the class
        print(slots)
        for key, value in slots.items():
            self.slots[key] = {
                "legoPos" : {
                    "lowX" : round(value['StartX'] / self.toolLegoUnit),
                    "lowY" : round(value['StartY'] / self.toolLegoUnit),
                    "highX" : round((value['SlotSizeX'] + value['StartX']) / self.toolLegoUnit),
                    "highY" : round((value['SlotSizeY'] + value['StartY']) / self.toolLegoUnit)
                },
                "numberX" : int(value['NumberX']),
                "numberY" : int(value['NumberY'])
            }
            self.calcCells(key)
            self.createSlotExtras(key)

        file.close()

# Creates an instance of SlotEditDialogue.
    def editSlot(self, name):
        self.focusedSlot = name
        # Create a new dialogue object
        ''' Not sure what the auto cleanup is like when instatiating new object :-/
        if self.editDialog:
            del self.editDialog
        self.editDialog = SlotEditDialogue(self)
        '''
        SlotEditDialogue(self)

# Deletes a slot from this.slots
    def deleteSlot(self, slot = None):
        if not slot:
            slot = self.focusedSlot
        del self.slots[slot]
        self._initCanvas()

# Clear placeholders that were used to draw a slot
    def clearPlaceholders(self):
        if self.slotPlaceholder:
            self.canvas.delete(self.slotPlaceholder)
        if self.drawDistance:
            self.canvas.delete(self.drawDistance)

# Add a new slot to this.slots
    def addSlot(self, event=None):
        name = self.getSlotName()
        if not name:
            # Delete placeholder rectangle
            self.clearPlaceholders()
            return

        # Snap x and y to nearest coordinates
        legoX1, legoY1 = self.getLegoPos(self.x1, self.y1)
        legoX2, legoY2 = self.getLegoPos(self.x2, self.y2)

        # Draw the rectangle
        canvasX1, canvasY1 = self.getCanvasPos(legoX1, legoY1)
        canvasX2, canvasY2 = self.getCanvasPos(legoX2, legoY2)
        rectangle = self.drawRectangle(canvasX1, canvasY1, canvasX2, canvasY2)

        # Add a new Frame on the canvas over the new slot
        button, buttonWindow = self.drawSlotExtras(
            name, canvasX1, canvasY1, canvasX2, canvasY2)

        # Save slot in the slots array
        self.slots[name] = {
            "canvasElements" : {
                "button" : button,
                "button_window" : buttonWindow,
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
        self.clearPlaceholders()

    def createSlotExtras(self, key, slot = None):
        if not slot:
            slot = self.slots[key]
        canvasX1, canvasY1 = self.getCanvasPos(slot['legoPos']['lowX'], slot['legoPos']['lowY'])
        canvasX2, canvasY2 = self.getCanvasPos(slot['legoPos']['highX'], slot['legoPos']['highY'])
        rectangle = self.drawRectangle(canvasX1, canvasY1, canvasX2, canvasY2)

        # Add a new Frame on the canvas over the new slot
        button, buttonWindow = self.drawSlotExtras(
            key, canvasX1, canvasY1, canvasX2, canvasY2)

        # Save slot in the slots array
        slot["canvasElements"] = {
            "button" : button,
            "button_window" : buttonWindow,
            "rectangle" : rectangle,
            "lego_text" : None, #TODO
            "rl_size" : None #TODO, real life size in mm
        }

    def updateFocusedFromInputs(self, xCount, yCount, xStart, yStart, xEnd, yEnd):
        slot = self.slots[self.focusedSlot]

        # Calculate the width and height of the slot in legos
        legoWidth = xEnd - xStart
        legoHeight = yEnd - yStart

        if xCount == 1 and yCount == 1:
            cells = None
        else:
            cells = self.calcCells(xStart, yStart, xCount, yCount, legoWidth, legoHeight)
            if not cells:
                tkinter.messagebox.showinfo("Fault", "Slot is not devisable by count")
                return False
        
        slot['innerSlots'] = cells
        slot['numberX'] = xCount
        slot['numberY'] = yCount
        slot['legoPos']['lowX'] = xStart
        slot['legoPos']['highX'] = xEnd
        slot['legoPos']['lowY'] = yStart
        slot['legoPos']['highY'] = yEnd

        self._initCanvas()
        return True

# Returns an array of lego dimension for drawing cells inside a slot
    #def calcCells(self, xStart, yStart, xCount, yCount, slotWidth, slotHeight):
    def calcCells(self, key, slot = None):
        if not slot:
            slot = self.slots[key]
        slotWidth = slot['legoPos']['highX'] - slot['legoPos']['lowX']
        slotHeight = slot['legoPos']['highY'] - slot['legoPos']['lowY']
        x_spacers = (slot['numberX'] - 1) * 2
        y_spacers = (slot['numberY'] - 1) * 2
        #Check if the number is divisible in both directions
        if (slotWidth - x_spacers) % slot['numberX'] != 0 or (slotHeight - y_spacers) % slot['numberY'] != 0:
            return False
        
        # We are good, build the cell dictionaries and push to the array
        cells = []
        x_size = (slotWidth - x_spacers) / slot['numberX']
        y_size = (slotHeight - y_spacers) / slot['numberY']
        x = slot['legoPos']['lowX']
        for xx in range(0, slot['numberX']):
            y = slot['legoPos']['lowY']
            for yy in range(0, slot['numberY']):
                cells.append({
                    "lowX" : x,
                    "highX" : x + x_size,
                    "lowY" : y,
                    "highY" : y + y_size
                })
                y += y_size + 2
            x += x_size + 2
        slot['innerSlots'] = cells
        # x_spacers = (xCount - 1) * 2
        # y_spacers = (yCount - 1) * 2
        # #Check if the number is divisible in both directions
        # if (slotWidth - x_spacers) % xCount != 0 or (slotHeight - y_spacers) % yCount != 0:
        #     return False
        
        # # We are good, build the cell dictionaries and push to the array
        # cells = []
        # x_size = (slotWidth - x_spacers) / xCount
        # y_size = (slotHeight - y_spacers) / yCount
        # x = xStart
        # for xx in range(0, xCount):
        #     y = yStart
        #     for yy in range(0, yCount):
        #         cells.append({
        #             "lowX" : x,
        #             "highX" : x + x_size,
        #             "lowY" : y,
        #             "highY" : y + y_size
        #         })
        #         y += y_size + 2
        #     x += x_size + 2
        # return cells

    def drawSlotExtras(self, name, x1, y1, x2, y2):
        lowerX = min(x1, x2)
        lowerY = min(y1, y2)
        slotMiddleX = abs(x1 - x2) / 2 + lowerX

        button = Button(self.master, text = name, command = partial(self.editSlot, name))
        btnWindow = self.canvas.create_window( slotMiddleX, lowerY + 30, anchor=NW, window = button)
        return button, btnWindow

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
            bkgColor = "spring green"

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
                    ix1, iy1 = self.getCanvasPos(inner['lowX'], inner['lowY'])
                    ix2, iy2 = self.getCanvasPos(inner['highX'], inner['highY'])
                    self.drawRectangle(ix1, iy1, ix2, iy2, "slot_inner")
            
            self.drawSlotExtras(key, x1, y1, x2, y2)

    def getRealLifePos(self, legoX, legoY):
        x = self.toolStartX + (legoX * self.toolLegoUnit)
        y = self.toolStartY + (legoY * self.toolLegoUnit)
        return x, y

    def saveIniFile(self):
        file = open(self.INI_FILE, "r+")
        file.truncate(0)
        # Machine Name
        text = "[Machine_Name]\nName = {name}".format(name = self.machineName)
        
        # Build slots
        for key, data in self.slots.items():

            startX, startY = self.getRealLifePos(data['legoPos']['lowX'], data['legoPos']['lowY'])
            numberX, numberY = data['numberX'], data['numberY']
            highX, highY = self.getRealLifePos(data['legoPos']['highX'], data['legoPos']['highY'])
            slotSizeX = highX - startX
            slotSizeY = highY - startY
            #we are assuming two legos will be used between cells at the moment
            difX = slotSizeX + ( 2 * self.toolLegoUnit)
            difY = slotSizeY + ( 2 * self.toolLegoUnit)

            # Preformated format, don't mess with this
            text += '''

[{name}]
StartX = {startX}
StartY = {startY}
StartZ = {startZ}
NumberX = {numberX}
NumberY = {numberY}
SlotSizeX = {slotSizeX}
SlotSizeY = {slotSizeY}
DiffX = {difX}
DiffY = {difY}
'''.format(
                name = key,
                startX = startX,
                startY = startY,
                startZ = self.toolStartZ,
                numberX = numberX,
                numberY = numberY,
                slotSizeX = slotSizeX,
                slotSizeY = slotSizeY,
                difX = difX,
                difY = difY
            )

        print(text)
        file.write(text)
        file.close()


# Initialize
    def __init__(self, root):

        # Parse settings file to set tool specific parameters
        file = open("slotApp.ini", "r")
        for line in file:
            setting = line.split("=")
            setattr(self, setting[0].strip(), float(setting[1].strip()))
        file.close()

        self.master = root
        pad = 70
        fullX = root.winfo_screenwidth()
        fullY = root.winfo_screenheight()
        self.boldFont = tkinter.font.Font(family="Helvetica", size=12, weight="bold")

        root.geometry("{0}x{1}+0+0".format(
            fullX-pad, fullY-pad))

        self.btnContainer = Frame(root)
        self.btnContainer.pack()

        self.button1 = Button(self.btnContainer, command = self.saveIniFile)
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

        
        
        self.parseIniFile()

        self._initCanvas()

    def __del__(self):
        if self.iniFile:
            self.iniFile.close()

class SlotEditDialogue:
    def __init__(self, appInstance):
        self.appInstance = appInstance
        self.window = Toplevel(appInstance.master)

        self.inputs = {
            "numCellsX" : {
                "name" : "X Number Cells"
            },
            "numCellsY" : {
                "name" : "Y Number Cells"
            },
            "legoWidth" : {
                "name" : "Cell Lego Width"
            },
            "legoHeight" : {
                "name" : "Cell Lego Height"
            },
            "startX" : {
                "name" : "X Start"
            },
            "endX" : {
                "name" : "X End"
            },
            "startY" : {
                "name" : "Y Start"
            },
            "endY" : {
                "name" : "Y End",
            }
        }

        row = 0
        for key, value in self.inputs.items():
            self.inputs[key]['input'] = self.createInput(value['name'], row)
            row += 1

        self.updateInputs()

        # Create save and cancel buttons
        row += 1
        self.saveBtn = Button(self.window, text = "Update", command = self.save)
        self.saveBtn.grid(row = row)
        # Create delete button
        self.deleteBtn = Button(self.window, text = "Delete", command = self.delete)
        self.deleteBtn.grid(row = row, column = 1)

# Re-pulls data from the main class into the dialogue.
    def updateInputs(self):
        slot = self.appInstance.slots[self.appInstance.focusedSlot]
        self.inputs['numCellsX']['value'] = slot['numberX']
        self.inputs['numCellsY']['value'] = slot['numberY']
        self.inputs['legoWidth']['value'] = slot['legoPos']['highX'] - slot['legoPos']['lowX']
        self.inputs['legoHeight']['value'] = slot['legoPos']['highY'] - slot['legoPos']['lowY']
        self.inputs['startX']['value'] = slot['legoPos']['lowX']
        self.inputs['endX']['value'] = slot['legoPos']['highX']
        self.inputs['startY']['value'] = slot['legoPos']['lowY']
        self.inputs['endY']['value'] = slot['legoPos']['highY']
        for key, value in self.inputs.items():
            value['input'].delete(0, END)
            value['input'].insert(0, value['value'])


    def save(self):
        self.appInstance.updateFocusedFromInputs(
            int(self.inputs['numCellsX']['input'].get()),
            int(self.inputs['numCellsY']['input'].get()),
            int(self.inputs['startX']['input'].get()),
            int(self.inputs['startY']['input'].get()),
            int(self.inputs['endX']['input'].get()),
            int(self.inputs['endY']['input'].get())
        )
        self.updateInputs()



    def delete(self):
        answer = tkinter.messagebox.askyesno("Delete", "Are you sure you want to delete this slot?")
        if answer:
            self.appInstance.deleteSlot()

    def createInput(self, name, row):
        Label(self.window, text = name).grid(row = row)
        entry = Entry(self.window)
        entry.grid(row = row, column = 1)
        return entry


root = Tk()
paintApp = SlotsIniApp(root)
root.mainloop()
