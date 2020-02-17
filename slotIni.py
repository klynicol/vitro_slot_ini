import sys
import shutil
import os
import math
import random
import time
import re
import copy
import requests
import json
from datetime import datetime
from functools import partial
from tkinter import *
import tkinter.font
import tkinter.simpledialog
import tkinter.messagebox

'''
@author Mark Wickline 2019-11-01

Small application that generates slots.ini files for vitro software.
Also pushes slot data into OT database `vitrodb_slots` table, to be used
with the OT/vitro module.
'''

class SlotsIniApp:

    iniFilePath = None
    otDatabaseLink  = 'http://ot.crystal-d.com/ot/index.php/vitro/saveSlots'

    # Positions and actions
    canvasAction = "draw_slot"
    leftBtn = "up"
    xPos = None
    yPos = None
    x1, y1, x2, y2 = None, None, None, None
    legoX1, legoY1 = 0, 0
    canvasX, canvasY = None, None # full width and height
    slotGroup = 0

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
    slots = [{},{}]
    # Key of the currrently focused slot
    focusedSlot = None

    boldFont = None
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

    def focusSlotGroup(self, group, btn):
        self.btnLayer1.config(bg="gray92")
        self.btnLayer2.config(bg="gray92")
        btn = getattr(self, btn)
        btn.config(bg="CadetBlue1")
        self.slotGroup = group
        self._initCanvas()

# Asks the user to input a slot name and checks if it's already used.
    def getSlotName(self, dialog = "Enter slot name"):
        name = tkinter.simpledialog.askstring("Name Slot", dialog)
        for slotGroup in self.slots:
            if name in slotGroup:
                name = self.getSlotName("Name already exists, enter a new name")
        return name

# Opens the slots.ini file and transposes the info into this.slots
    def parseIniFile(self):

        this_dir = os.path.dirname(os.path.realpath(__file__))
        self.iniFilePath = os.path.join(this_dir, self.INI_FILE)
        file = open(self.iniFilePath, "r")

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
        for key, value in slots.items():
            slotGroup = int(value['AppIniLayer'])
            startX = value['StartX'] - self.toolStartX
            startY = value['StartY'] - self.toolStartY
            self.slots[slotGroup][key] = {
                "legoPos" : {
                    "lowX" : round(startX / self.toolLegoUnit),
                    "lowY" : round(startY / self.toolLegoUnit),
                    "highX" : round((((value['DiffX'] * value['NumberX']) - (2 * self.toolLegoUnit)) + startX ) / self.toolLegoUnit),
                    "highY" : round((((value['DiffY'] * value['NumberY']) - (2 * self.toolLegoUnit)) + startY ) / self.toolLegoUnit)
                },
                "numberX" : int(value['NumberX']),
                "numberY" : int(value['NumberY']),
                "cellSizeX" : round(value['SlotSizeX'] / self.toolLegoUnit),
                "cellSizeY" : round(value['SlotSizeY'] / self.toolLegoUnit)
            }
            if self.slots[slotGroup][key]['numberX'] > 1 or self.slots[slotGroup][key]['numberY'] > 1:
                self.calcCells(slotGroup=slotGroup, key=key)
            else:
                self.slots[slotGroup][key]['innerSlots'] = []
        file.close()
        #Make a backup of the original file with date stamp.
        today = datetime.now()
        backupFileName = "slots_" + today.strftime("%Y%m%d_%H_%M_%S") + ".ini"
        shutil.copyfile(self.INI_FILE, backupFileName)

# Creates an instance of SlotEditDialogue.
    def editSlot(self, name):
        self.focusedSlot = name
        SlotEditDialogue(self)

# Deletes a slot from this.slots
    def deleteSlot(self, slotGroup, name):
        del self.slots[slotGroup][name]
        self._initCanvas()

# Clear placeholders that were used to draw a slot
    def clearPlaceholders(self):
        if self.slotPlaceholder:
            self.canvas.delete(self.slotPlaceholder)
        if self.drawDistance:
            self.canvas.delete(self.drawDistance)

    def openNewSlotDialogue(self):
        SlotCreateDialogue(self)

# Create a new slot from the input dialog. Will basically ignore other slots.
# User needs to be very specific in their needs.
    def createSlotFromDialogue(self, name, startX, startY, cellWidth, cellHeight, numCells, limitX ):
        if name in self.slots[self.slotGroup]:
            return "Slot name is already in use"
        if not limitX:
            limitX = self.toolTotalLegoX

        # Maths??, not even once!
        xCount = min(math.floor(((limitX - startX) + 2) / ( cellWidth + 2)), numCells)
        highX = (xCount * cellWidth) + ( 2 * (xCount - 1)) + startX

        def calcY():
            yCount = math.ceil( numCells / xCount )
            highY = (yCount * cellHeight) + ( 2 * (yCount - 1)) + startY
            return yCount, highY

        #Initial Y calculations.   
        yCount, highY = calcY()
            
        #If high Y is greater than the bed allows, decrement the yCount and calculate again
        #Until we are good.
        while highY > self.toolTotalLegoY:
            numCells -= xCount
            yCount, highY = calcY()
            

        if highY > self.toolTotalLegoY:
            return "Slot cannot fit in the Y direction"

        self.slots[self.slotGroup][name] = {
            "legoPos" : {
                "lowX" : startX,
                "lowY" : startY,
                "highX" : highX,
                "highY" : highY
            },
            "numberX" : xCount,
            "numberY" : yCount,
            "cellSizeX" : cellWidth,
            "cellSizeY" : cellHeight
        }

        if cellWidth > 1 or cellHeight > 1:
            self.calcCells(key=name)
        self._initCanvas()
        return True

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

        # Save slot in the slots array
        self.slots[self.slotGroup][name] = {
            "legoPos" : {
                "lowX" : min(legoX1, legoX2),
                "lowY" : min(legoY1, legoY2),
                "highX" : max(legoX1, legoX2),
                "highY" : max(legoY1, legoY2)
            },
            "numberX" : 1,
            "numberY" : 1,
            "cellSizeX" : max(legoX1, legoX2) - min(legoX1, legoX2),
            "cellSizeY" : max(legoY1, legoY2) - min(legoY1, legoY2)
        }

        # Delete placeholder rectangle
        self.clearPlaceholders()
        self._initCanvas()

    def updateFocusedFromInputs(self, slotGroup, name, xCount, yCount, xStart, yStart, xEnd, yEnd):
        temp = {}
        temp['numberX'] = xCount
        temp['numberY'] = yCount
        temp['legoPos'] = {}
        temp['legoPos']['lowX'] = xStart
        temp['legoPos']['highX'] = xEnd
        temp['legoPos']['lowY'] = yStart
        temp['legoPos']['highY'] = yEnd
        temp['innerSlots'] = []

        if xCount > 1 or yCount > 1:
            if not self.calcCells(slot = temp):
                return False

        self.slots[slotGroup][name] = temp

        self._initCanvas()
        return True

# Adds cells to a slot based on the slot information, returns the cells created.
    def calcCells(self, slotGroup = None, key = None, slot = None):
        if not slotGroup:
            slotGroup = self.slotGroup
        if not key:
            key = self.focusedSlot
        if not slot:
            slot = self.slots[slotGroup][key]

        slotWidth = slot['legoPos']['highX'] - slot['legoPos']['lowX']
        slotHeight = slot['legoPos']['highY'] - slot['legoPos']['lowY']
        x_spacers = (slot['numberX'] - 1) * 2
        y_spacers = (slot['numberY'] - 1) * 2
        #Check if the number is divisible in both directions
        if (slotWidth - x_spacers) % slot['numberX'] != 0 or (slotHeight - y_spacers) % slot['numberY'] != 0:
            tkinter.messagebox.showinfo("Fault", "Slot is not devisable by count")
            return False
        
        # We are good, build the cell dictionaries and push to a new cells array
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
        slot['cellSizeX'] = x_size #this is an update
        slot['cellSizeY'] = y_size #this is an update
        return cells

# Stuff drawn on the canvas that is associated with the slot.
    def drawSlotExtras(self, name, lowX, lowY, cellWidth, cellHeight):
        legoString = "{x}/{y}".format(x=cellWidth, y=cellHeight)
        rlString = "{x:.2f}/{y:.2f}".format(
            x= cellWidth * self.toolLegoUnit, 
            y = cellHeight * self.toolLegoUnit
        )
        button = Button(self.master, text = name, command = partial(self.editSlot, name), padx=15, font=self.boldFont)
        btnWindow = self.canvas.create_window( lowX + 22, lowY - 70, anchor=NW, window = button)
        legoText = self.canvas.create_text(lowX + 47, lowY - 25, text=legoString, font=self.boldFont)
        rlText = self.canvas.create_text(lowX + 51, lowY - 10, text=rlString, font=self.boldFont)
        return button, btnWindow, legoText, rlText

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
    def drawLine(self, x1, y1, x2, y2, fill="black"):
        self.canvas.create_line(x1, y1, x2, y2, fill=fill)


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
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

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
        for key, value in self.slots[self.slotGroup].items():

            lego = value['legoPos']
            x1, y1 = self.getCanvasPos(lego['lowX'], lego['lowY'])
            x2, y2 = self.getCanvasPos(lego['highX'], lego['highY'])

            self.drawRectangle(x1, y1, x2, y2)

            if 'innerSlots' in value and value['innerSlots']:
                for inner in value['innerSlots']:
                    ix1, iy1 = self.getCanvasPos(inner['lowX'], inner['lowY'])
                    ix2, iy2 = self.getCanvasPos(inner['highX'], inner['highY'])
                    self.drawRectangle(ix1, iy1, ix2, iy2, "slot_inner")
            
            self.drawSlotExtras(key, x1, y1, value['cellSizeX'], value['cellSizeY'])

    def getRealLifePos(self, legoX, legoY):
        x = self.toolStartX + (legoX * self.toolLegoUnit)
        y = self.toolStartY + (legoY * self.toolLegoUnit)
        return x, y

    def saveIniFile(self):
        file = open(self.iniFilePath, 'w')
        file.truncate(0)
        # Machine Name
        text = "[Machine_Name]\nName = {name}".format(name = self.machineName)
        
        # Build slots
        otDatabase = { "tool" : self.machineName, "slots" : [] }
        group = 0
        for slotGroup in self.slots:
            for key, data in slotGroup.items():

                #Dictionary entry for order tracker database.
                otDatabase['slots'].append({
                    'slot_name' : key,
                    'cell_width' : data['cellSizeX'],
                    'cell_height' : data['cellSizeY'],
                    'cell_count_x' : data['numberX'],
                    'cell_count_y' : data['numberY'],
                    'start_x' : data['legoPos']['lowX'],
                    'start_y' : data['legoPos']['lowY'],
                    'layer' : group
                })

                startX, startY = self.getRealLifePos(data['legoPos']['lowX'], data['legoPos']['lowY'])
                numberX, numberY = data['numberX'], data['numberY']
                highX, highY = self.getRealLifePos(data['legoPos']['highX'], data['legoPos']['highY'])
                #we are assuming two legos will be used between cells at the moment
                difX = ((highX - startX) + ( 2 * self.toolLegoUnit )) / numberX
                difY = ((highY - startY) + ( 2 * self.toolLegoUnit )) / numberY
                slotSizeX = difX - ( 2 * self.toolLegoUnit )
                slotSizeY = difY - ( 2 * self.toolLegoUnit )

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
AppIniLayer = {layer}
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
                    difY = difY,
                    layer = group
                )
            group += 1

        file.write(text)
        file.close()
        
        #Make a call to the order tracker database to store the slots in `vitrobd_slots`
        response = requests.post(self.otDatabaseLink, data=json.dumps(otDatabase))
        if(response.headers.get('content-type') == 'application/json'):
            response_data = response.json()
            if not response_data['status']:
                tkinter.messagebox.showinfo("OT Connection", "Something went wrong while updating order tracker, please contact Mark Wickline!")
        else:
            tkinter.messagebox.showinfo("OT Connection", "Something went wrong while updating order tracker, please contact Mark Wickline!")

# Initialize
    def __init__(self, root):

        # Parse settings file to set tool specific parameters
        file = open("slotApp.ini", "r")
        for line in file:
            setting = line.split("=")
            setattr(self, setting[0].strip(), float(setting[1].strip()))
        file.close()

        root.title("Slot INI App 1.0.1")
        self.master = root
        pad = 70
        fullX = root.winfo_screenwidth()
        fullY = root.winfo_screenheight()
        self.boldFont = tkinter.font.Font(family="Helvetica", size=12, weight="bold")

        root.geometry("{0}x{1}+0+0".format(
            fullX-pad, fullY-pad))

        btnContainer = Frame(root, padx=20)
        btnContainer.pack(fill=X)

        btnZoomOut = Button(btnContainer, command = self.zoomOut, padx=20)
        btnZoomOut['text'] = "-"
        btnZoomOut.pack(side=LEFT)

        btnZoomIn = Button(btnContainer, command = self.zoomIn, padx=20)
        btnZoomIn['text'] = "+"
        btnZoomIn.pack(side=LEFT)

        # btnConMid = Frame(btnContainer)
        # btnConMid.pack(side=TOP, expand=False)

        self.btnLayer1 = Button(btnContainer, command = lambda: self.focusSlotGroup(0, "btnLayer1"))
        self.btnLayer1.config(text="Layer 1", bg="CadetBlue1")
        self.btnLayer1.pack(side=LEFT)

        self.btnLayer2 = Button(btnContainer, command = lambda: self.focusSlotGroup(1, "btnLayer2"))
        self.btnLayer2.config(text="Layer 2")
        self.btnLayer2.pack(side=LEFT)

        btnAddSlot = Button(btnContainer, command = self.openNewSlotDialogue)
        btnAddSlot.config(text="Add New slot")
        btnAddSlot.pack(side=LEFT)


        self.coords = Text(btnContainer, height=1, width=20)
        self.coords.pack(side=RIGHT)

        self.btnSave = Button(btnContainer, command = self.saveIniFile, width=20, bg="green")
        self.btnSave["text"] = "Save"
        self.btnSave.pack( side = RIGHT)


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

class SlotEditDialogue:
    def __init__(self, appInstance):
        self.appInstance = appInstance
        self.window = Toplevel(appInstance.master)
    
        self.slotGroup = copy.copy(self.appInstance.slotGroup)
        self.slotName = copy.copy(self.appInstance.focusedSlot)
        self.window.title(self.slotName)

        self.inputs = {
            "numCellsX" : {
                "name" : "X Number Cells",
                "type" : "entry"
            },
            "numCellsY" : {
                "name" : "Y Number Cells",
                "type" : "entry"
            },
            "legoWidth" : {
                "name" : "Slot Width",
                "type" : "label"
            },
            "legoHeight" : {
                "name" : "Slot Height",
                "type" : "label"
            },
            "startX" : {
                "name" : "X Start",
                "type" : "entry"
            },
            "endX" : {
                "name" : "X End",
                "type" : "entry"
            },
            "startY" : {
                "name" : "Y Start",
                "type" : "entry"
            },
            "endY" : {
                "name" : "Y End",
                "type" : "entry"
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
        slot = self.appInstance.slots[self.slotGroup][self.slotName]
        self.inputs['numCellsX']['value'] = slot['numberX']
        self.inputs['numCellsY']['value'] = slot['numberY']
        self.inputs['legoWidth']['value'] = slot['legoPos']['highX'] - slot['legoPos']['lowX']
        self.inputs['legoHeight']['value'] = slot['legoPos']['highY'] - slot['legoPos']['lowY']
        self.inputs['startX']['value'] = slot['legoPos']['lowX']
        self.inputs['endX']['value'] = slot['legoPos']['highX']
        self.inputs['startY']['value'] = slot['legoPos']['lowY']
        self.inputs['endY']['value'] = slot['legoPos']['highY']
        for key, value in self.inputs.items():
            if value['type'] == 'label':
                value['input'].config(state=NORMAL)
            value['input'].delete(0, END)
            value['input'].insert('end', value['value'])
            if value['type'] == 'label':
                value['input'].config(state="readonly")


    def save(self):
        self.appInstance.updateFocusedFromInputs(
            self.slotGroup,
            self.slotName,
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
            self.appInstance.deleteSlot(self.slotGroup, self.slotName)
            self.window.destroy()

    def createInput(self, name, row):
        Label(self.window, text = name).grid(row = row)
        elem = Entry(self.window)
        elem.grid( row = row, column = 1)
        return elem

class SlotCreateDialogue:
    def __init__(self, appInstance):
        self.appInstance = appInstance
        self.window = Toplevel(appInstance.master)
        self.window.title("Add Slot")

        # Let's create some inputs.
        row = 0
        self.iName = self.createInput("Slot Name", row)
        row += 1
        self.iStartX = self.createInput("Start X", row)
        row += 1
        self.iStartY = self.createInput("Start Y", row)
        row += 1
        self.iCellWidth = self.createInput("Cell Width", row)
        row += 1
        self.iCellHeight = self.createInput("Cell Height", row)
        row += 1
        self.iCellCount = self.createInput("Cell Count", row)
        row += 1
        self.iCellLimit = self.createInput("Cell Limit X (optional)", row)
        row += 1

        # Create save and cancel buttons
        row += 1
        self.saveBtn = Button(self.window, text = "Create", command = self.save)
        self.saveBtn.grid(row=row)

    def save(self):
        response = self.appInstance.createSlotFromDialogue(
            self.iName.get(),
            int(self.iStartX.get()),
            int(self.iStartY.get()),
            int(self.iCellWidth.get()),
            int(self.iCellHeight.get()),
            int(self.iCellCount.get()),
            int(self.iCellLimit.get() or 0)
        )
        if response is True:
            self.window.destroy()
        else:
            tkinter.messagebox.showinfo(response)

    def createInput(self, name, row):
        Label(self.window, text = name).grid(row = row)
        entry = Entry(self.window)
        entry.grid(row = row, column = 1)
        return entry


root = Tk()
paintApp = SlotsIniApp(root)
root.mainloop()
