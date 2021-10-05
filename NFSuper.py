import socket
import ssl
import io
import time
import os
import sys

bracketTypes = [['[',']'], ['{', '}']]
byteConv = lambda x: bin(x)[2:].zfill(8)

class Tape:
    def __init__(self):
        self.pos = 0
        self.tapeData = {}

    def moveLeft(self, amount=1):
        if self.pos > 0: self.pos -= 1
        else: raise IndexError("Attempted to move left at position 0.")
    
    def moveRight(self, amount=1):
        self.pos += 1

    def increment(self, amount=1):
        if self.pos not in self.tapeData.keys(): self.tapeData[self.pos] = 1
        else: self.tapeData[self.pos] = (self.tapeData[self.pos]+1)%256
    
    def decrement(self, amount=1):
        if self.pos not in self.tapeData.keys(): self.tapeData[self.pos] = 255
        else: self.tapeData[self.pos] = (self.tapeData[self.pos]-1)%256
    
    def read(self):
        if self.pos not in self.tapeData.keys(): return 0
        else: return self.tapeData[self.pos]

    def setValue(self, value):
        if not isinstance(value,int):
            value = ord(value)
        self.tapeData[self.pos] = value



class Interpreter:
    def __init__(self, code='', inp='', inputMode=1):
        self.tape = Tape()
        self.callStack = []
        self.stack = []
        self.descriptors = []
        self.code = str(code)
        self.instructionPointer = 0
        self.input = inp
        self.inputMode = inputMode
        self.currentDescriptor = None
    
    def getIPFromStack(self):
        if len(self.stack) < 4: raise IndexError(f"Invalid stack size for getting IP, expected >=4, got {len(self.stack)}")
        return f"{self.stack.pop()}.{self.stack.pop()}.{self.stack.pop()}.{self.stack.pop()}"
        
    def getPortFromStack(self):
        if len(self.stack) < 2: raise IndexError(f"Invalid stack size for getting IP, expected >=4, got {len(self.stack)}")
        return int(byteConv(self.stack.pop())+byteConv(self.stack.pop()), 2)

    def TCPConnect(self):
        IPAddr = self.getIPFromStack()
        port = self.getPortFromStack()

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect((IPAddr, port))
        self.descriptors.append(s)
        self.currentDescriptor = len(self.descriptors)-1

    def SSLConnect(self):
        port = self.getPortFromStack()
        hostname = ''
        stackVal = self.stack.pop()
        while stackVal != 0:
            hostname += chr(stackVal)
            stackVal = self.stack.pop()
        IPAddr = socket.gethostbyname(hostname)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.load_verify_locations('cacert.pem')
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        ssock = context.wrap_socket(sock, server_hostname=hostname)
        ssock.connect((IPAddr, port))
        ssock.settimeout(2)
        self.descriptors.append(ssock)
        self.currentDescriptor = len(self.descriptors)-1
    
    def fileOpen(self):
        filename = ""
        stackVal = self.stack.pop()
        while stackVal != 0:
            filename += chr(stackVal)
            stackVal = self.stack.pop()
        if not os.path.exists(filename):
            open(filename, 'x')
        infile = open(filename, 'r+')
            
        self.descriptors.append(infile)
        self.currentDescriptor = len(self.descriptors)-1

    def createListenServer(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('0.0.0.0', self.getPortFromStack()))
        sock.listen(0)
        conn, addr = sock.accept()
        IPAddr = addr[0]
        IPArr = [int(i) for i in IPAddr.split(".")]
        [self.stack.append(i) for i in IPArr[::-1]]
        self.descriptors.append(conn)
        self.currentDescriptor = len(self.descriptors) - 1

    def descWrite(self):
        desc = self.descriptors[self.currentDescriptor]
        if isinstance(desc, socket.socket):
            desc.send(chr(self.tape.read()).encode('utf-8'))
        elif isinstance(desc, io.TextIOBase):
            desc.write(chr(self.tape.read()))

    def descRead(self):
        desc = self.descriptors[self.currentDescriptor]
        if isinstance(desc, socket.socket):
            try:
                self.tape.setValue(ord(desc.recv(1).decode('utf-8')))
            except:
                self.tape.setValue(0)
        elif isinstance(desc, io.TextIOBase):
            readInfo = desc.read(1)
            if readInfo != '':
                self.tape.setValue(ord(readInfo))
            else:
                self.tape.setValue(0)

    def descClose(self): 
        self.descriptors.pop(self.currentDescriptor).close()

    def getNextClosedBracket(self, type=']'):
        remainingCode = self.code[self.instructionPointer+1:]
        depth = 0
        for i in range(len(remainingCode)):
            if remainingCode[i] == '[': depth += 1
            elif remainingCode[i] == ']':
                if depth > 0: depth -= 1
                else: return i
    
    def testDescriptor(self):
        desc = self.descriptors[self.currentDescriptor]
        if isinstance(desc, socket.socket):
            status = 1
            try:
                desc.send(b'')
            except:
                status = 0
            self.tape.setValue(status)
        elif isinstance(desc, io.TextIOBase):
            currentIndex = desc.tell()
            status = 1
            if currentIndex >= os.path.getsize(desc.name):
                status = 0
            self.tape.setValue(status)
    
    def delay(self):
        timeInMS = self.tape.read()
        time.sleep(timeInMS/1000)

    def selectDescriptor(self):
        index = self.tape.read()
        if index > len(self.descriptors)-1:
            raise IndexError(f"Tried to get a descriptor that doesn't exist, tried {index}, but max was {len(self.descriptors)-1}.")
        self.currentDescriptor = index

    def step(self):
        if self.instructionPointer == len(self.code): return 1
        instruction = self.code[self.instructionPointer]
        match instruction:
            case '+': self.tape.increment()
            case '-': self.tape.decrement()
            case '<': self.tape.moveLeft()
            case '>': self.tape.moveRight()
            case '.': print(chr(self.tape.read()),end='')
            case ',':
                match self.inputMode:
                    case 0:
                        if len(self.input) == 0: raise IndexError("Tried to read from input string, but input string was empty.")
                        self.tape.setValue(self.input.pop(0))
                    case 1: 
                        inp = input()
                        self.tape.setValue(inp[0] if len(inp) > 0 else '\n')
            case '[':
                self.callStack.append(self.instructionPointer)
                if self.tape.read() == 0:
                    self.instructionPointer += self.getNextClosedBracket()
                    return 0
            case ']':
                matchingOpen = self.callStack.pop()
                if self.tape.read() != 0:
                    self.instructionPointer = matchingOpen
                    return 0
            case '(': self.stack.append(self.tape.read())
            case ')': self.tape.setValue(self.stack.pop())
            case '/': self.tape.setValue(self.stack[-1])
            case '~': self.TCPConnect()
            case '*': self.SSLConnect()
            case '^': self.descWrite()
            case 'v': self.descRead()
            case '`': self.descClose()
            case '&': self.fileOpen()
            case '%': self.selectDescriptor()
            case '=': self.createListenServer()
            case '?': self.testDescriptor()
            case '_': self.delay()

        self.instructionPointer += 1
        return 0


    def preprocess(self):
        isCode = True
        outCode = ""
        for i in self.code:
            if i == "{":
                isCode = False
            if i == "}":
                isCode = True
            if isCode:
                outCode += i
        self.code = outCode
        for i in bracketTypes:
            depth = 0
            for j in self.code:
                if j == i[0]: depth += 1
                elif j == i[1]: depth -= 1
            if depth != 0:
                raise SyntaxError(f"Mismatching '{i[0]}{i[1]}' brackets.")
    
    def run(self):
        self.preprocess()
        while self.step() == 0:
            pass

if __name__ == "__main__":
    if len(sys.argv) < 2:
        exit(f"Usage: {sys.argv[0]} <file>")
    interpreter = None
    with open(sys.argv[1],'r') as file:
        interpreter = Interpreter(file.read())
    interpreter.run()