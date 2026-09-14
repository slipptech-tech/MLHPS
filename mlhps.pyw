import os
import sys
import time
import json
import socket
import threading
import subprocess
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

# ============================================================
# FORCE PYQTGRAPH -> PYSIDE6
# ============================================================

os.environ["PYQTGRAPH_QT_LIB"] = "PySide6"


# ============================================================
# PATHS / CONFIG
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

CONFIG_FILE = os.path.join(
    BASE_DIR,
    "mlhps_config.json"
)


DEFAULT_CONFIG = {
    "server_type": "HTTP Server",
    "host": "127.0.0.1",
    "port": 8000,
    "logging": True,
    "monitoring": True,
    "interval": 1
}


# ============================================================
# ASCII
# ============================================================

ASCII_ART = r"""

███╗   ███╗██╗     ██╗  ██╗██████╗ ███████╗
████╗ ████║██║     ██║  ██║██╔══██╗██╔════╝
██╔████╔██║██║     ███████║██████╔╝███████╗
██║╚██╔╝██║██║     ██╔══██║██╔═══╝ ╚════██║
██║ ╚═╝ ██║███████╗██║  ██║██║     ███████║
╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝╚═╝     ╚══════╝

              M L H P S

       Local Server Monitor
"""


# ============================================================
# TERMINAL
# ============================================================

def clear_terminal():

    os.system(
        "cls" if os.name == "nt"
        else "clear"
    )


def ask_yes_no(
    question,
    default=True
):

    while True:

        suffix = (
            "[Y/n]"
            if default
            else "[y/N]"
        )

        answer = input(
            f"{question} {suffix}: "
        ).strip().lower()

        if not answer:
            return default

        if answer in (
            "y",
            "yes"
        ):
            return True

        if answer in (
            "n",
            "no"
        ):
            return False

        print(
            "Please enter Y or N."
        )


def ask_int(
    question,
    default,
    minimum,
    maximum
):

    while True:

        answer = input(
            f"{question} "
            f"[{default}]: "
        ).strip()

        if not answer:
            return default

        try:

            value = int(answer)

            if (
                minimum
                <= value
                <= maximum
            ):
                return value

        except ValueError:
            pass

        print(
            f"Enter a value "
            f"between {minimum} "
            f"and {maximum}."
        )


# ============================================================
# TERMINAL SETUP
# ============================================================

def terminal_setup():

    clear_terminal()

    print(ASCII_ART)

    print(
        "=" * 66
    )

    print(
        "                    INITIAL SETUP"
    )

    print(
        "=" * 66
    )

    print()

    print(
        "Select server type:"
    )

    print()

    print(
        "  [1] HTTP Server"
    )

    print(
        "      Local web server + HTTP statistics"
    )

    print()

    print(
        "  [2] TCP Server"
    )

    print(
        "      Local TCP connection monitor"
    )

    print()

    print(
        "  [3] HTTP + System Monitor"
    )

    print(
        "      HTTP server + extended PC monitoring"
    )

    print()

    while True:

        choice = input(
            "Select [1-3]: "
        ).strip()

        if choice in (
            "1",
            "2",
            "3"
        ):
            break

        print(
            "Invalid option."
        )


    if choice == "1":

        server_type = (
            "HTTP Server"
        )

    elif choice == "2":

        server_type = (
            "TCP Server"
        )

    else:

        server_type = (
            "HTTP + System Monitor"
        )


    print()

    print(
        "-" * 66
    )

    print(
        "SERVER CONFIGURATION"
    )

    print(
        "-" * 66
    )

    print()

    print(
        "MLHPS uses localhost only."
    )

    print(
        "The server will not listen on your LAN/public IP."
    )

    print()

    port = ask_int(
        "Port",
        8000,
        1024,
        65535
    )

    print()

    logging_enabled = ask_yes_no(
        "Enable server logging?",
        True
    )

    monitoring_enabled = ask_yes_no(
        "Enable system monitoring?",
        True
    )

    print()

    interval = ask_int(
        "Monitoring interval (seconds)",
        1,
        1,
        10
    )


    config = {

        "server_type":
            server_type,

        "host":
            "127.0.0.1",

        "port":
            port,

        "logging":
            logging_enabled,

        "monitoring":
            monitoring_enabled,

        "interval":
            interval
    }


    with open(
        CONFIG_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            config,
            file,
            indent=4
        )


    print()

    print(
        "=" * 66
    )

    print(
        "CONFIGURATION COMPLETE"
    )

    print(
        "=" * 66
    )

    print()

    print(
        f"Server       : "
        f"{server_type}"
    )

    print(
        "Host         : "
        "127.0.0.1"
    )

    print(
        f"Port         : "
        f"{port}"
    )

    print(
        "Logging      : "
        + (
            "Enabled"
            if logging_enabled
            else "Disabled"
        )
    )

    print(
        "Monitoring   : "
        + (
            "Enabled"
            if monitoring_enabled
            else "Disabled"
        )
    )

    print(
        f"Interval     : "
        f"{interval}s"
    )

    print()

    input(
        "Press ENTER to launch MLHPS..."
    )


# ============================================================
# CONFIG LOADER
# ============================================================

def load_config():

    if not os.path.exists(
        CONFIG_FILE
    ):

        return DEFAULT_CONFIG.copy()

    try:

        with open(
            CONFIG_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(
                file
            )

        result = (
            DEFAULT_CONFIG.copy()
        )

        result.update(
            data
        )

        return result

    except Exception:

        return DEFAULT_CONFIG.copy()


# ============================================================
# SERVER STATE
# ============================================================

server = None
server_thread = None

tcp_socket = None
tcp_thread = None

server_started = None

stats_lock = threading.Lock()

stats = {

    "requests": 0,

    "connections": 0,

    "errors": 0,

    "bytes": 0
}


# ============================================================
# HTTP SERVER
# ============================================================

class MLHPSHandler(
    BaseHTTPRequestHandler
):

    def do_GET(self):

        with stats_lock:

            stats[
                "requests"
            ] += 1

            stats[
                "connections"
            ] += 1


        try:

            html = """
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<title>MLHPS</title>

<style>

body {
    margin: 0;
    background: #080a0f;
    color: #eeeeee;
    font-family: Arial;
    text-align: center;
}

.container {
    margin-top: 120px;
}

h1 {
    font-size: 52px;
}

.status {
    color: #58e6a5;
}

</style>

</head>

<body>

<div class="container">

<h1>MLHPS</h1>

<p>Local Server Monitor</p>

<p class="status">
● SERVER ONLINE
</p>

<p>
127.0.0.1
</p>

</div>

</body>

</html>
"""

            data = html.encode(
                "utf-8"
            )


            with stats_lock:

                stats[
                    "bytes"
                ] += len(data)


            self.send_response(
                200
            )

            self.send_header(
                "Content-Type",
                "text/html; charset=utf-8"
            )

            self.send_header(
                "Content-Length",
                str(len(data))
            )

            self.end_headers()

            self.wfile.write(
                data
            )


        except Exception:

            with stats_lock:

                stats[
                    "errors"
                ] += 1


        finally:

            with stats_lock:

                stats[
                    "connections"
                ] -= 1


    def log_message(
        self,
        format,
        *args
    ):

        config = load_config()

        if config.get(
            "logging",
            True
        ):

            print(
                "[HTTP]",
                format % args
            )


# ============================================================
# TCP SERVER
# ============================================================

def tcp_server_loop(
    host,
    port
):

    global tcp_socket

    try:

        tcp_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        tcp_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )

        tcp_socket.bind(
            (
                host,
                port
            )
        )

        tcp_socket.listen(
            20
        )

        tcp_socket.settimeout(
            1
        )


        while tcp_socket:

            try:

                client, address = (
                    tcp_socket.accept()
                )

                with stats_lock:

                    stats[
                        "connections"
                    ] += 1


                threading.Thread(
                    target=handle_tcp_client,
                    args=(
                        client,
                    ),
                    daemon=True
                ).start()


            except socket.timeout:

                continue

            except OSError:

                break


    except Exception:

        with stats_lock:

            stats[
                "errors"
            ] += 1


def handle_tcp_client(
    client
):

    try:

        client.settimeout(
            2
        )

        data = client.recv(
            4096
        )

        if data:

            with stats_lock:

                stats[
                    "bytes"
                ] += len(data)


    except Exception:

        with stats_lock:

            stats[
                "errors"
            ] += 1


    finally:

        try:

            client.close()

        except Exception:

            pass


        with stats_lock:

            stats[
                "connections"
            ] -= 1


# ============================================================
# START HTTP
# ============================================================

def start_http_server(
    host,
    port
):

    global server
    global server_thread
    global server_started

    server = ThreadingHTTPServer(
        (
            host,
            port
        ),
        MLHPSHandler
    )

    server_thread = threading.Thread(
        target=server.serve_forever,
        daemon=True
    )

    server_thread.start()

    server_started = time.time()


# ============================================================
# START TCP
# ============================================================

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


# ============================================================
# STOP SERVER
# ============================================================

def stop_server():

    global server
    global tcp_socket
    global server_thread
    global tcp_thread
    global server_started

    try:

        if server is not None:

            server.shutdown()

            server.server_close()

    except Exception:

        pass


    server = None
    server_thread = None


    try:

        if tcp_socket is not None:

            tcp_socket.close()

    except Exception:

        pass


    tcp_socket = None
    tcp_thread = None

    server_started = None


# ============================================================
# GUI
# ============================================================

def run_gui():

    import psutil
    import pyqtgraph as pg

    from PySide6.QtCore import (
        Qt,
        QTimer,
        QPropertyAnimation,
        QEasingCurve,
        QRect
    )

    from PySide6.QtWidgets import (
        QApplication,
        QMainWindow,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QFrame,
        QGraphicsOpacityEffect,
        QPlainTextEdit,
        QGridLayout
    )


    # ========================================================
    # METRIC CARD
    # ========================================================

    class MetricCard(QFrame):

        def __init__(
            self,
            title,
            value
        ):

            super().__init__()

            self.setObjectName(
                "metricCard"
            )

            layout = QVBoxLayout(
                self
            )

            layout.setContentsMargins(
                18,
                14,
                18,
                14
            )

            layout.setSpacing(
                3
            )


            self.title = QLabel(
                title
            )

            self.title.setObjectName(
                "metricTitle"
            )


            self.value = QLabel(
                value
            )

            self.value.setObjectName(
                "metricValue"
            )


            layout.addWidget(
                self.title
            )

            layout.addWidget(
                self.value
            )


            self.effect = (
                QGraphicsOpacityEffect(
                    self.value
                )
            )

            self.value.setGraphicsEffect(
                self.effect
            )

            self.effect.setOpacity(
                1
            )


        def animate_value(self):

            animation = (
                QPropertyAnimation(
                    self.effect,
                    b"opacity"
                )
            )

            animation.setDuration(
                180
            )

            animation.setStartValue(
                0.45
            )

            animation.setEndValue(
                1.0
            )

            animation.setEasingCurve(
                QEasingCurve.OutCubic
            )

            animation.start()

            self.animation = animation


    # ========================================================
    # MAIN WINDOW
    # ========================================================

    class MLHPS(QMainWindow):

        def __init__(self):

            super().__init__()

            self.config = load_config()

            self.setWindowTitle(
                "MLHPS — Local Server Monitor"
            )

            self.resize(
                1380,
                940
            )

            self.setMinimumSize(
                1100,
                760
            )


            # DATA

            self.time_data = []

            self.cpu_data = []

            self.ram_data = []

            self.disk_data = []

            self.request_data = []

            self.network_rx = []

            self.network_tx = []


            self.last_requests = 0

            self.last_net = (
                psutil.net_io_counters()
            )

            self.build_ui()

            self.setup_graphs()

            self.apply_style()

            self.setup_timer()

            self.fade_in()

            self.start_local_server()


        # ====================================================
        # UI
        # ====================================================

        def build_ui(self):

            central = QWidget()

            self.setCentralWidget(
                central
            )


            main = QVBoxLayout(
                central
            )

            main.setContentsMargins(
                26,
                22,
                26,
                22
            )

            main.setSpacing(
                14
            )


            # ------------------------------------------------
            # HEADER
            # ------------------------------------------------

            header = QHBoxLayout()


            title_layout = QVBoxLayout()


            title = QLabel(
                "MLHPS"
            )

            title.setObjectName(
                "appTitle"
            )


            subtitle = QLabel(
                "Local Server Performance Monitor"
            )

            subtitle.setObjectName(
                "appSubtitle"
            )


            title_layout.addWidget(
                title
            )

            title_layout.addWidget(
                subtitle
            )


            header.addLayout(
                title_layout
            )

            header.addStretch()


            self.status = QLabel(
                "● STARTING"
            )

            self.status.setObjectName(
                "statusStarting"
            )


            header.addWidget(
                self.status
            )


            main.addLayout(
                header
            )


            # ------------------------------------------------
            # METRICS
            # ------------------------------------------------

            grid = QGridLayout()

            grid.setSpacing(
                10
            )


            self.cpu_card = MetricCard(
                "CPU USAGE",
                "0%"
            )

            self.ram_card = MetricCard(
                "RAM USAGE",
                "0%"
            )

            self.disk_card = MetricCard(
                "DISK USAGE",
                "0%"
            )

            self.cpu_freq_card = MetricCard(
                "CPU FREQUENCY",
                "0 MHz"
            )

            self.requests_card = MetricCard(
                "TOTAL REQUESTS",
                "0"
            )

            self.rps_card = MetricCard(
                "REQUESTS / SEC",
                "0"
            )

            self.connections_card = MetricCard(
                "ACTIVE CONNECTIONS",
                "0"
            )

            self.errors_card = MetricCard(
                "ERRORS",
                "0"
            )


            cards = [

                self.cpu_card,
                self.ram_card,
                self.disk_card,
                self.cpu_freq_card,
                self.requests_card,
                self.rps_card,
                self.connections_card,
                self.errors_card
            ]


            positions = [

                (0, 0),
                (0, 1),
                (0, 2),
                (0, 3),

                (1, 0),
                (1, 1),
                (1, 2),
                (1, 3)
            ]


            for card, position in zip(
                cards,
                positions
            ):

                grid.addWidget(
                    card,
                    position[0],
                    position[1]
                )


            main.addLayout(
                grid
            )


            # ------------------------------------------------
            # SYSTEM INFO
            # ------------------------------------------------

            info = QFrame()

            info.setObjectName(
                "infoPanel"
            )


            info_layout = QHBoxLayout(
                info
            )


            self.server_label = QLabel(
                "Server: "
                + self.config[
                    "server_type"
                ]
            )


            self.address_label = QLabel(
                f"127.0.0.1:"
                f"{self.config['port']}"
            )


            self.process_label = QLabel(
                "Processes: 0"
            )


            self.thread_label = QLabel(
                "Threads: 0"
            )


            self.uptime_label = QLabel(
                "Uptime: 00:00:00"
            )


            info_layout.addWidget(
                self.server_label
            )

            info_layout.addStretch()

            info_layout.addWidget(
                self.address_label
            )

            info_layout.addStretch()

            info_layout.addWidget(
                self.process_label
            )

            info_layout.addStretch()

            info_layout.addWidget(
                self.thread_label
            )

            info_layout.addStretch()

            info_layout.addWidget(
                self.uptime_label
            )


            main.addWidget(
                info
            )


            # ------------------------------------------------
            # SYSTEM GRAPH
            # ------------------------------------------------

            system_panel = QFrame()

            system_panel.setObjectName(
                "graphPanel"
            )


            system_layout = QVBoxLayout(
                system_panel
            )


            title = QLabel(
                "SYSTEM PERFORMANCE"
            )

            title.setObjectName(
                "sectionTitle"
            )


            system_layout.addWidget(
                title
            )


            self.system_graph = (
                pg.PlotWidget()
            )


            system_layout.addWidget(
                self.system_graph
            )


            main.addWidget(
                system_panel,
                2
            )


            # ------------------------------------------------
            # NETWORK GRAPH
            # ------------------------------------------------

            network_panel = QFrame()

            network_panel.setObjectName(
                "graphPanel"
            )


            network_layout = QVBoxLayout(
                network_panel
            )


            network_title = QLabel(
                "NETWORK ACTIVITY"
            )

            network_title.setObjectName(
                "sectionTitle"
            )


            network_layout.addWidget(
                network_title
            )


            self.network_graph = (
                pg.PlotWidget()
            )


            network_layout.addWidget(
                self.network_graph
            )


            main.addWidget(
                network_panel,
                1
            )


            # ------------------------------------------------
            # BOTTOM
            # ------------------------------------------------

            bottom = QHBoxLayout()


            self.log = QPlainTextEdit()

            self.log.setReadOnly(
                True
            )

            self.log.setMaximumHeight(
                125
            )


            bottom.addWidget(
                self.log,
                3
            )


            buttons = QVBoxLayout()


            self.start_button = (
                QPushButton(
                    "▶  START SERVER"
                )
            )


            self.stop_button = (
                QPushButton(
                    "■  STOP SERVER"
                )
            )


            self.restart_button = (
                QPushButton(
                    "↻  RESTART SERVER"
                )
            )


            self.clear_button = (
                QPushButton(
                    "⌫  CLEAR GRAPHS"
                )
            )


            self.exit_button = (
                QPushButton(
                    "✕  SHUTDOWN MLHPS"
                )
            )


            buttons.addWidget(
                self.start_button
            )

            buttons.addWidget(
                self.stop_button
            )

            buttons.addWidget(
                self.restart_button
            )

            buttons.addWidget(
                self.clear_button
            )

            buttons.addWidget(
                self.exit_button
            )


            bottom.addLayout(
                buttons
            )


            main.addLayout(
                bottom
            )


            # SIGNALS

            self.start_button.clicked.connect(
                self.start_local_server
            )

            self.stop_button.clicked.connect(
                self.stop_local_server
            )

            self.restart_button.clicked.connect(
                self.restart_server
            )

            self.clear_button.clicked.connect(
                self.clear_graphs
            )

            self.exit_button.clicked.connect(
                self.shutdown_application
            )


        # ====================================================
        # GRAPHS
        # ====================================================

        def setup_graphs(self):

            pg.setConfigOptions(
                antialias=True
            )


            graphs = [

                self.system_graph,

                self.network_graph
            ]


            for graph in graphs:

                graph.setBackground(
                    "#0d1016"
                )

                graph.showGrid(
                    x=True,
                    y=True,
                    alpha=0.10
                )


            self.system_graph.setYRange(
                0,
                100
            )


            self.cpu_curve = (
                self.system_graph.plot(
                    pen=pg.mkPen(
                        "#6c8cff",
                        width=3
                    )
                )
            )


            self.ram_curve = (
                self.system_graph.plot(
                    pen=pg.mkPen(
                        "#b56cff",
                        width=3
                    )
                )
            )


            self.disk_curve = (
                self.system_graph.plot(
                    pen=pg.mkPen(
                        "#55d6be",
                        width=3
                    )
                )


            self.rx_curve = (
                self.network_graph.plot(
                    pen=pg.mkPen(
                        "#6c8cff",
                        width=3
                    )
                )
            )


            self.tx_curve = (
                self.network_graph.plot(
                    pen=pg.mkPen(
                        "#ff9d5c",
                        width=3
                    )
                )
            )


        # ====================================================
        # TIMER
        # ====================================================

        def setup_timer(self):

            interval = max(
                1,
                int(
                    self.config.get(
                        "interval",
                        1
                    )
                )
            )


            self.timer = QTimer(
                self
            )


            self.timer.timeout.connect(
                self.update_monitor
            )


            self.timer.start(
                interval * 1000
            )


        # ====================================================
        # START
        # ====================================================

        def start_local_server(
            self
        ):

            global server

            if (
                server is not None
                or tcp_socket is not None
            ):

                self.write_log(
                    "[MLHPS] Server already running"
                )

                return


            try:

                host = "127.0.0.1"

                port = int(
                    self.config[
                        "port"
                    ]
                )


                server_type = (
                    self.config[
                        "server_type"
                    ]
                )


                if server_type == (
                    "TCP Server"
                ):

                    start_tcp_server(
                        host,
                        port
                    )

                else:

                    start_http_server(
                        host,
                        port
                    )


                self.set_online()


                self.write_log(
                    "[SERVER] Server started"
                )


                self.write_log(
                    f"[SERVER] "
                    f"{server_type}"
                )


                self.write_log(
                    f"[SERVER] "
                    f"127.0.0.1:{port}"
                )


            except Exception as e:

                self.set_error()

                self.write_log(
                    f"[ERROR] {e}"
                )


        # ====================================================
        # STOP
        # ====================================================

        def stop_local_server(
            self
        ):

            if (
                server is None
                and tcp_socket is None
            ):

                self.write_log(
                    "[SERVER] "
                    "Server is already stopped"
                )

                return


            stop_server()


            self.set_offline()


            self.write_log(
                "[SERVER] "
                "Server stopped"
            )


        # ====================================================
        # RESTART
        # ====================================================

        def restart_server(
            self
        ):

            self.write_log(
                "[SERVER] "
                "Restarting..."
            )


            stop_server()


            QTimer.singleShot(
                300,
                self.start_local_server
            )


        # ====================================================
        # STATUS
        # ====================================================

        def set_online(
            self
        ):

            self.status.setText(
                "● ONLINE"
            )

            self.status.setObjectName(
                "statusOnline"
            )

            self.refresh_style(
                self.status
            )


        def set_offline(
            self
        ):

            self.status.setText(
                "● OFFLINE"
            )

            self.status.setObjectName(
                "statusOffline"
            )

            self.refresh_style(
                self.status
            )


        def set_error(
            self
        ):

            self.status.setText(
                "● ERROR"
            )

            self.status.setObjectName(
                "statusError"
            )

            self.refresh_style(
                self.status
            )


        # ====================================================
        # MONITOR
        # ====================================================

        def update_monitor(
            self
        ):

            try:

                cpu = (
                    psutil.cpu_percent(
                        interval=None
                    )
                )


                ram = (
                    psutil.virtual_memory()
                )


                disk = (
                    psutil.disk_usage(
                        os.path.abspath(
                            os.sep
                        )
                    )
                )


                cpu_freq = (
                    psutil.cpu_freq()
                )


                with stats_lock:

                    requests = (
                        stats[
                            "requests"
                        ]
                    )

                    connections = (
                        stats[
                            "connections"
                        ]
                    )

                    errors = (
                        stats[
                            "errors"
                        ]
                    )


                # --------------------------------------------
                # REQUEST RATE
                # --------------------------------------------

                rps = (
                    requests
                    - self.last_requests
                )


                self.last_requests = (
                    requests
                )


                # --------------------------------------------
                # NETWORK
                # --------------------------------------------

                current_net = (
                    psutil.net_io_counters()
                )


                rx = max(
                    0,
                    current_net.bytes_recv
                    - self.last_net.bytes_recv
                )


                tx = max(
                    0,
                    current_net.bytes_sent
                    - self.last_net.bytes_sent
                )


                self.last_net = (
                    current_net
                )


                # --------------------------------------------
                # CPU FREQUENCY
                # --------------------------------------------

                frequency = 0

                if cpu_freq:

                    frequency = (
                        cpu_freq.current
                    )


                # --------------------------------------------
                # CARDS
                # --------------------------------------------

                self.set_card(
                    self.cpu_card,
                    f"{cpu:.1f}%"
                )


                self.set_card(
                    self.ram_card,
                    f"{ram.percent:.1f}%"
                )


                self.set_card(
                    self.disk_card,
                    f"{disk.percent:.1f}%"
                )


                self.set_card(
                    self.cpu_freq_card,
                    f"{frequency:.0f} MHz"
                )


                self.set_card(
                    self.requests_card,
                    str(requests)
                )


                self.set_card(
                    self.rps_card,
                    str(rps)
                )


                self.set_card(
                    self.connections_card,
                    str(connections)
                )


                self.set_card(
                    self.errors_card,
                    str(errors)
                )


                # --------------------------------------------
                # SYSTEM INFO
                # --------------------------------------------

                self.process_label.setText(
                    f"Processes: "
                    f"{len(
                        list(
                            psutil.process_iter()
                        )
                    )}"
                )


                self.thread_label.setText(
                    f"Threads: "
                    f"{threading.active_count()}"
                )


                if server_started:

                    seconds = int(
                        time.time()
                        - server_started
                    )

                    hours = (
                        seconds
                        // 3600
                    )

                    minutes = (
                        seconds
                        % 3600
                    ) // 60

                    secs = (
                        seconds
                        % 60
                    )

                    self.uptime_label.setText(
                        f"Uptime: "
                        f"{hours:02}:"
                        f"{minutes:02}:"
                        f"{secs:02}"
                    )


                else:

                    self.uptime_label.setText(
                        "Uptime: 00:00:00"
                    )


                # --------------------------------------------
                # GRAPH DATA
                # --------------------------------------------

                index = len(
                    self.time_data
                )


                self.time_data.append(
                    index
                )


                self.cpu_data.append(
                    cpu
                )


                self.ram_data.append(
                    ram.percent
                )


                self.disk_data.append(
                    disk.percent
                )


                self.network_rx.append(
                    rx / 1024
                )


                self.network_tx.append(
                    tx / 1024
                )


                max_points = 60


                self.time_data = (
                    self.time_data[
                        -max_points:
                    ]
                )


                self.cpu_data = (
                    self.cpu_data[
                        -max_points:
                    ]
                )


                self.ram_data = (
                    self.ram_data[
                        -max_points:
                    ]
                )


                self.disk_data = (
                    self.disk_data[
                        -max_points:
                    ]
                )


                self.network_rx = (
                    self.network_rx[
                        -max_points:
                    ]
                )


                self.network_tx = (
                    self.network_tx[
                        -max_points:
                    ]
                )


                # --------------------------------------------
                # DRAW
                # --------------------------------------------

                self.cpu_curve.setData(
                    self.time_data,
                    self.cpu_data
                )


                self.ram_curve.setData(
                    self.time_data,
                    self.ram_data
                )


                self.disk_curve.setData(
                    self.time_data,
                    self.disk_data
                )


                self.rx_curve.setData(
                    self.time_data,
                    self.network_rx
                )


                self.tx_curve.setData(
                    self.time_data,
                    self.network_tx
                )


            except Exception as e:

                self.write_log(
                    f"[MONITOR] {e}"
                )


        # ====================================================
        # CARD ANIMATION
        # ====================================================

        def set_card(
            self,
            card,
            value
        ):

            if card.value.text() != value:

                card.value.setText(
                    value
                )

                card.animate_value()


        # ====================================================
        # LOG
        # ====================================================

        def write_log(
            self,
            text
        ):

            timestamp = time.strftime(
                "%H:%M:%S"
            )

            self.log.appendPlainText(
                f"[{timestamp}] {text}"
            )


        # ====================================================
        # CLEAR
        # ====================================================

        def clear_graphs(
            self
        ):

            self.time_data.clear()

            self.cpu_data.clear()

            self.ram_data.clear()

            self.disk_data.clear()

            self.network_rx.clear()

            self.network_tx.clear()


            self.cpu_curve.clear()

            self.ram_curve.clear()

            self.disk_curve.clear()

            self.rx_curve.clear()

            self.tx_curve.clear()


            self.write_log(
                "[MLHPS] "
                "Graph history cleared"
            )


        # ====================================================
        # SHUTDOWN
        # ====================================================

        def shutdown_application(
            self
        ):

            self.write_log(
                "[MLHPS] "
                "Stopping server..."
            )


            stop_server()


            self.timer.stop()


            self.write_log(
                "[MLHPS] "
                "Application closed"
            )


            QTimer.singleShot(
                150,
                QApplication.instance().quit
            )


        # ====================================================
        # STYLE
        # ====================================================

        def apply_style(
            self
        ):

            self.setStyleSheet("""

            QMainWindow {
                background: #080a0f;
            }

            QWidget {
                color: #eeeeee;
                font-family: "Segoe UI";
            }


            #appTitle {
                color: #ffffff;
                font-size: 35px;
                font-weight: 800;
            }

            #appSubtitle {
                color: #727a8a;
                font-size: 13px;
            }


            #metricCard {
                background: #10131a;
                border: 1px solid #1d222d;
                border-radius: 14px;
            }

            #metricCard:hover {
                background: #131720;
                border: 1px solid #2b3240;
            }


            #metricTitle {
                color: #727a89;
                font-size: 10px;
                font-weight: 700;
            }


            #metricValue {
                color: #f4f5f7;
                font-size: 23px;
                font-weight: 750;
            }


            #infoPanel {
                background: #10131a;
                border: 1px solid #1d222d;
                border-radius: 12px;
            }


            #graphPanel {
                background: #10131a;
                border: 1px solid #1d222d;
                border-radius: 14px;
            }


            #sectionTitle {
                color: #aeb5c4;
                font-size: 11px;
                font-weight: 700;
                padding: 6px;
            }


            #statusStarting {
                color: #f0c75e;
                background: #211c10;
                border-radius: 10px;
                padding: 8px 16px;
                font-weight: 700;
            }


            #statusOnline {
                color: #58e6a5;
                background: #102019;
                border-radius: 10px;
                padding: 8px 16px;
                font-weight: 700;
            }


            #statusOffline {
                color: #8c93a2;
                background: #151820;
                border-radius: 10px;
                padding: 8px 16px;
                font-weight: 700;
            }


            #statusError {
                color: #ff647c;
                background: #211116;
                border-radius: 10px;
                padding: 8px 16px;
                font-weight: 700;
            }


            QPushButton {
                background: #171b25;
                border: 1px solid #272d3a;
                border-radius: 10px;
                padding: 10px 16px;
                color: #eeeeee;
                font-weight: 600;
            }


            QPushButton:hover {
                background: #222936;
                border: 1px solid #3a4354;
            }


            QPushButton:pressed {
                background: #101319;
            }


            QPlainTextEdit {
                background: #0d1016;
                border: 1px solid #1d222d;
                border-radius: 12px;
                color: #7e8797;
                padding: 8px;
                font-family: Consolas;
                font-size: 11px;
            }

            """)


        # ====================================================
        # STYLE REFRESH
        # ====================================================

        def refresh_style(
            self,
            widget
        ):

            widget.style().unpolish(
                widget
            )

            widget.style().polish(
                widget
            )

            widget.update()


        # ====================================================
        # FADE IN
        # ====================================================

        def fade_in(
            self
        ):

            effect = (
                QGraphicsOpacityEffect(
                    self
                )
            )


            self.setGraphicsEffect(
                effect
            )


            animation = (
                QPropertyAnimation(
                    effect,
                    b"opacity"
                )
            )


            animation.setDuration(
                850
            )


            animation.setStartValue(
                0.0
            )


            animation.setEndValue(
                1.0
            )


            animation.setEasingCurve(
                QEasingCurve.OutCubic
            )


            animation.start()


            self.fade_animation = (
                animation
            )


        # ====================================================
        # CLOSE
        # ====================================================

        def closeEvent(
            self,
            event
        ):

            self.timer.stop()

            stop_server()

            event.accept()


    # ========================================================
    # APPLICATION
    # ========================================================

    app = QApplication(
        sys.argv
    )

    app.setStyle(
        "Fusion"
    )


    window = MLHPS()

    window.show()


    sys.exit(
        app.exec()
    )


# ============================================================
# TERMINAL LAUNCHER
# ============================================================

def launch_setup():

    python_exe = (
        sys.executable
    )


    if python_exe.lower().endswith(
        "pythonw.exe"
    ):

        python_exe = (
            python_exe[
                :-10
            ]
            + "python.exe"
        )


    subprocess.run(
        [
            python_exe,
            os.path.abspath(
                __file__
            ),
            "--setup"
        ],
        creationflags=(
            subprocess.CREATE_NEW_CONSOLE
            if os.name == "nt"
            else 0
        )
    )


# ============================================================
# MAIN
# ============================================================

def main():

    if "--setup" in sys.argv:

        terminal_setup()

        return


    if not os.path.exists(
        CONFIG_FILE
    ):

        launch_setup()


    run_gui()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()
