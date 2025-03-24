# IPC Debugger

A simple debugging tool for Inter-Process Communication (IPC) mechanisms including pipes, message queues, and shared memory.

## Features

- Visualize data transfer through pipes
- Monitor message queues
- Track shared memory access
- Identify potential deadlocks and bottlenecks
- Simple GUI interface to simulate and monitor IPC operations

## Project Structure

- `main.py`: Entry point for the application
- `ipc_debugger/`: Core module
  - `__init__.py`: Package initialization
  - `gui.py`: GUI implementation with Tkinter
  - `pipe_debug.py`: Pipe debugging functionality
  - `queue_debug.py`: Message queue debugging
  - `shared_mem_debug.py`: Shared memory debugging
  - `deadlock_detector.py`: Simple deadlock detection

## Requirements

- Python 3.6+
- Tkinter (included in standard Python)

## Usage

```
python main.py
```

## Implementation Details

The application uses a simplified approach to demonstrate IPC mechanisms:
- Named pipes for pipe communication
- Python's multiprocessing.Queue for message queues
- Multiprocessing shared memory for shared memory visualization
- Thread locks and semaphores for deadlock simulation and detection 