# NFSuper
NFSuper is a derivative of the BrainFuck esolang, with a Stack, Networking, and File IO.

### Instructions

Usage: `python NFSuper.py <file>`

```
{}: Everything enclosed in these will be treated as a comment.
+: inc current element
-: dec current element
>: move instruction pointer one to the right
<: move instruction pointer one to the left
[: start loop
]: end loop
.: print element in ascii to console
,: get one byte of input in ascii and put it into the selected cell
(: push to the stack
): pop from the stack
/: peek from the stack
~: connect over TCP to the IP and Port specified in the stack (more info later)
*: connect over SSL to the Hostname and port specified in the stack (more info later)
&: open a file from a filename on the stack (more info later)
%: select a descriptor (more info later) from the current cell value.
`: disconnect from the current connection
=: listen for a connection on the port in the stack (more info later) (blocking)
?: Return a 1 or 0 if current descriptor is still active (if socket is still connected, or if you've reached end of file)
^: send the value from the current cell over the connection
v: receive one byte from connection and put it into the current cell
_: Delay for an amount of time in ms taken from current cell value. 
```

### Descriptors

To allow for the user to have multiple files and socket connections active at once, there is a system for what are called 'descriptors' which can either be sockets or files. Descriptors are stored in a single list, referred to as the 'descriptor table', and are indexed by the order in which they are created, starting at 0.

### Networking info

All sockets, upon connection, are stored as descriptors in the descriptor table.

#### TCP:

To allow for the user to specify the IP and port to connect to *inside* the program as it's running, the IP is specified by putting the values inside the stack, the port being split between the Most Significant Byte and the Least Significant Byte.

Example for connecting to 127.0.0.1:8080
```
127
0
0
1
31 - Most significant byte of port number
144 - Least significant byte of port number
```

#### SSL:

SSL must use a hostname instead of an IP address in order to verify the certificate, so you must specify port, then hostname terminated by a null byte on the stack.

Example for connecting to www.google.com:443
```
1 - Most significant byte of port number
187 - Least significant byte of port number
119 - 'w'
119 - 'w'
119 - 'w'
46 - '.'
103 - 'g'
111 - 'o'
111 - 'o'
103 - 'g'
108 - 'l'
101 - 'e'
46 - '.'
99 - 'c'
111 - 'o'
109 - 'm'
0 - NUL, specifies end of string.
```

### File IO

Files can be opened as a new descriptor, and are able to be read and written to using v and ^ similar to sockets.

To open a file, you need to put the filename on the stack, terminated by a null byte.

The format for opening a file is as follows:

Example stack values for opening a file called 'example.txt'
```
101 - 'e'
120 - 'x'
97 - 'a'
109 - 'm'
112 - 'p'
108 - 'l'
101 - 'e'
46 - '.'
116 - 't'
120 - 'x'
116 - 't'
0 - NUL, specifies end of string.
```

### Examples
echoServer.bf - Starts listening on port 8083, then, when connected, will send anything you send back to you.

ssltest.bf - Sends a HEAD request to www.google.com:443, then prints out the result.