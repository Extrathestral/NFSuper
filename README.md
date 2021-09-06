### Instructions
```
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
~: connect to the host specified in the stack (more info later)
`: disconnect from the current connection
=: listen for a connection on the port in the stack (more info later) (blocking)
{: skip to the next } if there is no current connection
}: skip to the last { if there is a current connection
^: send the value from the current cell over the connection
v: receive one byte from connection and put it into the current cell
```

### Networking info

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

### TODO:

```
v1.0:

    -Full Rewrite: half this interpreter (the standard BF instruction set) was written by me years ago, and the other half (the custom features) was written painfully dealing with my horrid code, gonna purge and rewrite

    -File IO: self-explanatory

    -Descriptor Table: Will work similarly to the tape, but will hold sessions for Sockets and FileIO

    -New Socket types: UDP, SSL (TCP wrapped in SSL, for use with HTTPS and the likes)```