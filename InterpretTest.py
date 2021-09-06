from NFSuper import Interpreter
# Create new interpreter object
x = Interpreter()
# Load code from file
file = open("echoServer.bf","r")
bfString = file.read()
file.close()
# interpret the code
x.bf_interpret(bfString)
