
import sys
import os
import time
import subprocess
from typing import List, Tuple, Optional
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSlider, QFrame, QSplitter, QTextEdit,
    QGroupBox, QProgressBar, QStatusBar, QFormLayout,
    QSpinBox, QLineEdit
)
from PySide6.QtCore import (
    Qt, QTimer, QThread, Signal, QRectF, QPointF
)
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QPixmap, QIcon
)

from gomoku_parser import ReplayParser
from gomoku_board import Board


class BoardWidget(QWidget):

    def __init__(self, board_size: int = 20, cell_size: int = 30):
        super().__init__()
        self.board_size = board_size
        self.cell_size = cell_size
        self.board = Board(board_size)
        self.moves = []
        self.current_move = 0

        min_width = (board_size + 1) * cell_size
        min_height = (board_size + 1) * cell_size
        self.setMinimumSize(min_width, min_height)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.fillRect(self.rect(), QColor(205, 133, 63))

        pen = QPen(QColor(139, 69, 19), 2)
        painter.setPen(pen)

        offset = self.cell_size
        for i in range(self.board_size):
            x = offset + i * self.cell_size
            painter.drawLine(x, offset, x, offset + (self.board_size - 1) * self.cell_size)

            y = offset + i * self.cell_size
            painter.drawLine(offset, y, offset + (self.board_size - 1) * self.cell_size, y)

        for y in range(self.board_size):
            for x in range(self.board_size):
                stone = self.board.get_stone(x, y)
                if stone != 0:
                    center_x = offset + x * self.cell_size
                    center_y = offset + y * self.cell_size
                    radius = self.cell_size // 2 - 3

                    if stone == 1:
                        painter.setBrush(QBrush(QColor(30, 30, 30)))
                    else:
                        painter.setBrush(QBrush(QColor(240, 240, 240)))

                    painter.setPen(QPen(Qt.PenStyle.NoPen))
                    painter.drawEllipse(QPointF(center_x, center_y), radius, radius)

    def update_board(self, moves: List[Tuple[int, int, int]], current_move: int):
        self.moves = moves
        self.current_move = current_move

        self.board.clear()
        for i in range(min(current_move, len(moves))):
            x, y, player = moves[i]
            self.board.set_stone(x, y, player)

        self.update()


class ControlPanel(QWidget):

    play_pause_clicked = Signal()
    next_move_clicked = Signal()
    prev_move_clicked = Signal()
    restart_clicked = Signal()
    speed_changed = Signal(float)
    hot_reload_toggled = Signal(bool)
    real_time_toggled = Signal(bool)
    launch_liskvork_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout(status_group)

        self.move_label = QLabel("Move: 0/0")
        self.move_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        status_layout.addWidget(self.move_label)

        self.last_move_label = QLabel("Last Move: None")
        status_layout.addWidget(self.last_move_label)

        self.hot_reload_label = QLabel("Hot Reload: ON")
        self.hot_reload_label.setStyleSheet("color: green; font-weight: bold;")
        status_layout.addWidget(self.hot_reload_label)

        self.real_time_label = QLabel("Real-Time: OFF")
        self.real_time_label.setStyleSheet("color: gray;")
        status_layout.addWidget(self.real_time_label)

        self.playback_label = QLabel("Playback: Paused")
        self.playback_label.setStyleSheet("color: red;")
        status_layout.addWidget(self.playback_label)

        layout.addWidget(status_group)

        speed_group = QGroupBox("Playback Speed")
        speed_layout = QVBoxLayout(speed_group)

        self.speed_label = QLabel("Speed: 1.0x")
        speed_layout.addWidget(self.speed_label)

        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(1, 100)
        self.speed_slider.setValue(10)
        self.speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.speed_slider.setTickInterval(10)
        self.speed_slider.valueChanged.connect(self.on_speed_changed)
        speed_layout.addWidget(self.speed_slider)

        preset_layout = QHBoxLayout()
        self.speed_05x_btn = QPushButton("0.5x")
        self.speed_1x_btn = QPushButton("1x")
        self.speed_2x_btn = QPushButton("2x")
        self.speed_5x_btn = QPushButton("5x")
        self.speed_10x_btn = QPushButton("10x")

        for btn in [self.speed_05x_btn, self.speed_1x_btn, self.speed_2x_btn, self.speed_5x_btn, self.speed_10x_btn]:
            btn.clicked.connect(self.on_preset_speed_clicked)
            preset_layout.addWidget(btn)

        speed_layout.addLayout(preset_layout)
        layout.addWidget(speed_group)

        control_group = QGroupBox("Controls")
        control_layout = QVBoxLayout(control_group)

        self.play_pause_btn = QPushButton("▶ Play")
        self.play_pause_btn.clicked.connect(self.play_pause_clicked.emit)
        control_layout.addWidget(self.play_pause_btn)

        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("⏮ Prev")
        self.prev_btn.clicked.connect(self.prev_move_clicked.emit)
        nav_layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("Next ⏭")
        self.next_btn.clicked.connect(self.next_move_clicked.emit)
        nav_layout.addWidget(self.next_btn)
        control_layout.addLayout(nav_layout)

        self.restart_btn = QPushButton("🔄 Restart")
        self.restart_btn.clicked.connect(self.restart_clicked.emit)
        control_layout.addWidget(self.restart_btn)

        # Toggle buttons
        toggle_layout = QVBoxLayout()
        self.hot_reload_btn = QPushButton("Hot Reload: ON")
        self.hot_reload_btn.setCheckable(True)
        self.hot_reload_btn.setChecked(True)
        self.hot_reload_btn.clicked.connect(self.on_hot_reload_toggled)
        toggle_layout.addWidget(self.hot_reload_btn)

        self.real_time_btn = QPushButton("Real-Time: OFF")
        self.real_time_btn.setCheckable(True)
        self.real_time_btn.clicked.connect(self.on_real_time_toggled)
        toggle_layout.addWidget(self.real_time_btn)

        control_layout.addLayout(toggle_layout)
        layout.addWidget(control_group)

        liskvork_group = QGroupBox("Launch Game")
        liskvork_layout = QVBoxLayout(liskvork_group)

        self.launch_liskvork_btn = QPushButton("Launch Liskvork")
        self.launch_liskvork_btn.clicked.connect(self.launch_liskvork_clicked.emit)
        liskvork_layout.addWidget(self.launch_liskvork_btn)

        layout.addWidget(liskvork_group)

        self.winner_frame = QFrame()
        self.winner_frame.setFrameStyle(QFrame.Shape.Box)
        self.winner_frame.setStyleSheet("background-color: #FFFFE0; border: 2px solid #008000;")
        self.winner_frame.setVisible(False)

        winner_layout = QVBoxLayout(self.winner_frame)
        self.winner_label = QLabel("🏆 Winner: Player X!")
        self.winner_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.winner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        winner_layout.addWidget(self.winner_label)

        layout.addWidget(self.winner_frame)

        layout.addStretch()

    def on_speed_changed(self, value):
        speed = value / 10.0
        self.speed_label.setText(f"Speed: {speed:.1f}x")
        self.speed_changed.emit(speed)

    def on_preset_speed_clicked(self):
        sender = self.sender()
        if sender == self.speed_05x_btn:
            speed = 0.5
        elif sender == self.speed_1x_btn:
            speed = 1.0
        elif sender == self.speed_2x_btn:
            speed = 2.0
        elif sender == self.speed_5x_btn:
            speed = 5.0
        elif sender == self.speed_10x_btn:
            speed = 10.0

        self.speed_slider.setValue(int(speed * 10))
        self.speed_changed.emit(speed)

    def on_hot_reload_toggled(self, checked):
        self.hot_reload_label.setText(f"Hot Reload: {'ON' if checked else 'OFF'}")
        self.hot_reload_label.setStyleSheet(f"color: {'green' if checked else 'gray'}; font-weight: bold;")
        self.hot_reload_btn.setText(f"Hot Reload: {'ON' if checked else 'OFF'}")
        self.hot_reload_toggled.emit(checked)

    def on_real_time_toggled(self, checked):
        self.real_time_label.setText(f"Real-Time: {'ON' if checked else 'OFF'}")
        self.real_time_label.setStyleSheet(f"color: {'green' if checked else 'gray'};")
        self.real_time_btn.setText(f"Real-Time: {'ON' if checked else 'OFF'}")
        self.real_time_toggled.emit(checked)

    def update_status(self, current_move: int, total_moves: int, playing: bool,
                     last_move: Optional[Tuple[int, int, int]] = None):
        self.move_label.setText(f"Move: {current_move}/{total_moves}")

        if last_move:
            x, y, player = last_move
            self.last_move_label.setText(f"Last Move: ({x}, {y}) by Player {player}")
        else:
            self.last_move_label.setText("Last Move: None")

        self.playback_label.setText(f"Playback: {'Playing' if playing else 'Paused'}")
        self.playback_label.setStyleSheet(f"color: {'green' if playing else 'red'};")

        self.play_pause_btn.setText("Pause" if playing else "Play")

    def show_winner(self, winner: int):
        self.winner_label.setText(f"Winner: Player {winner}!")
        self.winner_frame.setVisible(True)

    def hide_winner(self):
        self.winner_frame.setVisible(False)


class GomokuVisualizer(QMainWindow):

    def __init__(self, replay_file: Optional[str] = None):
        super().__init__()
        self.board_size = 20
        self.cell_size = 30

        self.moves = []
        self.current_move = 0
        self.playing = False
        self.speed = 1.0
        self.auto_reload = True
        self.real_time_mode = False

        self.replay_file = replay_file
        self.last_modified = 0
        self.liskvork_process = None

        self.setup_ui()
        self.setup_connections()

        if replay_file:
            self.load_replay(replay_file)

        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self.next_move)

        self.reload_timer = QTimer()
        self.reload_timer.timeout.connect(self.check_file_changes)
        self.reload_timer.start(1000)

    def setup_ui(self):
        self.setWindowTitle("Gomoku Replay Visualizer")
        self.setWindowIcon(QIcon())
        self.resize(1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.board_widget = BoardWidget(self.board_size, self.cell_size)
        splitter.addWidget(self.board_widget)

        self.control_panel = ControlPanel()
        self.control_panel.setMinimumWidth(300)
        self.control_panel.setMaximumWidth(400)
        splitter.addWidget(self.control_panel)

        splitter.setSizes([800, 300])

        main_layout.addWidget(splitter)

        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

    def setup_connections(self):
        self.control_panel.play_pause_clicked.connect(self.toggle_playback)
        self.control_panel.next_move_clicked.connect(self.next_move)
        self.control_panel.prev_move_clicked.connect(self.prev_move)
        self.control_panel.restart_clicked.connect(self.restart)
        self.control_panel.speed_changed.connect(self.set_speed)
        self.control_panel.hot_reload_toggled.connect(self.set_hot_reload)
        self.control_panel.real_time_toggled.connect(self.set_real_time)
        self.control_panel.launch_liskvork_clicked.connect(self.launch_liskvork)

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_Space:
            self.toggle_playback()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        if self.liskvork_process and self.liskvork_process.poll() is None:
            try:
                print("Terminating liskvork process...")
                self.liskvork_process.terminate()
                try:
                    self.liskvork_process.wait(timeout=3)
                    print("Liskvork process terminated gracefully")
                except subprocess.TimeoutExpired:
                    print("Process didn't terminate gracefully, force killing...")
                    self.liskvork_process.kill()
                    self.liskvork_process.wait(timeout=2)
                    print("Liskvork process force killed")
            except Exception as e:
                print(f"Error terminating liskvork process: {e}")
                try:
                    self.liskvork_process.kill()
                except:
                    pass
        event.accept()

    def load_replay(self, filename: str):
        try:
            parser = ReplayParser()
            self.moves = parser.parse_file(filename)
            self.current_move = 0
            self.replay_file = filename

            if os.path.exists(filename):
                self.last_modified = os.path.getmtime(filename)

            self.board_widget.update_board(self.moves, self.current_move)
            self.control_panel.update_status(self.current_move, len(self.moves), self.playing)
            self.control_panel.hide_winner()

            self.status_bar.showMessage(f"Loaded {len(self.moves)} moves from {filename}")

        except Exception as e:
            self.status_bar.showMessage(f"Error loading file: {str(e)}")

    def toggle_playback(self):
        if not self.real_time_mode:
            self.playing = not self.playing
            if self.playing:
                self.playback_timer.start(int(1000 / self.speed))
            else:
                self.playback_timer.stop()

            self.control_panel.update_status(self.current_move, len(self.moves), self.playing,
                                           self.moves[self.current_move - 1] if self.current_move > 0 else None)

    def next_move(self):
        if self.current_move < len(self.moves):
            self.current_move += 1
            self.board_widget.update_board(self.moves, self.current_move)

            winner = self.check_winner()
            if winner:
                self.control_panel.show_winner(winner)
                self.playing = False
                self.playback_timer.stop()

            self.control_panel.update_status(self.current_move, len(self.moves), self.playing,
                                           self.moves[self.current_move - 1])

    def prev_move(self):
        if self.current_move > 0:
            self.current_move -= 1
            self.board_widget.update_board(self.moves, self.current_move)
            self.control_panel.hide_winner()
            self.control_panel.update_status(self.current_move, len(self.moves), self.playing,
                                           self.moves[self.current_move - 1] if self.current_move > 0 else None)

    def restart(self):
        self.current_move = 0
        self.playing = False
        self.playback_timer.stop()
        self.board_widget.update_board(self.moves, self.current_move)
        self.control_panel.hide_winner()
        self.control_panel.update_status(self.current_move, len(self.moves), self.playing)

    def set_speed(self, speed: float):
        self.speed = speed
        if self.playing:
            self.playback_timer.setInterval(int(1000 / self.speed))

    def set_hot_reload(self, enabled: bool):
        self.auto_reload = enabled

    def set_real_time(self, enabled: bool):
        self.real_time_mode = enabled
        if enabled:
            self.current_move = len(self.moves)
            self.board_widget.update_board(self.moves, self.current_move)
            self.control_panel.update_status(self.current_move, len(self.moves), self.playing,
                                           self.moves[-1] if self.moves else None)

    def launch_liskvork(self):
        try:
            liskvork_path = os.path.join(os.path.dirname(__file__), "..", "liskvork", "liskvork")
            if not os.path.exists(liskvork_path):
                self.status_bar.showMessage("Error: liskvork executable not found")
                return

            cmd = [liskvork_path]

            self.status_bar.showMessage(f"Launching liskvork...")

            project_root = os.path.join(os.path.dirname(__file__), "..")
            with open(os.devnull, 'w') as devnull:
                self.liskvork_process = subprocess.Popen(
                    cmd,
                    cwd=project_root,
                    stdin=subprocess.DEVNULL,
                    stdout=devnull,
                    stderr=devnull
                )

        except Exception as e:
            self.status_bar.showMessage(f"Error launching liskvork: {str(e)}")

    def check_file_changes(self):
        if not self.replay_file or not self.auto_reload or not os.path.exists(self.replay_file):
            return

        try:
            current_modified = os.path.getmtime(self.replay_file)
            if current_modified > self.last_modified:
                self.status_bar.showMessage("File changed, reloading...")
                old_move_count = len(self.moves)

                parser = ReplayParser()
                new_moves = parser.parse_file(self.replay_file)

                if len(new_moves) != old_move_count:
                    self.moves = new_moves
                    self.last_modified = current_modified

                    if self.real_time_mode:
                        self.current_move = len(self.moves)
                        self.control_panel.update_status(self.current_move, len(self.moves), self.playing,
                                                       self.moves[-1] if self.moves else None)
                    else:
                        self.current_move = min(self.current_move, len(self.moves))

                    self.board_widget.update_board(self.moves, self.current_move)
                    self.status_bar.showMessage(f"Reloaded {len(self.moves)} moves")

        except Exception as e:
            self.status_bar.showMessage(f"Error checking file: {str(e)}")

    def check_winner(self) -> int:
        if self.current_move == 0:
            return 0

        last_move = self.moves[self.current_move - 1]
        x, y, player = last_move

        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

        for dx, dy in directions:
            count = 1

            tx, ty = x + dx, y + dy
            while 0 <= tx < self.board_size and 0 <= ty < self.board_size and self.get_stone_at(tx, ty) == player:
                count += 1
                tx += dx
                ty += dy

            tx, ty = x - dx, y - dy
            while 0 <= tx < self.board_size and 0 <= ty < self.board_size and self.get_stone_at(tx, ty) == player:
                count += 1
                tx -= dx
                ty -= dy

            if count >= 5:
                return player

        return

    def get_stone_at(self, x: int, y: int) -> int:
        for i in range(min(self.current_move, len(self.moves))):
            move_x, move_y, player = self.moves[i]
            if move_x == x and move_y == y:
                return player
        return 0


def main():
    app = QApplication(sys.argv)

    app.setApplicationName("Gomoku Visualizer")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("EPITECH")

    import argparse
    parser = argparse.ArgumentParser(description="Gomoku Replay Visualizer")
    parser.add_argument("replay_file", nargs="?", help="Replay file to visualize")
    parser.add_argument("--size", type=int, default=20, help="Board size (default: 20)")
    parser.add_argument("--cell-size", type=int, default=30, help="Cell size in pixels (default: 30)")

    args = parser.parse_args()

    window = GomokuVisualizer(args.replay_file)
    if args.size != 20 or args.cell_size != 30:
        pass

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
