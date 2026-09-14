# MLHPS — My Local Host Private Server

**MLHPS** is a modern local server management and system monitoring application designed for developers, testers, and advanced users who need a convenient way to launch, control, and monitor local server environments.

The application combines **server management, real-time system monitoring, network statistics, performance graphs, and an interactive graphical interface** in a single lightweight tool.

### Key Features

* **Local Server Management** — start, stop, restart, and shut down local servers.
* **Multiple Server Modes** — HTTP Server, TCP Server, and combined HTTP + System Monitor mode.
* **Real-Time Monitoring** — CPU, RAM, disk usage, CPU frequency, processes, threads, uptime, and network activity.
* **Network Statistics** — incoming/outgoing traffic, requests per second, active connections, total requests, and errors.
* **Live Performance Graphs** — continuously updated CPU, memory, disk, and network charts.
* **Modern GUI** — dark interface with smooth animations, dynamic status indicators, metric cards, and visual feedback.
* **Configurable Environment** — customizable port, logging, monitoring interval, and other startup parameters.
* **Server Control** — instantly stop or restart the running server directly from the application.
* **Local-Only Operation** — server services are designed to bind to `127.0.0.1`, keeping the environment intended for local development and testing.
* **Lightweight Architecture** — built with Python, PySide6, PyQtGraph, and PSUtil.

Using strong TCP Technology:

def start_tcp_server(
    host,
    port
):

    global tcp_thread
    global server_started

    tcp_thread = threading.Thread(
        target=tcp_server_loop,
        args=(
            host,
            port
        ),
        daemon=True
    )

    tcp_thread.start()

    server_started = time.time()




### Purpose

MLHPS is intended for **local development, server testing, performance monitoring, debugging, and educational purposes**. It provides developers with a clear overview of how their local server and computer resources behave while applications are running.

### Technology

**Python · PySide6 · PyQtGraph · PSUtil · HTTP · TCP**

MLHPS focuses on combining functionality with a clean interface, providing an easy-to-use control center for local server environments.

