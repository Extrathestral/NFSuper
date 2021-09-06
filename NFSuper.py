from socket import *
class Interpreter():
    currentIndex = 0
    cells = []
    stack = []
    bfsocket = None
    selectedCell = 0
    debug = False
    skip = 0
    outputStr = ""
    inNetLoop = False
    
    def __init__(self, debug=False, live_output = True):
        self.cells = [0]
        self.dbg = debug
        self.liveOutput = live_output
    
    def move_right(self):
        if len(self.cells) - 1 < self.selectedCell + 1:
            self.cells.append(0)
            self.selectedCell += 1
        else:
            self.selectedCell += 1
    
    def move_left(self):
        if self.selectedCell == 0:
            raise IndexError("Attempt to move left, despite being on index 0.")
        else:
            self.selectedCell -= 1
    
    def add(self):
        val1 = self.cells[self.selectedCell]
        if val1 == 255:
            self.cells[self.selectedCell] = 0
        else:
            self.cells[self.selectedCell] = self.cells[self.selectedCell] + 1
    
    def subtract(self):
        val1 = self.cells[self.selectedCell]
        if val1 == 0:
            self.cells[self.selectedCell] = 255
        else:
            self.cells[self.selectedCell] = self.cells[self.selectedCell] - 1
    
    def push(self):
        self.stack.insert(0, self.cells[self.selectedCell])
    
    def pop(self):
        if len(self.stack) <= 0:
            raise IndexError("Tried to pop element when stack was empty.")
        self.cells[self.selectedCell] = self.stack.pop(0)
    
    def output(self):
        self.outputStr += chr(self.cells[self.selectedCell])
        if self.liveOutput and self.cells[self.selectedCell] != 0:
            print(chr(self.cells[self.selectedCell]), end='')
    
    def getOutput(self):
        return self.outputStr
    
    def byteInput(self):
        self.cells[self.selectedCell] += ord(input("")[0])
    
    def getCells(self):
        return self.cells

    def getSelectedCell(self):
        return self.selectedCell

    def getIPFromStack(self):
        ipArr = [str(self.stack.pop(0)) for i in range(4)]
        return '.'.join(ipArr)
    
    def getPortFromStack(self):
        port = [self.stack.pop(0) for i in range(2)]
        portBin = [bin(i)[2:] for i in port]
        portBinStr = str(portBin[0])+str(portBin[1])
        return int(portBinStr,2)

    def connect(self):
        ipArr = self.getIPFromStack()
        port = self.getPortFromStack()
        if self.bfsocket != None:
            self.bfsocket.shutdown(SHUT_RDWR)
            self.bfsocket.close()
        self.bfsocket = socket(AF_INET,SOCK_STREAM)
        self.bfsocket.connect((ipArr,port))
    
    def disconnect(self):
        if self.bfsocket != None:
            self.bfsocket.shutdown(SHUT_RDWR)
            self.bfsocket.close()
            self.bfsocket = None

    def listen(self):
        port = self.getPortFromStack()
        if self.bfsocket != None:
            self.bfsocket.shutdown(SHUT_RDWR)
            self.bfsocket.close()
        self.bfsocket = socket(AF_INET, SOCK_STREAM)
        self.bfsocket.bind(("0.0.0.0",port))
        self.bfsocket.listen(1)
        self.bfsocket = self.bfsocket.accept()[0]
        ipAddr, _ = self.bfsocket.getpeername()
        ipList = ipAddr.split(".")[::-1]
        [self.stack.insert(0, int(i)) for i in ipList]
    
    def send(self):
        if self.bfsocket != None:
            self.bfsocket.send(chr(self.cells[self.selectedCell]).encode())

    def receive(self, bf):
        if self.bfsocket != None:
            try:
                data = int(ord(self.bfsocket.recv(1).decode()))
                self.cells[self.selectedCell] = data
            except:
                self.bfsocket.close()
                self.bfsocket = None
        else:
            startIndex = bf[:self.currentIndex][::-1].index("{")
            self.currentIndex -= startIndex + 2
            

    def getStack(self):
        return self.stack

    def peek(self):
        if len(self.stack) <= 0:
            raise IndexError("Tried to peek element when stack was empty.")
        self.cells[self.selectedCell] = self.stack[0]

    def enterNetLoop(self, bf):
        if self.inNetLoop:
            raise SyntaxError("Cannot enter multi-layered netLoop, feature not implemented because dumb.")

        if self.bfsocket == None:
            endIndex = bf.index("}", self.currentIndex)
            self.currentIndex = endIndex
        else:
            self.inNetLoop = True
    
    def exitNetLoop(self, bf):
        if self.bfsocket != None:
            startIndex = bf[:self.currentIndex][::-1].index("{")
            self.currentIndex -= startIndex+2
            self.inNetLoop = False
        else:
            self.inNetLoop = False

    def enterLoop(self, bf):
        if self.cells[self.selectedCell] == 0:
            endIndex = bf.index("]")
            self.currentIndex = endIndex
    
    def exitLoop(self, bf):
        if self.cells[self.selectedCell] != 0:
            startIndex = bf[:self.currentIndex][::-1].index("[")
            self.currentIndex -= startIndex+1
    
    def bf_interpret(self, bf, console_input=True, manualInput=""):
        validSquares = 0
        validCurly = 0
        for i in bf:
            if i == "[":
                validSquares += 1
            elif i == "]":
                validSquares -= 1
            elif i == "{":
                validCurly += 1
            elif i == "}":
                validCurly -= 1
        if validSquares != 0:
            raise SyntaxError("Mismatched square brackets.")
        if validCurly != 0:
            raise SyntaxError("Mismatched curly brackets.")
        while self.currentIndex < len(bf):            
            if self.skip > 0:
                self.skip -= 1
                self.currentIndex += 1
                continue
            j = bf[self.currentIndex]

            argswitcher = {
                "[": self.enterLoop,
                "]": self.exitLoop,
                "{": self.enterNetLoop,
                "v": self.receive,
                "}": self.exitNetLoop
            }
            switcher = {
                ">": self.move_right,
                "<": self.move_left,
                "+": self.add,
                "-": self.subtract,
                ",": self.byteInput,
                "(": self.push,
                ")": self.pop,
                "/": self.peek,
                "~": self.connect,
                "`": self.disconnect,
                "^": self.send,
                "=": self.listen,
                
            }
            if j == ".":
                if console_input:
                    self.output()
                else:
                    if len(manualInput) > 0:
                        x = manualInput[0]
                        manualInput = manualInput[1:]
                    else:
                        raise SyntaxError("You must specify input as manualInput if you aren't using console_input")
            else:
                result = switcher.get(j,None)
                if result == None:
                    result = argswitcher.get(j, None)
                    if result == None:
                        self.currentIndex += 1
                        continue
                    result(bf)
                else:
                    result()
            if self.inNetLoop:
                if self.bfsocket == None:
                    self.inNetLoop = False
                    startIndex = bf[:self.currentIndex][::-1].index("{")
                    self.currentIndex -= startIndex + 1
            self.currentIndex += 1
