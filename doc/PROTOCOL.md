# Gomoku AI Protocol

Communication protocol between a brain (AI) and a gomoku manager.

## Overview

- The manager creates two pipes for bidirectional communication
- The brain is a console application reading from stdin and writing to stdout
- Each line ends with CR LF (0x0d, 0x0a)
- Empty lines are ignored
- The brain must flush output after each response

## Mandatory Commands

### START [size]

Initialize the brain with board size.

**Input:**
```
START 20
```

**Response:**
- `OK` - initialization successful
- `ERROR message` - unsupported size or error

**Notes:**
- Board size 20 is required for Gomocup tournaments
- Other sizes are recommended but optional

### TURN [X],[Y]

Opponent's move. Coordinates are 0-indexed.

**Input:**
```
TURN 10,10
```

**Response:**
```
11,10
```

### BEGIN

Brain plays first move on empty board.

**Input:**
```
BEGIN
```

**Response:**
```
10,10
```

### BOARD

Set entire board state.

**Input:**
```
BOARD
10,10,1
10,11,2
11,11,1
DONE
```

Where each line is `X,Y,field`:
- `1` = own stone
- `2` = opponent stone
- `3` = special (winning line or forbidden in renju)

**Response:**
```
9,9
```

**Notes:**
- In renju, moves must be in order they were played
- In gomoku, order doesn't matter
- Response is like TURN command

### INFO [key] [value]

Configuration information. Brain can ignore or respond to specific keys.

**Input:**
```
INFO timeout_turn 10000
INFO timeout_match 300000
INFO max_memory 83886080
INFO time_left 295000
```

**Keys:**
- `timeout_turn` - milliseconds per move (0=no limit)
- `timeout_match` - milliseconds for whole match (0=no limit)
- `max_memory` - bytes (0=no limit)
- `time_left` - remaining milliseconds
- `game_type` - 0=human, 1=brain, 2=tournament, 3=network
- `rule` - bitmask: 1=exactly five, 2=continuous, 4=renju, 8=caro
- `folder` - persistent storage folder path
- `evaluate` - X,Y coordinates for evaluation (debug only)

**Response:**
- None (INFO commands require no response)

**Notes:**
- time_left is sent before every move if time is limited
- Brain must cope with missing INFO values

### END

Terminate the brain immediately.

**Input:**
```
END
```

**Response:**
- None
- Brain should delete temporary files
- Must not crash if time to exit is too long

### ABOUT

Get brain information.

**Input:**
```
ABOUT
```

**Response:**
```
name="SomeBrain", version="1.0", author="Author", country="USA"
```

**Fields:**
- `name` - brain name (required format: pbrain-*)
- `version` - version string
- `author` - author name
- `country` - country code
- `www` - website URL
- `email` - contact email

## Brain Response Commands

### OK

Successful operation (response to START).

**Example:**
```
OK
```

### ERROR [message]

Operation failed with reason.

**Example:**
```
ERROR Board size not supported
```

### UNKNOWN [message]

Command not implemented or unknown.

**Example:**
```
UNKNOWN Command not supported
```

## Communication Flow Examples

### Simple game

```
Manager: START 20
Brain:   OK
Manager: BEGIN
Brain:   10,10
Manager: TURN 11,10
Brain:   10,11
Manager: TURN 11,11
Brain:   9,10
Manager: TURN 12,10
Brain:   8,10
Manager: END
Brain:   (terminates)
```

### With configuration

```
Manager: START 20
Brain:   OK
Manager: INFO timeout_turn 10000
Manager: INFO timeout_match 300000
Manager: INFO max_memory 83886080
Manager: INFO time_left 295000
Manager: INFO game_type 2
Manager: BEGIN
Brain:   10,10
Manager: TURN 11,10
Brain:   10,11
...
```

### Board state

```
Manager: START 20
Brain:   OK
Manager: BOARD
         10,10,1
         10,11,2
         11,11,1
         DONE
Brain:   9,9
Manager: TURN 9,10
Brain:   12,12
Manager: END
Brain:   (terminates)
```

## Rules & Constraints

- Brain name must start with `pbrain-` and contain only A-Z, a-z, 0-9, dash, underscore, dot
- Brain can create a folder with same name to store temporary files (max 20MB)
- Brain cannot write to stdout after END command
- Brain should not read input while thinking (use threads to avoid deadlock)
- If only one thread, don't read during computation
- Manager will terminate brain after timeout if it's stuck
- Empty lines in input are ignored
- Very long lines may be silently truncated

## Brain Implementation Checklist

- [x] Handle START command
- [x] Handle TURN command
- [x] Handle BEGIN command
- [x] Handle BOARD command with multi-line input
- [x] Handle END command
- [x] Handle ABOUT command
- [x] Flush stdout after each response
- [x] Support board size 20
- [x] Use CR LF or LF line endings
- [x] Return ERROR for unsupported operations
- [x] Return UNKNOWN for unimplemented commands
- [x] Clean up on END

## Implementation Notes

This implementation supports only mandatory Gomoku AI Protocol commands:
- **START** - Initialize with board size
- **TURN** - Opponent's move
- **BEGIN** - Brain's first move
- **BOARD** - Set entire board state
- **END** - Terminate brain
- **ABOUT** - Get brain information

Optional features like INFO, RECTSTART, RESTART, TAKEBACK, SWAP2BOARD are not supported in this minimal implementation.
