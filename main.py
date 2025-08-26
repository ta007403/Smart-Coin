"""
Software Version: Smart Coin v1.0
Description:
    This script manages and controls various payment and transaction components
    in a self-service terminal or kiosk system. Supported hardware and interfaces
    include a coin acceptor, bill acceptor, NFC card reader, and support for digital
    bank transfers. It handles input from users, validates payment methods, processes
    transactions, and manages payment logic.

    Key features:
    - Accepts coins and bills through dedicated hardware interfaces
    - Supports contactless NFC card transactions
    - Enables bank transfer payment handling
    - Logs and monitors transaction status for system integrity

Author: Chanwut Norachan
Email: chanwut_norachan@hotmail.com
Version: 1.0.1
Created: 2025-08-05
Last Modified: 2025-08-20
"""
from PyQt5.QtWidgets import QApplication, QStackedWidget, QMainWindow, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QProgressBar
from PyQt5.QtGui import QFontDatabase, QFont, QGuiApplication
from PyQt5.QtCore import Qt, QEvent, QTimer, QRect
from PyQt5 import uic
from utils import config
import multiprocessing
from functools import partial
import threading
import resources_rc
import sys
import os
import time
import ast
import re
from dotenv import load_dotenv
from datetime import datetime
import serial

load_dotenv()

MACHINE_ID = os.getenv("MACHINE_ID")
if MACHINE_ID is None:
    raise RuntimeError(".env file is not set. Please check your .env file!")

WITHDRAW_FEE = os.getenv("WITHDRAW_FEE")
if WITHDRAW_FEE is None:
    raise RuntimeError(".env file is not set. Please check your .env file!")

WITHDRAW_FEE_USE_PERCENT = os.getenv("WITHDRAW_FEE_USE_PERCENT")
if WITHDRAW_FEE_USE_PERCENT is None:
    raise RuntimeError(".env file is not set. Please check your .env file!")

DEPOSIT_FEE = os.getenv("DEPOSIT_FEE")
if DEPOSIT_FEE is None:
    raise RuntimeError(".env file is not set. Please check your .env file!")

DEPOSIT_FEE_USE_PERCENT = os.getenv("DEPOSIT_FEE_USE_PERCENT")
if DEPOSIT_FEE_USE_PERCENT is None:
    raise RuntimeError(".env file is not set. Please check your .env file!")

WEB_SOCKET_URL = os.getenv("WEB_SOCKET_URL")
if WEB_SOCKET_URL is None:
    raise RuntimeError(".env file is not set. Please check your .env file!")

COIN_ACCEPTOR_PORT = os.getenv("COIN_ACCEPTOR_PORT")
if COIN_ACCEPTOR_PORT is None:
    raise RuntimeError(".env file is not set. Please check your .env file!")

BILL_ACCEPTOR_PORT = os.getenv("BILL_ACCEPTOR_PORT")
if BILL_ACCEPTOR_PORT is None:
    raise RuntimeError(".env file is not set. Please check your .env file!")

QR_CODE_READER_PORT = os.getenv("QR_CODE_READER_PORT")
if QR_CODE_READER_PORT is None:
    raise RuntimeError(".env file is not set. Please check your .env file!")

ARDUINO_GSM_PORT = os.getenv("ARDUINO_GSM_PORT")
if ARDUINO_GSM_PORT is None:
    raise RuntimeError(".env file is not set. Please check your .env file!")

ACCOUNT_NAME = os.getenv("ACCOUNT_NAME")
if ACCOUNT_NAME is None:
    raise RuntimeError(".env file is not set. Please check your .env file!")

PROMPTPAY_NUMBER = os.getenv("PROMPTPAY_NUMBER")
if PROMPTPAY_NUMBER is None:
    raise RuntimeError(".env file is not set. Please check your .env file!")

WITHDRAW_MEMO = os.getenv("WITHDRAW_MEMO")
if WITHDRAW_MEMO is None:
    raise RuntimeError(".env file is not set. Please check your .env file!")

NOTE_DISPENSER_100_PORT = os.getenv("NOTE_DISPENSER_100_PORT")
if NOTE_DISPENSER_100_PORT is None:
    raise RuntimeError(".env file is not set. Please check your .env file!")

NOTE_DISPENSER_500_PORT = os.getenv("NOTE_DISPENSER_500_PORT")
if NOTE_DISPENSER_500_PORT is None:
    raise RuntimeError(".env file is not set. Please check your .env file!")

NOTE_DISPENSER_1000_PORT = os.getenv("NOTE_DISPENSER_1000_PORT")
if NOTE_DISPENSER_1000_PORT is None:
    raise RuntimeError(".env file is not set. Please check your .env file!")

SERVER_API_HOST = os.getenv("SERVER_API_HOST")
if SERVER_API_HOST is None:
    raise RuntimeError(".env file is not set. Please check your .env file!")
    
SERVER_API_PORT = os.getenv("SERVER_API_PORT")
if SERVER_API_PORT is None:
    raise RuntimeError(".env file is not set. Please check your .env file!")

DAHSBOARD_HOST = os.getenv("DAHSBOARD_HOST")
if DAHSBOARD_HOST is None:
    raise RuntimeError(".env file is not set. Please check your .env file!")

DAHSBOARD_PORT = os.getenv("DAHSBOARD_PORT")
if DAHSBOARD_PORT is None:
    raise RuntimeError(".env file is not set. Please check your .env file!")

SOFTWARE_VERSION = os.getenv("SOFTWARE_VERSION")
if SOFTWARE_VERSION is None:
    raise RuntimeError(".env file is not set. Please check your .env file!")

TELEGRAM_ENABLE = os.getenv("TELEGRAM_ENABLE")
if TELEGRAM_ENABLE is None:
    raise RuntimeError(".env file is not set. Please check your .env file!")

BASE_FEE = os.getenv("BASE_FEE")
if BASE_FEE is None:
    raise RuntimeError(".env file is not set. Please check your .env file!")

MONEY_TRANSFER_NOT_CORRECT = os.getenv("MONEY_TRANSFER_NOT_CORRECT")
if MONEY_TRANSFER_NOT_CORRECT is None:
    raise RuntimeError(".env file is not set. Please check your .env file!")

LN_TRANFER_FAIL = os.getenv("LN_TRANFER_FAIL")
if LN_TRANFER_FAIL is None:
    raise RuntimeError(".env file is not set. Please check your .env file!")

NFC_MIN_LENGTH = 4
NFC_MAX_LENGTH = 20
MILLISAT = 1000
START_PAGE = 0
NEED_TO_CLEAR_LINE_EDIT = False
IDLE_TIMEOUT_MS = 300_000  # 5 minutes for go back to home page when no activity

# --- Import all modules ---
from modules.GSM_Module import ArduinoSMSAndReadWorker, ArduinoCheckStatusWorker, ArduinoSMSDeleteWorker, ArduinoGSMResetWorker
from modules.Lightning_Network import LNURLCheckerWorker, LNbitsWebSocketWorker, LNbitsInvoiceWorker, LNbitsBalanceWorker, CustomerInvoiceWorker, LNbitsPayWorker
from modules.Coin import CoinAcceptorProcess
from modules.Bill import BillAcceptorProcess
from modules.Telegram_notify import telegram_worker
from modules.Sound import play_sound_by_index
from modules.Schedule_Task import DailyTask
from modules.NFC import NFCReader, RefillCardWorker, NFCBalanceWorker, sync_card_database
from modules.Server_API import APIServerWorker, Server_API_Handler, update_IP_Linux
from modules.GPIO import GPIOMgr
from modules.Timer import TimerTask
from modules.Note_Dispenser import DispenserWorker
from modules.QR_Code_Reader import QRCodeReader
from modules.BTC_Price import BTCPriceFetcher
from utils.helpers import parse_lnurl, strip_http_prefix, generate_qr_pixmap, split_text_in_half, sum_banknote_value, extract_lnurl_from_text, extract_uid, extract_only_one_lnurl
from modules.Promptpay_Generate import generate_promptpay_payload
from modules.Can_Dispense import available_buttons, can_dispense, get_banknote_breakdown
from modules.JSON_Management import MoneyDataManager
from modules.Web_Dashboard import dashboard_flask_app
from modules.Thread_Checker import WatchdogChecker

def load_fonts():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    font_dir = os.path.join(BASE_DIR, 'assets/fonts')

    font1_path = os.path.join(font_dir, 'supermarket.ttf')
    font2_path = os.path.join(font_dir, 'norwester.otf')

    font_id = QFontDatabase.addApplicationFont(font1_path)
    font_families1 = QFontDatabase.applicationFontFamilies(font_id)
    if font_families1:
        QApplication.setFont(QFont(font_families1[0], 12))
    else:
        print("Font 1 load failed!")

    font_id = QFontDatabase.addApplicationFont(font2_path)
    font_families2 = QFontDatabase.applicationFontFamilies(font_id)
    if font_families2:
        QApplication.setFont(QFont(font_families2[0], 12))
    else:
        print("Font 2 load failed!")

class VirtualKeyboard(QWidget):
    def __init__(self, target_line_edit, parent=None):
        super().__init__(parent)
        self.target = target_line_edit
        self.shift_mode = False
        self.setWindowTitle("Virtual Keyboard")
        self.setStyleSheet("background-color: #f5f5f5;")
        self._filter_installed = False

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

         # ---- NEW FONT LINES ----
        self.preview_font = QFont("supermarket", 22, QFont.Bold)
        self.keyboard_font = QFont("supermarket", 22)
        
        self.button_style = """
            QPushButton {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #dddddd;
                border-radius: 10px;
                min-width: 30px;
                min-height: 30px;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background-color: #f2f2f2;
            }
            QPushButton:pressed {
                background-color: #a0e3a0; /* green press effect */
            }
        """

        self.setWindowFlags(
            Qt.Tool |
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint
        )

        self.setCursor(Qt.BlankCursor)
        self.setLayout(self.layout)

        # 👇 DEFER ALL THESE to next event loop
        QTimer.singleShot(100, self.defer_show_keyboard)  # ✅ DEFER actual display logic
        
    def defer_show_keyboard(self):
        screen = QGuiApplication.primaryScreen().availableGeometry()
        screen_width = screen.width()
        screen_height = screen.height()

        keyboard_height = int(screen_height * 0.92)
        keyboard_width = int(screen_width * 0.8)

        self.resize(keyboard_width, keyboard_height)
        self.move(82, 0)

        self.setFixedSize(self.size())

        QTimer.singleShot(100, self._final_show)

    def _final_show(self):
        self.show()
        self.raise_()
        self.activateWindow()

        QGuiApplication.processEvents()
        QTimer.singleShot(100, self.load_keys)

    def load_keys(self):
        global NEED_TO_CLEAR_LINE_EDIT
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # ✅ PREVIEW LABEL ROW
        self.preview_label = QLabel("")
        self.preview_label.setFont(QFont(self.preview_font))
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #ffffff;
                color: #222222;
                padding: 12px;
                border: 2px solid #cccccc;
                border-radius: 10px;
            }
        """)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setFixedHeight(60)
        # Set the preview text to the line edit's current text
        if NEED_TO_CLEAR_LINE_EDIT == True:
            self.preview_label.setText("")
            self.target.setText("")
            NEED_TO_CLEAR_LINE_EDIT = False
        else:
            self.preview_label.setText(self.target.text())
        self.layout.addWidget(self.preview_label)  # ✅ Insert as top row

        keys = [
            "1234567890",
            "qwertyuiop",
            "asdfghjkl",
            "zxcvbnm"
        ]

        for row in keys:
            row_layout = QHBoxLayout()
            for char in row:
                btn = QPushButton(char.upper() if self.shift_mode else char.lower())
                btn.setFont(self.keyboard_font)
                btn.clicked.connect(partial(self.key_pressed, char))
                btn.setStyleSheet(self.button_style)
                row_layout.addWidget(btn)
            self.layout.addLayout(row_layout)

        special_layout = QHBoxLayout()

        #shift = QPushButton("⇧ Shift")
        #shift.clicked.connect(self.toggle_shift)  # no need for partial with no arguments
        #shift.setStyleSheet(self.button_style)
        #special_layout.addWidget(shift)

        walletofsatoshi = QPushButton("@walletofsatoshi.com")
        walletofsatoshi.setFont(self.keyboard_font)
        walletofsatoshi.clicked.connect(partial(self.key_pressed, "@walletofsatoshi.com"))
        walletofsatoshi.setStyleSheet(self.button_style)
        special_layout.addWidget(walletofsatoshi)

        for char in ["@", ".", ".com"]:
            btn = QPushButton(char)
            btn.setFont(self.keyboard_font)
            btn.clicked.connect(partial(self.key_pressed, char))
            btn.setStyleSheet(self.button_style)
            special_layout.addWidget(btn)

        self.layout.addLayout(special_layout)

        control_layout = QHBoxLayout()

        clear_all = QPushButton("🗑️ Clear All")
        clear_all.setFont(self.keyboard_font)
        clear_all.clicked.connect(self.clear_all)
        clear_all.setStyleSheet(self.button_style)
        control_layout.addWidget(clear_all)

        backspace = QPushButton("⌫ Backspace")
        backspace.setFont(self.keyboard_font)
        backspace.clicked.connect(self.backspace)
        backspace.setStyleSheet(self.button_style)
        control_layout.addWidget(backspace)

        enter = QPushButton("✔ Enter")
        enter.setFont(self.keyboard_font)
        enter.clicked.connect(self.finish)
        enter.setStyleSheet(self.button_style)
        control_layout.addWidget(enter)

        self.layout.addLayout(control_layout)

    def key_pressed(self, char):
        play_sound_by_index(10)
        text = self.target.text()
        if self.shift_mode:
            char = char.upper()
        else:
            char = char.lower()
        self.target.setText(text + char)
        self.preview_label.setText(self.target.text())  # ✅ mirror to label

    def backspace(self):
        play_sound_by_index(10)
        text = self.target.text()
        self.target.setText(text[:-1])
        self.preview_label.setText(self.target.text())  # ✅ update preview

    def clear_all(self):
        play_sound_by_index(10)
        self.target.setText("")               # Clear QLineEdit
        self.preview_label.setText("")        # Clear preview label

    # def toggle_shift(self):
    #     self.shift_mode = not self.shift_mode
    #     self.load_keys()

    def showEvent(self, event):
        super().showEvent(event)
        if self.parent() and not self._filter_installed:
            self.parent().installEventFilter(self)
            self._filter_installed = True

    # This function is use for prevent customer touch outside the keyboard
    def eventFilter(self, obj, event):
        KEYBOARD_X = 0
        KEYBOARD_Y = 0
        KEYBOARD_W = 800
        KEYBOARD_H = 480

        if event.type() == QEvent.MouseButtonPress:
            # If click is outside the keyboard, close it
            keyboard_rect = QRect(KEYBOARD_X, KEYBOARD_Y, KEYBOARD_W, KEYBOARD_H)
            if not keyboard_rect.contains(event.globalPos()):
                self.finish()
                return True  # eat event so it doesn't focus anything else
        return super().eventFilter(obj, event)

    def finish(self):
        print("VirtualKeyboard.finish() called")  # Debug!
        play_sound_by_index(10)
        # Show the buttons again
        self.main_window.helpButton_page2.show()
        self.main_window.backButton_page2.show()
        #self.preview_label.setText("")
        # Remove event filter if present
        if self.parent() and self._filter_installed:
            self.parent().removeEventFilter(self)
            self._filter_installed = False
        self.close()

class MainWindow(QMainWindow):
    last_scan = {"type": None, "raw": None, "parsed": None, "sat": None, "payment_type": None, "timestamp": None, "THB": None}
    note_stock = {1000: 0, 500: 0, 100: 0} # This variable is just a temporary use

    def __init__(self):
        super().__init__()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        ui_path = os.path.join(script_dir, "Main_Page.ui")
        uic.loadUi(ui_path, self)
        self.setup_connections()
        self.progress_states = {}  # To track multiple progress bars
        self.selected_thb = None
        self.PRESS_OK_PAGE2_FLAG = False

        # self.start_reset_GSM()

        self.coin_counts = {1: 0, 2: 0, 5: 0, 10: 0}
        self.note_counts = {20: 0, 50: 0, 100: 0, 500: 0, 1000: 0}
        self.invoice = ""
        self.current_page = 0

        self.gpio = GPIOMgr()
        #self.gpio.set_pin(27, 1)  # Set pin 17 HIGH (on)
        self.gpio.set_led(True)  # Turn LED on

        if TELEGRAM_ENABLE == "True":
            telegram_worker(f"Hello, Smart Coin Just Start Now")

        # This function is use for update server API
        self.manager = MoneyDataManager()
        self.manager.set_smart_coin_software_version(SOFTWARE_VERSION)

        # Create worker for arduino GSM status and get firmware version
        self.arduino_sms_check_status()

        # This line is use for quick sync NFC database
        sync_card_database()
        NFC_Wallet_count = self.manager.count_wallets_in_file()
        self.manager.set_amount_of_nfc_wallet(NFC_Wallet_count)

        self.delete_worker = None
        self.ser = serial.Serial(ARDUINO_GSM_PORT, 9600, timeout=0.2)

        # Inactivity timer
        self.idle_timer = QTimer(self)
        self.idle_timer.setInterval(IDLE_TIMEOUT_MS)
        self.idle_timer.timeout.connect(self.go_home)
        self.idle_timer.start()

        # Install event filter for all input events
        self.installEventFilter(self)
		
        # This is for version 1
        if SOFTWARE_VERSION == "Smart Coin v1.0" or SOFTWARE_VERSION == "Smart Coin v1.2":
            self.withdrawButton_page0.hide()
            self.depositButton_page0.move(280, 310)
    

        # This variable is a real use for limit banknotes in withdrawal state
        self.LIMITBANKNOTE100 = self.manager.get_current_banknote_100()
        self.LIMITBANKNOTE500 = self.manager.get_current_banknote_500()
        self.LIMITBANKNOTE1000 = self.manager.get_current_banknote_1000()

        # Create worker for API server
        self.api_worker = APIServerWorker(SERVER_API_HOST, int(SERVER_API_PORT), Server_API_Handler)
        self.api_worker.server_started.connect(lambda: print("API Server Started!"))
        self.api_worker.start()

        # Enable dashboard
        flask_thread = threading.Thread(
            target=dashboard_flask_app.run,
            name="Dashboard Server",
            kwargs={
                'host': DAHSBOARD_HOST,
                'port': int(DAHSBOARD_PORT),
                'debug': False,
                'use_reloader': False
            }
        )
        flask_thread.daemon = True
        flask_thread.start()

        # Create daily task
        self.morning_worker = DailyTask("morning", "Asia/Bangkok", self.morning_task, False)
        self.morning_worker.start()
        self.evening_worker = DailyTask("evening", "Asia/Bangkok", self.evening_task, False)
        self.evening_worker.start()
        section = DailyTask.get_time_section()
        print(f"It's {section} now.")
        if section == "morning":
            self.transferButton_page3.show()
            self.midnight_warn_page3.hide()
        else:
            self.transferButton_page3.hide()
            self.midnight_warn_page3.show()
        
        # Connect virtual keyboard
        self.LNAddresslineEdit_page2.mousePressEvent = self.show_keyboard

        # Change deposit button
        self.depositButton_page0.setStyleSheet("""
            QPushButton {
                background-color: #1db954;
                color: rgb(122, 26, 247);
                padding-top: 20px;
            }
        """)
        # Change withdraw button
        self.withdrawButton_page0.setStyleSheet("""
            QPushButton {
                background-color: #f7931b;
                color: rgb(122, 26, 247);
                padding-top: 20px;
            }
        """)
        # Change bank transfer button
        self.transferButton_page3.setStyleSheet("""
            QPushButton {
                background-color: #1db954;
                color: rgb(122, 26, 247);
                padding-top: 20px;
            }
        """)
        # Change cash and coin button
        self.coinNoteButton_page3.setStyleSheet("""
            QPushButton {
                background-color: #f7931b;
                color: rgb(122, 26, 247);
                padding-top: 20px;
            }
        """)

        # Create watchdog to monitor thread and worker
        #self.thread_watchdog = WatchdogChecker(refresh_interval=60)
        #self.thread_watchdog.status_report.connect(self.handle_status_report)
        #self.thread_watchdog.start()

        # Create worker for coin acceptor
        self.coin_result_queue = multiprocessing.Queue()
        self.coin_command_queue = multiprocessing.Queue()
        self.coin_proc = CoinAcceptorProcess(
            port=COIN_ACCEPTOR_PORT,
            result_queue=self.coin_result_queue,
            command_queue=self.coin_command_queue
        )
        self.coin_proc.start()

        self.coin_poll_timer = QTimer()
        self.coin_poll_timer.timeout.connect(self.poll_coin_queue)
        self.coin_poll_timer.start(50)
        self.disable_coin()

        # Create worker for bill acceptor
        self.bill_result_queue = multiprocessing.Queue()
        self.bill_command_queue = multiprocessing.Queue()
        self.bill_proc = BillAcceptorProcess(
            port=BILL_ACCEPTOR_PORT,
            result_queue=self.bill_result_queue,
            command_queue=self.bill_command_queue
        )
        self.bill_proc.start()

        self.bill_poll_timer = QTimer()
        self.bill_poll_timer.timeout.connect(self.poll_bill_queue)
        self.bill_poll_timer.start(50)
        while True:
            if not self.bill_result_queue.empty():
                msg, val = self.bill_result_queue.get_nowait()
                print(f"[DEBUG] Bill process msg: {msg}, {val}")
                if msg == "info" and "ready" in val:
                    break
            time.sleep(0.05)
        self.disable_bill()

        # This variable use for withdraw page
        self.selected_amount = None
        self.WithdrawBanknote_100_THB = 0
        self.WithdrawBanknote_500_THB = 0
        self.WithdrawBanknote_1000_THB = 0

        # This is button for withdrawal section
        self.amount_buttons = {
            self.Button100_page27: (100, self.label_sat_100_page27),
            self.Button200_page27: (200, self.label_sat_200_page27),
            self.Button300_page27: (300, self.label_sat_300_page27),
            self.Button400_page27: (400, self.label_sat_400_page27),
            self.Button500_page27: (500, self.label_sat_500_page27),
            self.Button600_page27: (600, self.label_sat_600_page27),
            self.Button700_page27: (700, self.label_sat_700_page27),
            self.Button800_page27: (800, self.label_sat_800_page27),
            self.Button900_page27: (900, self.label_sat_900_page27),
            self.Button1000_page27: (1000, self.label_sat_1000_page27),
            self.Button1500_page27: (1500, self.label_sat_1500_page27),
            self.Button2000_page27: (2000, self.label_sat_2000_page27),
        }

        # Connect all amount buttons to withdrawal handler
        for button, value in self.amount_buttons.items():
            button.clicked.connect(lambda checked, v=value[0]: self.handle_amount_selected(v))
            button.clicked.connect(lambda: play_sound_by_index(5)) # Sound

        # This is button for deposit section
        self.thb_buttons = {
            20:  (self.Button20_page4,  12,  self.label_sat_20_page4),
            50:  (self.Button50_page4,  13,  self.label_sat_50_page4),
            100: (self.Button100_page4, 14, self.label_sat_100_page4),
            200: (self.Button200_page4, 15, self.label_sat_200_page4),
            300: (self.Button300_page4, 16, self.label_sat_300_page4),
            400: (self.Button400_page4, 17, self.label_sat_400_page4),
            500: (self.Button500_page4, 18, self.label_sat_500_page4),
            800: (self.Button800_page4, 19, self.label_sat_800_page4),
            1000: (self.Button1000_page4, 20, self.label_sat_1000_page4),
            1500: (self.Button1500_page4, 21, self.label_sat_1500_page4),
            2000: (self.Button2000_page4, 22, self.label_sat_2000_page4),
            3000: (self.Button3000_page4, 23, self.label_sat_3000_page4),
        }

        # Connect all amount buttons to deposit handler
        for value, (button, target_page, label) in self.thb_buttons.items():
            button.clicked.connect(lambda checked, v=value: self.on_thb_button_clicked(v))
            button.clicked.connect(lambda: play_sound_by_index(5)) # Sound

        #self.gpio.set_pin(27, 0)  # Set pin 17 LOW (off)
        self.gpio.set_led(False)  # Turn LED off

    # This function is for take back to home page when no activity
    def go_home(self):
        if self.current_page in (1, 2, 3, 4, 9, 10, 27, 28):
            self.goto_page(0)  # Switch to home page
            print("Returned to HOME PAGE due to inactivity.")

    # This function is for take back to home page when no activity
    def reset_idle_timer(self):
        self.idle_timer.start()

    # This function is for take back to home page when no activity
    def eventFilter(self, obj, event):
        # Catch user input events and reset timer
        if event.type() in (event.MouseButtonPress, event.MouseButtonRelease,
                            event.KeyPress, event.KeyRelease, event.TouchBegin,
                            event.TouchEnd, event.TouchUpdate):
            self.reset_idle_timer()
        return super().eventFilter(obj, event)

    # This function is for page 4 which is decide the amount of transfer and generate promptpay QR code
    def on_thb_button_clicked(self, amount):
        self.goto_page(11)
        self.selected_thb = None
        self.selected_thb = amount
        self.last_scan['payment_type'] = "Bank_Transfer" # This line is identify payment type which is coin and note or bank transfer
        #print(f"This is amount {amount} selected")
        self.thbHeader_page11.setText(f"จำนวนเงิน {amount:,} บาท")
        self.accountHeader_page11.setText(f"บัญชี {ACCOUNT_NAME}")
        payload = generate_promptpay_payload(PROMPTPAY_NUMBER, amount)
        #print(payload)
        data_to_encode = str(payload)
        qr_pixmap = generate_qr_pixmap(data_to_encode, size=320)
        self.label_qrcode_page11.setPixmap(qr_pixmap)

    def morning_task(self):
        print("[TASK] Good morning! This is your scheduled task.")
        print(f"Today is [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
        IP_Address = update_IP_Linux()
        print(f"This is our IP: {IP_Address}")
        self.transferButton_page3.show()
        self.midnight_warn_page3.hide()
        sync_card_database()
        NFC_Wallet_count = self.manager.count_wallets_in_file()
        self.manager.set_amount_of_nfc_wallet(NFC_Wallet_count)
        self.start_reset_GSM()

    def evening_task(self):
        print("[TASK] Good evening! This is your scheduled task.")
        self.transferButton_page3.hide()
        self.midnight_warn_page3.show()

    # This function use for connect all button signal
    def setup_connections(self):
        # Page 0
        self.withdrawButton_page0.clicked.connect(self.update_withdrawal_buttons)
        self.withdrawButton_page0.clicked.connect(self.update_thb_labels_page27)
        self.withdrawButton_page0.clicked.connect(lambda: self.goto_page(27))
        self.depositButton_page0.clicked.connect(lambda: self.goto_page(2))
        self.feeButton_page0.clicked.connect(lambda: self.goto_page(1))
        self.feeButton_page0.clicked.connect(self.update_fee_page)
        self.nfcBalanceButton_page0.clicked.connect(lambda: self.goto_page(9))
        self.nfcBalanceButton_page0.clicked.connect(self.clear_label_page9)
        self.withdrawButton_page0.clicked.connect(lambda: play_sound_by_index(5)) # Sound
        self.depositButton_page0.clicked.connect(lambda: play_sound_by_index(5)) # Sound
        self.nfcBalanceButton_page0.clicked.connect(lambda: play_sound_by_index(5)) # Sound
        self.feeButton_page0.clicked.connect(lambda: play_sound_by_index(5)) # Sound
        
        # Page 1
        self.backButton_page1.clicked.connect(lambda: self.goto_page(0))
        self.backButton_page1.clicked.connect(lambda: play_sound_by_index(5)) # Sound

        # Page 2
        self.backButton_page2.clicked.connect(lambda: self.goto_page(0))
        self.helpButton_page2.clicked.connect(lambda: self.goto_page(10))
        self.okButton_page2.clicked.connect(self.on_ok_page2)
        self.backButton_page2.clicked.connect(lambda: play_sound_by_index(5)) # Sound
        self.helpButton_page2.clicked.connect(lambda: play_sound_by_index(5)) # Sound
        self.okButton_page2.clicked.connect(lambda: play_sound_by_index(5)) # Sound

        # page 3
        self.coinNoteButton_page3.clicked.connect(lambda: self.goto_page(6))
        self.coinNoteButton_page3.clicked.connect(lambda: self.enable_coin())
        self.coinNoteButton_page3.clicked.connect(lambda: self.enable_bill())
        self.coinNoteButton_page3.clicked.connect(self.reset_counts)
        self.coinNoteButton_page3.clicked.connect(self.backButton_page6.show)
        self.coinNoteButton_page3.clicked.connect(self.okButton_page6.hide)
        self.cancelButton_page3.clicked.connect(lambda: self.goto_page(0))
        self.transferButton_page3.clicked.connect(lambda: self.goto_page(4))
        self.transferButton_page3.clicked.connect(self.start_arduino_sms_listener)
        self.transferButton_page3.clicked.connect(self.update_thb_labels_page4)
        self.coinNoteButton_page3.clicked.connect(lambda: play_sound_by_index(5)) # Sound
        self.cancelButton_page3.clicked.connect(lambda: play_sound_by_index(5)) # Sound
        self.transferButton_page3.clicked.connect(lambda: play_sound_by_index(5)) # Sound

        # page 4
        self.backButton_page4.clicked.connect(lambda: self.goto_page(3))
        self.cancelButton_page4.clicked.connect(lambda: self.goto_page(0))
        self.backButton_page4.clicked.connect(lambda: play_sound_by_index(5)) # Sound
        self.cancelButton_page4.clicked.connect(lambda: play_sound_by_index(5)) # Sound
        self.cancelButton_page4.clicked.connect(lambda: setattr(self, 'selected_thb', None))

        # page 6
        if SOFTWARE_VERSION == "Smart Coin v1.2":
            self.backButton_page6.clicked.connect(lambda: self.goto_page(2))
            
        else:
            self.backButton_page6.clicked.connect(lambda: self.goto_page(3))
        self.backButton_page6.clicked.connect(lambda: self.disable_coin())
        self.okButton_page6.clicked.connect(lambda: self.disable_coin())
        self.backButton_page6.clicked.connect(lambda: self.disable_bill())
        self.okButton_page6.clicked.connect(lambda: self.disable_bill())
        self.okButton_page6.clicked.connect(self.handle_LN_process_transfer_page5)
        self.okButton_page6.clicked.connect(self.backButton_page6.show)
        self.backButton_page6.clicked.connect(lambda: play_sound_by_index(5)) # Sound
        self.okButton_page6.clicked.connect(lambda: play_sound_by_index(5)) # Sound
        self.backButton_page6.clicked.connect(self.reset_counts)

        # page 8
        self.cancelButton_page8.clicked.connect(lambda: self.goto_page(0))
        self.okButton_page8.clicked.connect(self.handle_LN_process_transfer_page5)
        self.cancelButton_page8.clicked.connect(lambda: play_sound_by_index(5)) # Sound
        self.okButton_page8.clicked.connect(lambda: play_sound_by_index(5)) # Sound
        
        # page 9
        self.backButton_page9.clicked.connect(lambda: self.goto_page(0))
        self.backButton_page9.clicked.connect(lambda: play_sound_by_index(5)) # Sound

        # page 10
        self.cancelButton_page10.clicked.connect(lambda: self.goto_page(0))
        self.understandButton_page10.clicked.connect(lambda: self.goto_page(2))
        self.cancelButton_page10.clicked.connect(lambda: play_sound_by_index(5)) # Sound
        self.understandButton_page10.clicked.connect(lambda: play_sound_by_index(5)) # Sound

        # page 11
        self.methodButton_page11.clicked.connect(lambda checked=False: self.goto_page(3))
        self.cancelButton_page11.clicked.connect(lambda checked=False: self.goto_page(0))
        self.methodButton_page11.clicked.connect(lambda: play_sound_by_index(5)) # Sound
        self.cancelButton_page11.clicked.connect(lambda: play_sound_by_index(5)) # Sound
        # page 12 to page 23
        #for page in range(12, 24):  # 12 to 23 inclusive
        #    cancel_btn = getattr(self, f'cancelButton_page{page}')
        #    method_btn = getattr(self, f'methodButton_page{page}')
        #    cancel_btn.clicked.connect(lambda checked=False: self.goto_page(0))
        #    method_btn.clicked.connect(lambda checked=False: self.goto_page(3))
        #    cancel_btn.clicked.connect(self.stop_sms_worker)
        #    method_btn.clicked.connect(self.stop_sms_worker)

        # page 24
        self.cancelButton_page24.clicked.connect(lambda: self.goto_page(0))
        self.cancelButton_page24.clicked.connect(lambda: play_sound_by_index(5)) # Sound

        # page 25
        self.cancelButton_page25.clicked.connect(lambda: self.goto_page(0))
        self.cancelButton_page25.clicked.connect(lambda: play_sound_by_index(5)) # Sound

        # page 27
        self.backButton_page27.clicked.connect(lambda: self.goto_page(0))
        self.customizeButton_page27.clicked.connect(lambda: self.goto_page(28))
        self.customizeButton_page27.clicked.connect(self.clear_withdraw_values_page28)
        self.customizeButton_page27.clicked.connect(self.show_total_value)
        self.backButton_page27.clicked.connect(lambda: play_sound_by_index(5)) # Sound
        self.customizeButton_page27.clicked.connect(lambda: play_sound_by_index(5)) # Sound

        # page 28
        # Connect increase/decrease buttons to handlers
        self.increase100Button_page28.clicked.connect(lambda: self.adjust_banknote('100', 1))
        self.decrease100Button_page28.clicked.connect(lambda: self.adjust_banknote('100', -1))
        self.increase500Button_page28.clicked.connect(lambda: self.adjust_banknote('500', 1))
        self.decrease500Button_page28.clicked.connect(lambda: self.adjust_banknote('500', -1))
        self.increase1000Button_page28.clicked.connect(lambda: self.adjust_banknote('1000', 1))
        self.decrease1000Button_page28.clicked.connect(lambda: self.adjust_banknote('1000', -1))
        self.backButton_page28.clicked.connect(lambda: self.goto_page(27))
        self.okButton_page28.clicked.connect(lambda: self.goto_page(29))
        self.okButton_page28.clicked.connect(self.generate_QR_page_29)
        self.increase100Button_page28.clicked.connect(lambda: play_sound_by_index(10)) # Sound
        self.increase500Button_page28.clicked.connect(lambda: play_sound_by_index(10)) # Sound
        self.increase1000Button_page28.clicked.connect(lambda: play_sound_by_index(10)) # Sound
        self.decrease100Button_page28.clicked.connect(lambda: play_sound_by_index(10)) # Sound
        self.decrease500Button_page28.clicked.connect(lambda: play_sound_by_index(10)) # Sound
        self.decrease1000Button_page28.clicked.connect(lambda: play_sound_by_index(10)) # Sound
        self.backButton_page28.clicked.connect(lambda: play_sound_by_index(5)) # Sound
        self.okButton_page28.clicked.connect(lambda: play_sound_by_index(5)) # Sound
        self.backButton_page28.clicked.connect(self.clear_withdraw_values_page28)
        
        # page 29
        self.backButton_page29.clicked.connect(lambda: self.goto_page(27))
        self.cancelButton_page29.clicked.connect(lambda: self.goto_page(0))
        self.backButton_page29.clicked.connect(lambda: self.stop_web_socket_worker(27))
        self.cancelButton_page29.clicked.connect(lambda: self.stop_web_socket_worker(0, self.clear_withdraw_values_page28))
        self.backButton_page29.clicked.connect(lambda: play_sound_by_index(5)) # Sound
        self.cancelButton_page29.clicked.connect(lambda: play_sound_by_index(5)) # Sound
        #self.cancelButton_page29.clicked.connect(self.clear_withdraw_values_page28)

    def update_withdrawal_buttons(self):
        # List of all amounts you want to check/buttons you want to control
        button_amounts = [
            100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1500, 2000
        ]

        self.LIMITBANKNOTE100 = self.manager.get_current_banknote_100()
        self.LIMITBANKNOTE500 = self.manager.get_current_banknote_500()
        self.LIMITBANKNOTE1000 = self.manager.get_current_banknote_1000()

        # Get available amounts using your Can_Dispense logic
        denominations = [100, 500, 1000]
        self.note_stock = {den: getattr(self, f"LIMITBANKNOTE{den}", 0) for den in denominations}
        can_show_amounts = available_buttons(self.note_stock, button_amounts)

        # Loop through all expected buttons by name
        for amt in button_amounts:
            label_name = f'label_sat_{amt}_page27'
            btn_name = f'Button{amt}_page27'
            btn = getattr(self, btn_name, None)
            label = getattr(self, label_name, None)
            if btn:
                if amt in can_show_amounts:
                    btn.show()
                    label.show()
                else:
                    btn.hide()
                    label.hide()
                # If you want to hide: btn.setVisible(amt in can_show_amounts)
            else:
                print(f"Warning: No such button {btn_name} in UI!")      

    def start_delete_sms(self):
        # Start and connect both signals!
        self.ser = serial.Serial(
            port=ARDUINO_GSM_PORT,
            baudrate=9600,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1       # 1 second timeout for .read() and .readline()
        )
        self.delete_worker = ArduinoSMSDeleteWorker(self.ser)
        self.delete_worker.delete_done.connect(self.handle_delete_done)
        self.delete_worker.finished.connect(self.cleanup_delete_worker)
        self.delete_worker.start()

    def handle_delete_done(self, response):
        print("Delete finished:", response)
        # Do NOT set self.delete_worker = None here!

    def cleanup_delete_worker(self):
        print("Delete worker thread finished, now cleanup reference.")
        self.delete_worker = None

    def start_reset_GSM(self):
        # Start and connect both signals!
        self.ser = serial.Serial(
            port=ARDUINO_GSM_PORT,
            baudrate=9600,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1       # 1 second timeout for .read() and .readline()
        )
        self.GSM_reset_worker = ArduinoGSMResetWorker(self.ser)
        self.GSM_reset_worker.reset_done.connect(self.handle_reset_done)
        self.GSM_reset_worker.start()

    def handle_reset_done(self, response):
        print("Reset GSM Module finished:", response)

    # This function is for page 4
    def start_arduino_sms_listener(self):
        self.sms_worker = ArduinoSMSAndReadWorker(port=ARDUINO_GSM_PORT)
        self.sms_worker.cmti_detected.connect(self.on_cmti_detected)
        #self.sms_worker.arduino_line.connect(self.on_arduino_line)  # optional
        self.sms_worker.sms_parsed.connect(self.on_arduino_line)
        self.sms_worker.finished.connect(self.on_sms_worker_finished)
        self.sms_worker.start()

    # This function use for update arduino SMS version
    def arduino_sms_check_status(self):
        print("arduino_sms_check_status start")
        self.sms_status_worker = ArduinoCheckStatusWorker(port=ARDUINO_GSM_PORT)
        self.sms_status_worker.arduino_status.connect(self.handle_arduino_status)
        self.sms_status_worker.start()

    # This function use for update arduino SMS version
    def handle_arduino_status(self, lines):
        # Example input: ['FW: 2.1  (Jun 26 2025 21:59:50)']
        if not lines:
            print("No STATUS lines received!")
            return

        first_line = lines[0]
        match = re.search(r'FW:\s*([^\s]+)', first_line)
        if match:
            app_version = match.group(1) 
            #print("Extracted firmware version:", app_version)
            self.manager.set_arduino_firmware_version(app_version)
        else:
            print("FW version not found in status line.")

    # This function is for page 4
    def on_cmti_detected(self, line):
        print(f"CMTI Detected: {line}")
        self.goto_page(26)
        self.start_progress_animation(self.progressBar_page26, 10)
        play_sound_by_index(14)

    # This function is for page 4 and this is the last function which is get called when customer transfer before go to LN process
    def on_arduino_line(self, line):
        self.manager.refresh_json_data()
        print(f"Arduino: {line}")

        if isinstance(line, dict):  # It's already parsed!
            if "amount" in line:
                amount = line["amount"]
                temp_amount = line["amount"]
                print(f"[INFO] Parsed transfer amount from dict: {amount}")
                print(f"self.selected_thb = {self.selected_thb}")
                if DEPOSIT_FEE_USE_PERCENT == "False":
                    self.last_scan['sat'] = (int(amount) - int(DEPOSIT_FEE)) * int(config.SATS_PER_THB) # This line is contain variable which is correct sat summary
                else:
                    temp_amount -= int(BASE_FEE)
                    self.last_scan['sat'] = (int(temp_amount) - (int(DEPOSIT_FEE) * int(temp_amount)) // 100) * int(config.SATS_PER_THB) # This line is contain variable which is correct sat summary

                if amount == self.selected_thb:
                    self.last_scan['THB'] = amount
                    transfer_temp = self.manager.get_customer_transferred_amount()
                    transfer_temp += int(self.selected_thb)
                    self.manager.set_customer_transferred_amount(transfer_temp)
                    self.handle_LN_process_transfer_page5() # Transfer success
                    self.stop_sms_worker()
                else:
                    self.last_scan['THB'] = amount
                    transfer_temp = self.manager.get_customer_transferred_amount()
                    transfer_temp += int(amount)
                    self.manager.set_customer_transferred_amount(transfer_temp)
                    self.label_THB_page8.setText(f"{amount} บาท")
                    self.label_Sat_page8.setText(f"{self.last_scan['sat']} Sat") # This line is show deducted sat that customer will receive
                    play_sound_by_index(9)
                    self.goto_page(8) # Transfer not equal to selected choice
                    self.contactHeader_page8.setText(MONEY_TRANSFER_NOT_CORRECT)
                    self.stop_sms_worker()
        elif isinstance(line, str):
            if line.startswith("Arduino: {"):
                dict_str = line[len("Arduino: "):].strip()
                try:
                    data = ast.literal_eval(dict_str)
                    if isinstance(data, dict) and "amount" in data:
                        amount = data["amount"]
                        print(f"[INFO] Parsed transfer amount from dict string: {amount}")
                        print(f"self.selected_thb = {self.selected_thb}")
                        if DEPOSIT_FEE_USE_PERCENT == "False":
                            self.last_scan['sat'] = (int(amount) - int(DEPOSIT_FEE)) * int(config.SATS_PER_THB) # This line is contain variable which is correct sat summary
                        else:
                            temp_amount -= int(BASE_FEE)
                            self.last_scan['sat'] = (int(temp_amount) - (int(DEPOSIT_FEE) * int(temp_amount)) // 100) * int(config.SATS_PER_THB) # This line is contain variable which is correct sat summary

                        if amount == self.selected_thb:
                            self.last_scan['THB'] = amount
                            transfer_temp = self.manager.get_customer_transferred_amount()
                            transfer_temp += int(self.selected_thb)
                            self.manager.set_customer_transferred_amount(transfer_temp)
                            self.handle_LN_process_transfer_page5() # Transfer success
                            self.stop_sms_worker()
                        else:
                            self.last_scan['THB'] = amount
                            transfer_temp = self.manager.get_customer_transferred_amount()
                            transfer_temp += int(amount)
                            self.manager.set_customer_transferred_amount(transfer_temp)
                            self.label_THB_page8.setText(f"{amount} บาท")
                            self.label_Sat_page8.setText(f"{self.last_scan['sat']} Sat") # This line is show deducted sat that customer will receive
                            play_sound_by_index(9)
                            self.goto_page(8) # Transfer not equal to selected choice
                            self.contactHeader_page8.setText(MONEY_TRANSFER_NOT_CORRECT)
                            self.stop_sms_worker()
                except Exception as e:
                    print(f"[WARN] Could not parse Arduino line as dict: {e}")
            elif "Amount:" in line:
                match = re.search(r'Amount:\s*([\d\.]+)', line)
                if match:
                    amount = float(match.group(1))
                    print(f"[INFO] Parsed transfer amount: {amount}")
                    print(f"self.selected_thb = {self.selected_thb}")
                    if DEPOSIT_FEE_USE_PERCENT == "False":
                        self.last_scan['sat'] = (int(amount) - int(DEPOSIT_FEE)) * int(config.SATS_PER_THB) # This line is contain variable which is correct sat summary
                    else:
                        temp_amount -= int(BASE_FEE)
                        self.last_scan['sat'] = (int(temp_amount) - (int(DEPOSIT_FEE) * int(temp_amount)) // 100) * int(config.SATS_PER_THB) # This line is contain variable which is correct sat summary

                    if amount == self.selected_thb:
                        self.last_scan['THB'] = amount
                        transfer_temp = self.manager.get_customer_transferred_amount()
                        transfer_temp += int(self.selected_thb)
                        self.manager.set_customer_transferred_amount(transfer_temp)
                        self.handle_LN_process_transfer_page5() # Transfer success
                        self.stop_sms_worker()
                    else:
                        self.last_scan['THB'] = amount
                        transfer_temp = self.manager.get_customer_transferred_amount()
                        transfer_temp += int(amount)
                        self.manager.set_customer_transferred_amount(transfer_temp)
                        self.label_THB_page8.setText(f"{amount} บาท")
                        self.label_Sat_page8.setText(f"{self.last_scan['sat']} Sat") # This line is show deducted sat that customer will receive
                        play_sound_by_index(9)
                        self.goto_page(8) # Transfer not equal to selected choice
                        self.contactHeader_page8.setText(MONEY_TRANSFER_NOT_CORRECT)
                        self.stop_sms_worker()

    # This function is for page 4
    def on_sms_worker_finished(self):
        print("SMS listening worker finished.")
        # go to somewhere

    # This function is for page 4
    def stop_sms_worker(self):
        if hasattr(self, "sms_worker") and self.sms_worker is not None:
            if self.sms_worker.isRunning():
                self.sms_worker.stop()
                print("[INFO] Stopped sms_worker thread.")
            else:
                print("[INFO] sms_worker was not running.")
        else:
            print("[INFO] sms_worker does not exist.")

    # This function is for page 4
    def update_thb_labels_page4(self):
        if not hasattr(config, "SATS_PER_THB") or config.SATS_PER_THB is None:
            print("[WARN] SATS_PER_THB not set! Skipping label update.")
            return
        for value, (_, _, label) in self.thb_buttons.items():
            if DEPOSIT_FEE_USE_PERCENT == "False":
                Real_THB_After_Deduted = max(0, int(value) - int(DEPOSIT_FEE)) # If you want to change fee to be percent, you just have a look here
            else:
                value -= int(BASE_FEE)
                Real_THB_After_Deduted = max(0, int(value) - (int(DEPOSIT_FEE) * int(value)) // 100) # If you want to change fee to be percent, you just have a look here

            sats = Real_THB_After_Deduted * int(config.SATS_PER_THB)
            label.setText(f"{sats:,} Sat")

    # This function is for page 27
    def update_thb_labels_page27(self):
        if not hasattr(config, "SATS_PER_THB") or config.SATS_PER_THB is None:
            print("[WARN] SATS_PER_THB not set! Skipping label update.")
            return
        for button, (amount, label) in self.amount_buttons.items():
            if DEPOSIT_FEE_USE_PERCENT == "False":
                Real_THB_After_Deduted = max(0, int(amount) - int(DEPOSIT_FEE))
            else:
                amount -= int(BASE_FEE)
                Real_THB_After_Deduted = max(0, int(amount) - (int(DEPOSIT_FEE) * int(amount)) // 100)
            sats = Real_THB_After_Deduted * int(config.SATS_PER_THB)
            label.setText(f"{sats:,} Sat")

    def goto_page(self, n):
        self.current_page = n
        self.reset_idle_timer() # This line is for take back to home page when no activity
        print(f"goto_page called with n={n}")
        self.stackedWidget.setCurrentIndex(n)
        if hasattr(self, 'btc_price_fetcher'):
            print("btc_price_fetcher exists")
            # This is check for main page, if we are not in main we will stop read BTC price
            if n == 0:
                # Always reset key state variables
                self.selected_thb = None
                self.selected_amount = None
                self.last_scan = {"type": None, "raw": None, "parsed": None, "sat": None, "payment_type": None, "timestamp": None, "THB": None}
                print("Resuming BTC fetcher")
                self.btc_price_fetcher.resume()
                self.LNAddresslineEdit_page2.clear()
                self.clear_withdraw_values_page28()
                self.reset_counts()

                # Clean up worker
                self.cleanup_ws_worker()
                self.stop_sms_worker()

            else:
                print("Pausing BTC fetcher")
                self.btc_price_fetcher.pause()

            if n == 2 or n == 9:
                self.progressBar_page2.hide()
                self.start_qr_code_reader() # This line is very important, its trigger everything
            else:
                self.stop_qr_code_reader()
                self.LNAddresslineEdit_page2.setText("") # Make it clear when come to page 2

            if n == 3:
                self.check_balance() # Check maximum balance which is Smart Coin can transfer
                #self.midnight_warn_page3.hide()

            if n == 4:
                # show cancel and select medthod button for page 12 to page 23
                for page in range(12, 24):  # 12 to 23 inclusive
                    cancel_btn = getattr(self, f'cancelButton_page{page}')
                    method_btn = getattr(self, f'methodButton_page{page}')
                    cancel_btn.show()
                    method_btn.show()

            if n == 5:
                self.progressBar_page5.hide()
                #self.gpio.set_pin(27, 1)  # Set pin 17 HIGH (on)
                self.gpio.set_led(True)  # Turn LED on
            else:
                #self.gpio.set_pin(27, 0)  # Set pin 17 HIGH (off)
                self.gpio.set_led(False)  # Turn LED off

            if n == 6:
				self.gpio.enable_coin_acceptor(True)   # Enable coin acceptor
                self.reset_counts()
            else:
                self.gpio.enable_coin_acceptor(False)   # Disable coin acceptor

            if n == 27:
                self.clear_withdraw_values_page28()

            if n == 28:
                self.clear_withdraw_values_page28()
            
        else:
            print("btc_price_fetcher does NOT exist!")

    def cleanup_ws_worker(self):
        if hasattr(self, "ws_worker") and self.ws_worker is not None:
            try:
                self.ws_worker.stop()
            except Exception as e:
                print("Error stopping websocket worker:", e)
            finally:
                self.ws_worker = None

    # This function is for page 9
    def check_nfc_balance(self, nfc_uid):
        self.nfc_balance_worker = NFCBalanceWorker(nfc_uid = nfc_uid)
        self.nfc_balance_worker.balance_ready.connect(self.on_nfc_balance_ready)
        self.nfc_balance_worker.error.connect(self.on_nfc_balance_error)
        self.nfc_balance_worker.start()

    # This function is for page 9
    def on_nfc_balance_ready(self, balance):
        print(f"NFC wallet balance: {balance} sats")
        self.line4Header_page9.show()
        self.line5Header_page9.show()
        self.satLabel_page9.show()
        self.thbLabel_Page9.show()
        self.satLabel_page9.setText(f"{balance:,} sat")
        NFC_THB_Value = int(balance) / int(config.SATS_PER_THB)
        self.thbLabel_Page9.setText(f"{int(NFC_THB_Value):,} บาท")
        self.progressBar_page9.hide()

    # This function is for page 9
    def on_nfc_balance_error(self, msg):
        print(f"NFC balance error: {msg}")
        self.nfclineEdit_page9.setText("NFC not registered with Smart Coin")
        self.clear_label_page9()

    # This function is for page 5
    def pay_invoice_gui(self, bolt11_invoice):
        self.pay_worker = LNbitsPayWorker(bolt11_invoice = bolt11_invoice)
        self.pay_worker.payment_success.connect(self.on_pay_success)
        self.pay_worker.payment_error.connect(self.on_pay_error)
        self.pay_worker.start()

    # This function is for page 5 and this is the last step to pay LN to customer wallet [Coin, Notes, Transfer]
    def on_pay_success(self, payment_hash):
        self.step4Header_page5.setText(f"Payment hash: {payment_hash}")
        print(f"Payment hash: {payment_hash}")
        self.step5Header_page5.setText("Payment sent successfully!")
        print("Payment sent successfully!")
        if TELEGRAM_ENABLE == "True":
            telegram_worker(f"{MACHINE_ID} Transfer {self.last_scan['THB']:,} บาท เป็นจำนวน {self.last_scan['sat']:,} sat")
        QTimer.singleShot(1000, self.goto_success_page7)  # 1 seconds (1000 ms)
        play_sound_by_index(6)

    # This function is for page 5
    def goto_success_page7(self):
        self.goto_page(7)
        # Start timer for 5-second delay to page 0
        QTimer.singleShot(5000, lambda: self.goto_page(0))  # 5 seconds (5000 ms)

    # This function is for page 5
    def goto_fail_page25(self):
        self.ErrorMessage_page25.setText(LN_TRANFER_FAIL)
        self.goto_page(25)

    # This function is for page 5
    def on_pay_error(self, error_msg):
        self.step4Header_page5.setText(f"Failed to send payment.")
        self.step5Header_page5.setText(f"Error: {error_msg}")
        QTimer.singleShot(3000, self.goto_fail_page25)  # 3 seconds (3000 ms)

    # This function is for page 5
    def request_invoice(self, lightning_address, amount_sats):
        self.invoice_worker = CustomerInvoiceWorker(lightning_address, amount_sats)
        self.invoice_worker.invoice_ready.connect(self.handle_invoice_ready)
        self.invoice_worker.error.connect(self.handle_invoice_error)
        self.invoice_worker.start()

    # This function is for page 5
    def handle_invoice_ready(self, pr):
        print("[GUI] Got invoice:", pr)
        self.invoice = pr
        self.invoice_cut = split_text_in_half(self.invoice)
        #print(f"invoice cut: {self.invoice_cut}")
        self.step3Header_page5.setText(f"Invoice: {self.invoice_cut}")
        self.pay_invoice_gui(self.invoice) # Call worker to pay invoice

    # This function is for page 5
    def handle_invoice_error(self, msg):
        print("[GUI] LNURL invoice error:", msg)
        self.step3Header_page5.setText(f"Error: {msg}")
        QTimer.singleShot(3000, self.goto_fail_page25)  # 3 seconds (3000 ms)

    # This function is for page 5 and will go to page 24 if customer put under fee rate
    def handle_LN_process_transfer_page5(self):
        print("welcome to handle_LN_process_transfer_page5")
        if self.last_scan['payment_type'] == "Coin_And_Note":
            print("This is Coin_And_Note")
            total = (
                sum(k * v for k, v in self.coin_counts.items()) +
                sum(k * v for k, v in self.note_counts.items())
            )
            self.last_scan['THB'] = total

            if DEPOSIT_FEE_USE_PERCENT == "False":
                if self.last_scan['THB'] <= int(DEPOSIT_FEE):
                    self.goto_page(24) # Not enough, go to warning/error page
                    return None
            else:
                print(f"total = {self.last_scan['THB']}")
                Fee_Check = ((int(DEPOSIT_FEE) * self.last_scan['THB']) // 100)
                print(f"Fee_Check = {Fee_Check}")
                if self.last_scan['sat'] <= 0:
                    print("Come to 4")
                    self.goto_page(24) # Not enough, go to warning/error page
                    return None

        elif self.last_scan['payment_type'] == "Bank_Transfer":
            print("This is Bank_Transfer")
        
        self.goto_page(5) # Process as normal
        print(f"Summary_sat = {self.last_scan['sat']}")
        self.step3Header_page5.setText(f"")
        self.step4Header_page5.setText(f"")
        self.step5Header_page5.setText(f"")

        if self.last_scan["type"] == "NFC":
            print("This is an NFC wallet, transfer to NFC logic.")
            self.progressBar_page5.show()
            self.start_progress_animation(self.progressBar_page5, 30)
            play_sound_by_index(3)

            self.step1Header_page5.setText(f"ระบบกำลังทำการโอน bitcoin เป็นจำนวน {self.last_scan['sat']:,} ซาโตชิ")
            self.step2Header_page5.setText(f"NFC refill to : {self.last_scan['parsed']}")
            Sat_Amount = int(self.last_scan['sat']) * MILLISAT # Convert sat to millsat because LNbits is talk in millisat
            self.start_NFC_refill(self.last_scan['parsed'], self.last_scan['sat'])
            print(f"NFC refill to : {self.last_scan['parsed']}")
            
        elif self.last_scan["type"] == "LNURL" or self.last_scan["type"] == "LNADDRESS":
            print("This is an LNURL or LN Address, do LNURL or LN Address logic.")
            self.progressBar_page5.show()
            self.start_progress_animation(self.progressBar_page5, 100)
            play_sound_by_index(2)

            self.step1Header_page5.setText(f"ระบบกำลังทำการโอน bitcoin เป็นจำนวน {self.last_scan['sat']:,} ซาโตชิ")
            self.step2Header_page5.setText(f"Send to : {self.last_scan['parsed']}")
            Sat_Amount = int(self.last_scan['sat']) * MILLISAT # Convert sat to millsat because LNbits is talk in millisat
            self.request_invoice(self.last_scan["parsed"], self.last_scan['sat']) # Request invoice to customer's wallet
            print(f"Transfer sat to : {self.last_scan['parsed']}")

        else:
            print("Unknown or error type.")

    # This function is for NFC page 5
    def start_NFC_refill(self, nfc_uid, sat_amount):
        self.refill_worker = RefillCardWorker(
            nfc_uid=nfc_uid,
            sat_amount=sat_amount,
        )
        self.refill_worker.refill_success.connect(self.on_refill_success)
        self.refill_worker.error.connect(self.on_refill_error)
        self.refill_worker.start()

    # This function is for page 5 and this is the last step to pay LN to customer wallet [NFC]
    def on_refill_success(self, invoice, payment_hash, pay_json):
        invoice_cut = split_text_in_half(invoice)
        self.step3Header_page5.setText(f"Invoice: {invoice_cut}")
        self.step4Header_page5.setText(f"Payment hash: {payment_hash}")
        self.step5Header_page5.setText("Payment sent successfully!")
        print(f"Payment hash: {payment_hash}")
        print("Payment sent successfully!")
        if TELEGRAM_ENABLE == "True":
            telegram_worker(f"{MACHINE_ID} Transfer {self.last_scan['THB']:,} บาท เป็นจำนวน {self.last_scan['sat']:,} sat")
        QTimer.singleShot(3000, self.goto_success_page7)  # 3 seconds (3000 ms)
        play_sound_by_index(6)

    # This function is for NFC page 5
    def on_refill_error(self, message):
        self.step3Header_page5.setText("Refill error")
        self.step4Header_page5.setText(message)
        self.step5Header_page5.setText("")
        QTimer.singleShot(3000, self.goto_fail_page25)  # 3 seconds (3000 ms)

    # This function is for page 3, 4, 6
    def check_balance(self):
        self.balance_worker = LNbitsBalanceWorker()
        self.balance_worker.balance_ready.connect(self.on_balance_ready)
        self.balance_worker.error.connect(self.on_balance_error)
        self.balance_worker.start()

    # This function is for page 3, 4, 6
    def on_balance_ready(self, balance):
        balance = abs(balance)
        print(f"[Debug] balance = {balance}")
        sats_per_thb = max(1, int(config.SATS_PER_THB))
        print(f"[Debug] sats_per_thb = {sats_per_thb}")
        max_sat = int(balance / 1000)
        max_THB = int(max_sat / sats_per_thb)

        print(f"[GUI] LNbits balance: {max_sat:,} sat")
        print(f"[GUI] LNbits balance: {max_THB:,} THB")
        self.amount_warn_page3.setText(f"ทำรายการได้ไม่เกิน {max_THB:,} บาท")
        self.label_limit_page6.setText(f"Limit {max_THB:,} บาท")

    # This function is for page 3, 4, 6
    def on_balance_error(self, msg):
        print(f"[GUI] LNbits balance error: {msg}")

    # This function is for page 2
    def start_qr_code_reader(self):
        global QR_CODE_READER_PORT
        self.qr_reader = QRCodeReader(QR_CODE_READER_PORT)
        self.qr_reader.code_scanned.connect(self.handle_qr_scanned)
        self.qr_reader.start()

    # This function is use when leave page 2
    def stop_qr_code_reader(self):
        print(f"[QR] Stop QR code reader")
        if hasattr(self, "qr_reader") and self.qr_reader is not None:
            self.qr_reader.stop()
            self.qr_reader = None  # Optional: let garbage collection clean up

    # This function is for page 6
    def poll_coin_queue(self):
        while not self.coin_result_queue.empty():
            msg, value = self.coin_result_queue.get_nowait()
            if msg == "coin":
                self.on_coin_inserted(value)
            elif msg == "error":
                self.on_coin_error(value)
            elif msg == "info":
                print(value)

    def enable_coin(self):
        global COIN_ENABLE
        print("Coin enabled")
        COIN_ENABLE = True
        self.coin_command_queue.put("enable")

    def disable_coin(self):
        global COIN_ENABLE
        print("Coin disabled")
        COIN_ENABLE = False
        #self.coin_command_queue.put("disable")

    # This function is for page 6
    def on_coin_inserted(self, value):
        global COIN_ENABLE
        print(f"[DEBUG] on_coin_inserted called, COIN_ENABLE = {COIN_ENABLE}")
        if COIN_ENABLE == False:
            print("[DEBUG] Coin event ignored because acceptor is disabled.")
            return
        play_sound_by_index(11)
        self.manager.refresh_json_data()
        print(f"[GUI] Got {value} baht from coin acceptor!")
        self.last_scan['payment_type'] = "Coin_And_Note" # This line is identify payment type which is coin and note or bank transfer
        if value in self.coin_counts:
            self.coin_counts[value] += 1
            self.update_page6_labels()

        if value == 1:
            coin_temp = self.manager.get_current_coin_1()
            coin_temp += self.coin_counts[1]
            self.manager.set_current_coin_1(coin_temp)
        elif value == 2:
            coin_temp = self.manager.get_current_coin_2()
            coin_temp += self.coin_counts[2]
            self.manager.set_current_coin_2(coin_temp)
        elif value == 5:
            coin_temp = self.manager.get_current_coin_5()
            coin_temp += self.coin_counts[5]
            self.manager.set_current_coin_5(coin_temp)
        elif value == 10:
            coin_temp = self.manager.get_current_coin_10()
            coin_temp += self.coin_counts[10]
            self.manager.set_current_coin_10(coin_temp)

        self.update_total_money_summary()

    # This function is for page 6
    def on_coin_error(self, error_msg):
        print(f"[GUI] Coin acceptor error: {error_msg}")
        # Optionally show an error dialog

    # This function is for page 6
    def poll_bill_queue(self):
        while not self.bill_result_queue.empty():
            msg, value = self.bill_result_queue.get_nowait()
            if msg == "note":
                self.on_note_inserted(value)
            elif msg == "error":
                self.on_bill_error(value)
            elif msg == "info":
                print(value)

    def enable_bill(self):
        self.bill_command_queue.put("enable")

    def disable_bill(self):
        self.bill_command_queue.put("disable")

    # This function is for page 6
    def on_note_inserted(self, value):
        play_sound_by_index(1)
        self.manager.refresh_json_data()
        self.last_scan['payment_type'] = "Coin_And_Note" # This line is identify payment type which is coin and note or bank transfer
        print(f"[GUI] Got {value} baht from bill acceptor!")
        if value in self.note_counts:
            self.note_counts[value] += 1
            self.update_page6_labels()

        if value == 20:
            note_temp = self.manager.get_current_note_20()
            note_temp += self.note_counts[20]
            self.manager.set_current_note_20(note_temp)
        elif value == 50:
            note_temp = self.manager.get_current_note_50()
            note_temp += self.note_counts[50]
            self.manager.set_current_note_50(note_temp)
        elif value == 100:
            note_temp = self.manager.get_current_note_100()
            note_temp += self.note_counts[100]
            self.manager.set_current_note_100(note_temp)
        elif value == 500:
            note_temp = self.manager.get_current_note_500()
            note_temp += self.note_counts[500]
            self.manager.set_current_note_500(note_temp)
        elif value == 1000:
            note_temp = self.manager.get_current_note_1000()
            note_temp += self.note_counts[1000]
            self.manager.set_current_note_1000(note_temp)
        else:
            print(f"Unknown note denomination: {value}")

        self.update_total_money_summary()

    # This function is for page 6
    def on_bill_error(self, error_msg):
        print(f"[GUI] Bill acceptor error: {error_msg}")
        # Optionally show an error dialog

    # This function is for page 6 and will update total value when customer insert coin and bill
    def update_page6_labels(self):
        # Update coin labels
        self.inputCoin1_page6.setText(str(self.coin_counts[1]))
        self.inputCoin2_page6.setText(str(self.coin_counts[2]))
        self.inputCoin5_page6.setText(str(self.coin_counts[5]))
        self.inputCoin10_page6.setText(str(self.coin_counts[10]))
        # Update note labels
        self.inputNote20_page6.setText(str(self.note_counts[20]))
        self.inputNote50_page6.setText(str(self.note_counts[50]))
        self.inputNote100_page6.setText(str(self.note_counts[100]))
        self.inputNote500_page6.setText(str(self.note_counts[500]))
        self.inputNote1000_page6.setText(str(self.note_counts[1000]))
        # Update sum
        total = (
            sum(k * v for k, v in self.coin_counts.items()) +
            sum(k * v for k, v in self.note_counts.items())
        )
        self.inputSumNoteCoin_page6.setText(f"{total:,} บาท")

        if DEPOSIT_FEE_USE_PERCENT == "False":
            Real_THB_After_Deduted = max(0, int(total) - int(DEPOSIT_FEE)) # If you want to change fee to be percent, you just have a look here
        else:
            Real_THB_After_Deduted = max(0, int(total) - int(BASE_FEE) - (int(DEPOSIT_FEE) * int(total) // 100)) # If you want to change fee to be percent, you just have a look here

        print(f"Cash and coin in total = {total}")
        #print(f"DEPOSIT_FEE = {DEPOSIT_FEE}")
        print(f"Real_THB_After_Deduted = {Real_THB_After_Deduted}")
        self.last_scan["sat"] = Real_THB_After_Deduted * int(config.SATS_PER_THB) 
        self.inputSumSat_page6.setText(f"{self.last_scan['sat']:,} Sat") # This line is contain variable to show sat summary
        self.backButton_page6.hide()
        self.okButton_page6.show()

    # This function is for page 6
    def reset_counts(self):
        for k in self.coin_counts:
            self.coin_counts[k] = 0
        for k in self.note_counts:
            self.note_counts[k] = 0
        self.update_page6_labels()

    # This function is for page 28
    def clear_withdraw_values_page28(self):
        self.WithdrawBanknote_100_THB = 0
        self.WithdrawBanknote_500_THB = 0
        self.WithdrawBanknote_1000_THB = 0
        self.inputNote100_page28.setText("0")
        self.inputNote500_page28.setText("0")
        self.inputNote1000_page28.setText("0")
        self.inputSumNote_page28.setText("0 บาท")
        self.maxNote100_page28.hide()
        self.maxNote500_page28.hide()
        self.maxNote1000_page28.hide()
        self.okButton_page28.hide()

    # This function is for page 28
    def adjust_banknote(self, note_type, change):
        max_reached = False
        if note_type == '100':
            new_value = self.WithdrawBanknote_100_THB + change
            if 0 <= new_value <= self.LIMITBANKNOTE100:
                self.WithdrawBanknote_100_THB = new_value
            if new_value >= self.LIMITBANKNOTE100:
                max_reached = True
            self.maxNote100_page28.setVisible(max_reached)
        elif note_type == '500':
            new_value = self.WithdrawBanknote_500_THB + change
            if 0 <= new_value <= self.LIMITBANKNOTE500:
                self.WithdrawBanknote_500_THB = new_value
            if new_value >= self.LIMITBANKNOTE500:
                max_reached = True
            self.maxNote500_page28.setVisible(max_reached)
        elif note_type == '1000':
            new_value = self.WithdrawBanknote_1000_THB + change
            if 0 <= new_value <= self.LIMITBANKNOTE1000:
                self.WithdrawBanknote_1000_THB = new_value
            if new_value >= self.LIMITBANKNOTE1000:
                max_reached = True
            self.maxNote1000_page28.setVisible(max_reached)
        self.update_banknote_display()

        # ✅ Set total THB amount at the end
        thb_amount = (
            self.WithdrawBanknote_100_THB * 100 +
            self.WithdrawBanknote_500_THB * 500 +
            self.WithdrawBanknote_1000_THB * 1000
        )
        self.last_scan['THB'] = thb_amount

    # This function is for page 28
    def update_banknote_display(self):
        self.inputNote100_page28.setText(str(self.WithdrawBanknote_100_THB))
        self.inputNote500_page28.setText(str(self.WithdrawBanknote_500_THB))
        self.inputNote1000_page28.setText(str(self.WithdrawBanknote_1000_THB))
        # --- Show sum ---
        total = (self.WithdrawBanknote_100_THB * 100 +
                 self.WithdrawBanknote_500_THB * 500 +
                 self.WithdrawBanknote_1000_THB * 1000)
        self.inputSumNote_page28.setText(f"{total:,} บาท")
        print(f"Banknotes in Total: {total}")

        self.selected_amount = total

        if total == 0:
            self.okButton_page28.hide()
        else:
            self.okButton_page28.show()

    # This function is for page 27 and this function use for calculate how many banknotes need to dispense
    def handle_amount_selected(self, value):
        self.selected_amount = value
        note_stock = {
            100: self.manager.get_current_banknote_100(),
            500: self.manager.get_current_banknote_500(),
            1000: self.manager.get_current_banknote_1000()
        }
        breakdown = get_banknote_breakdown(value, note_stock)
        if breakdown is None:
            print("Cannot dispense this amount with current stock!")
            # Handle error: show a message or disable button
            return
        # Otherwise, use the breakdown
        self.WithdrawBanknote_1000_THB = breakdown[1000]
        self.WithdrawBanknote_500_THB = breakdown[500]
        self.WithdrawBanknote_100_THB = breakdown[100]

        print(f"Selected amount: {value}")
        print(f"100 THB banknote: {self.WithdrawBanknote_100_THB}")
        print(f"500 THB banknote: {self.WithdrawBanknote_500_THB}")
        print(f"1000 THB banknote: {self.WithdrawBanknote_1000_THB}")
        self.last_scan['THB'] = self.selected_amount
        self.generate_QR_page_29()

    # This function is for page 29
    def generate_QR_page_29(self):
        # global WITHDRAW_FEE
        # Show loading bar
        self.goto_page(26)

        if WITHDRAW_FEE_USE_PERCENT == "False":
            invoice_amount = int(config.SATS_PER_THB) * (int(self.selected_amount) + int(WITHDRAW_FEE))
        else:
            invoice_amount = int(config.SATS_PER_THB) * (int(self.selected_amount) + (int(WITHDRAW_FEE) * int(self.selected_amount) // 100))

        self.satHeader_page29.setText(f"ต้องโอนมาเป็นจำนวน {invoice_amount:,} sat")
        self.last_scan['sat'] = invoice_amount
        self.worker = LNbitsInvoiceWorker(amount_sats=invoice_amount, memo=WITHDRAW_MEMO)
        self.worker.invoice_ready.connect(self.on_invoice_ready)
        self.worker.error.connect(self.on_invoice_error)
        self.worker.start()

        self.start_progress_animation(self.progressBar_page26, 20)
        play_sound_by_index(13)

    # This function is for page 29
    def on_invoice_ready(self, invoice):
        data_to_encode = str(invoice)
        qr_pixmap = generate_qr_pixmap(data_to_encode, size=320)
        self.label_qrcode_page29.setPixmap(qr_pixmap)
        self.goto_page(29)

        # Start WebSocket worker to listen for payment
        global WEB_SOCKET_URL
        self.cleanup_ws_worker()  # Stop old worker (if any)
        self.ws_worker = LNbitsWebSocketWorker(WEB_SOCKET_URL)
        self.ws_worker.payment_received.connect(self.on_payment_received)
        self.ws_worker.start()

    # This function is for page 29
    def stop_web_socket_worker(self, target_page, after_cleanup=None):
        self.goto_page(target_page)
        QTimer.singleShot(100, self.cleanup_ws_worker)
        if after_cleanup:
            QTimer.singleShot(200, after_cleanup)  # Do slow stuff even later

    # This function is for page 29
    def cleanup_ws_worker(self):
        if hasattr(self, "ws_worker") and self.ws_worker is not None:
            try:
                self.ws_worker.stop()
                self.ws_worker.wait()  # Wait for thread to finish
            except Exception as e:
                print("Error stopping websocket worker:", e)
            self.ws_worker = None

    # This function is for page 29 for dispense bank note here so this is the last state for withdrawal
    def on_payment_received(self, data):
        self.manager.refresh_json_data()
        print("Payment received!", data)
        amount = data.get('payment', {}).get('amount', None)
        sat_transfer_amount = int(amount) // MILLISAT
        print("Amount received:", sat_transfer_amount)
        if int(sat_transfer_amount) == int(self.last_scan['sat']):
            self.goto_page(30)

            # 100 THB Note
            if self.WithdrawBanknote_100_THB > 0:
                dispense_temp = self.manager.get_current_banknote_100()
                dispense_temp -= int(self.WithdrawBanknote_100_THB)
                print(f"dispense_temp : {dispense_temp}")
                self.manager.set_current_banknote_100(dispense_temp)
                sum_dispense_temp = self.manager.get_total_withdraw_amount()
                sum_dispense_temp += 100 * int(self.WithdrawBanknote_100_THB)
                print(f"sum_dispense_temp : {sum_dispense_temp}")
                self.manager.set_total_withdraw_amount(sum_dispense_temp)

                worker_100 = DispenserWorker('Dispenser100', NOTE_DISPENSER_100_PORT, 100)
                worker_100.start()
                worker_100.dispense(self.WithdrawBanknote_100_THB)
                worker_100.stop()

            # 500 THB Note
            if self.WithdrawBanknote_500_THB > 0:
                dispense_temp = self.manager.get_current_banknote_500()
                dispense_temp -= int(self.WithdrawBanknote_500_THB)
                print(f"dispense_temp : {dispense_temp}")
                self.manager.set_current_banknote_500(dispense_temp)
                sum_dispense_temp = self.manager.get_total_withdraw_amount()
                sum_dispense_temp += 500 * int(self.WithdrawBanknote_500_THB)
                print(f"sum_dispense_temp : {sum_dispense_temp}")
                self.manager.set_total_withdraw_amount(sum_dispense_temp)

                worker_500 = DispenserWorker('Dispenser500', NOTE_DISPENSER_500_PORT, 500)
                worker_500.start()
                worker_500.dispense(self.WithdrawBanknote_500_THB)
                worker_500.stop()

            # 1000 THB Note
            if self.WithdrawBanknote_1000_THB > 0:
                dispense_temp = self.manager.get_current_banknote_1000()
                dispense_temp -= int(self.WithdrawBanknote_1000_THB)
                print(f"dispense_temp : {dispense_temp}")
                self.manager.set_current_banknote_1000(dispense_temp)
                sum_dispense_temp = self.manager.get_total_withdraw_amount()
                sum_dispense_temp += 1000 * int(self.WithdrawBanknote_1000_THB)
                print(f"sum_dispense_temp : {sum_dispense_temp}")
                self.manager.set_total_withdraw_amount(sum_dispense_temp)

                worker_1000 = DispenserWorker('Dispenser1000', NOTE_DISPENSER_1000_PORT, 1000)
                worker_1000.start()
                worker_1000.dispense(self.WithdrawBanknote_1000_THB)
                worker_1000.stop()

            self.cleanup_ws_worker() #Clean Web Socket worker
            self.clear_withdraw_values_page28()

            # Start a single-shot timer for 5 seconds (5000 ms)
            self.page_reset_timer = QTimer()
            self.page_reset_timer.setSingleShot(True)
            self.page_reset_timer.timeout.connect(lambda: self.goto_page(0))
            self.page_reset_timer.start(5000)
            play_sound_by_index(6)

            thb_amount = self.last_scan.get('THB')
            if thb_amount is None:
                thb_amount = 0

            if TELEGRAM_ENABLE == "True":
                try:
                    telegram_worker(f"{MACHINE_ID} Withdraw {thb_amount:,} บาท แล้วได้รับ Bitcoin จำนวน {sat_transfer_amount:,} sat")
                except Exception as e:
                    print("Telegram error:", e)

        else:
            self.goto_page(25)
            self.ErrorMessage_page25.setText(f"ยอดที่โอนมามีเพียงแค่ : {sat_transfer_amount:,} sat")

    # This function is for page 29
    def on_invoice_error(self, error_msg):
        QMessageBox.critical(self, "Error", error_msg)

    # This function is for page 2
    def show_keyboard(self, event):
        if hasattr(self, 'keyboard') and self.keyboard is not None and self.keyboard.isVisible():
            return
        self.keyboard = VirtualKeyboard(self.LNAddresslineEdit_page2, parent=self)
        self.keyboard.main_window = self
        self.keyboard.destroyed.connect(lambda: setattr(self, 'keyboard', None))
        self.keyboard.show()
        self.helpButton_page2.hide()
        self.backButton_page2.hide()

    # This function is for page 0 and this is a periodic called
    def update_btc_price(self, price):
        print("Bitcoin price updating...")
        self.BTC_Price_label_page0.setText(f"{config.BTC_THB:,.0f} บาท")
        self.SatPrice_label_page0.setText(f"{config.SATS_PER_THB:,.0f} Sat")

        # Do configuration
        withdraw_enable = self.manager.get_withdraw_enable()
        bank_transfer_enable = self.manager.get_bank_transfer_enable()
        print(f"withdraw_enable status: {withdraw_enable}")
        print(f"bank_transfer_enable status: {bank_transfer_enable}")
        if withdraw_enable == "No":
            self.withdrawButton_page0.hide()
            self.depositButton_page0.move(280, 310)
        if bank_transfer_enable == "No":
            self.transferButton_page3.hide()
            self.midnight_warn_page3.hide()
            self.coinNoteButton_page3.move(240, 230)

        self.start_delete_sms() # Clear SMS in the SIM

    # This function is for page 2
    def handle_qr_scanned(self, text):
        if self.current_page == 2:
            try:
                scan_type = "UNKNOWN"
                parsed = text
                parts = re.split(r'(?:\r\n|\r|\n|<CR>)', text)
                found = False
                uids = None  # Make sure this is always set, even if not found

                for part in parts:
                    part = part.strip()
                    if not part:
                        continue

                    print(f"part = {part}")

                    # LNURL block
                    if part.lower().startswith("lightning:lnurl") or part.lower().startswith("lnurl"):
                        only_one_lnurl = extract_only_one_lnurl(part)
                        print(f"DEBUG: only_one_lnurl = {only_one_lnurl}")
                        if only_one_lnurl:
                            lnurl = extract_lnurl_from_text(only_one_lnurl)
                            print(f"DEBUG: lnurl = {lnurl}")
                            if lnurl:
                                try:
                                    url = parse_lnurl(lnurl)
                                    print(f"DEBUG: url = {url}")
                                except Exception as err:
                                    print(f"DEBUG: parse_lnurl failed: {err}")
                                    continue
                                scan_type = "LNURL"
                                parsed = url
                                self.LNAddresslineEdit_page2.setText(url)
                                self.handle_check_lnurl(url)
                                self.progressBar_page2.show()
                                self.start_progress_animation(self.progressBar_page2, 10)
                                play_sound_by_index(14)
                                found = True
                                break  # IMPORTANT: Exit loop after handling LNURL
                        
                    # Lightning Address block
                    elif "@" in part and "." in part:
                        scan_type = "LNADDRESS"
                        if part.count("@") != 1:
                            continue
                        parsed = strip_http_prefix(part)
                        self.LNAddresslineEdit_page2.setText(parsed)
                        self.handle_check_lnurl(parsed)
                        self.progressBar_page2.show()
                        self.start_progress_animation(self.progressBar_page2, 10)
                        play_sound_by_index(14)
                        found = True
                        break

                    # NFC block
                    elif NFC_MIN_LENGTH < len(part) < NFC_MAX_LENGTH:
                        uids = extract_uid(part)
                        print(f"DEBUG: uids = {uids}")
                        scan_type = "NFC"
                        if uids is not None and NFCReader.NFC_Check_Register(uids):
                            parsed = uids
                            self.LNAddresslineEdit_page2.setText(uids)
                            play_sound_by_index(14)
                            if SOFTWARE_VERSION == "Smart Coin v1.2":
                                self.goto_page(6)
                            else:
                                self.goto_page(3)
                            found = True
                            break
                        else:
                            continue

                if not found:
                    play_sound_by_index(9)
                    self.LNAddresslineEdit_page2.setText("Invalid QR, Please try again")

                # Save scan context
                self.last_scan = {
                    "type": scan_type,
                    "raw": text,
                    "parsed": parsed,
                    "timestamp": time.time()
                }
                print(f"Last scan info: {self.last_scan}")

            except Exception as e:
                print(f"LNURL parse error: {e}")
                play_sound_by_index(9)
                self.LNAddresslineEdit_page2.setText("Invalid QR, Please try again")
                self.last_scan = {
                    "type": "ERROR",
                    "raw": text,
                    "parsed": None,
                    "timestamp": time.time()
                }

        elif self.current_page == 9:
            uids = extract_uid(text)
            print(uids)
            if uids is None:
                play_sound_by_index(9)
                self.clear_label_page9()
                self.nfclineEdit_page9.setText("Invalid NFC UID")
                print("Invalid NFC UID")
                scan_type = "NFC_UNREGISTERED"
            else:
                if NFCReader.NFC_Check_Register(uids):
                    self.progressBar_page9.show()
                    self.start_progress_animation(self.progressBar_page9, 10)
                    play_sound_by_index(1)
                    self.nfclineEdit_page9.setText(f"NFC UID : {uids}")
                    self.check_nfc_balance(uids)
                    print("Check balance NFC")
                    scan_type = "NFC"
                else:
                    play_sound_by_index(9)
                    self.clear_label_page9()
                    self.nfclineEdit_page9.setText("This card is not registered")
                    print("This card is not registered")
                    scan_type = "NFC_UNREGISTERED"
            
        else:
            print("Page out of index")

    # This function is for page 2
    def handle_check_lnurl(self, LNURL):
        # Start worker
        print("Start worker for parse LNURL")
        self.lnurl_worker = LNURLCheckerWorker(LNURL)
        self.lnurl_worker.finished.connect(self.handle_check_linghtning_address_on_internet)
        self.lnurl_worker.start()

    # This function is for page 2
    def handle_check_linghtning_address_on_internet(self, result):
        #print("This is handle_check_linghtning_address_on_internet on website")
        global NEED_TO_CLEAR_LINE_EDIT
        if result["ok"]:
            data = result["data"]
            print(data)
            if SOFTWARE_VERSION == "Smart Coin v1.2":
                self.goto_page(6)  # Go to page coin and note
            else:
                self.goto_page(3)  # Go to page 3
            if self.PRESS_OK_PAGE2_FLAG ==True:
                play_sound_by_index(14)
                self.PRESS_OK_PAGE2_FLAG =False
        else:
            print(result)
            # Optionally, show error in UI or go to error page
            self.progressBar_page2.hide()
            self.LNAddresslineEdit_page2.setText("Invalid Lightning Address")
            NEED_TO_CLEAR_LINE_EDIT = True
            play_sound_by_index(9)

    # This function is for page 9
    def clear_label_page9(self):
        self.line4Header_page9.hide()
        self.line5Header_page9.hide()
        self.satLabel_page9.hide()
        self.thbLabel_Page9.hide()
        self.nfclineEdit_page9.setText("")
        self.progressBar_page9.hide()

    # This function is for page 2
    def on_ok_page2(self):
        value = self.LNAddresslineEdit_page2.text()
        global NEED_TO_CLEAR_LINE_EDIT
        # This is for prevent press enter without input LN address
        if not value.strip():
            self.LNAddresslineEdit_page2.setText("Please enter a value before proceeding!")
            NEED_TO_CLEAR_LINE_EDIT = True
            return None
        elif value.count("@") != 1:
            play_sound_by_index(9)
            self.LNAddresslineEdit_page2.setText("Invalid LN address, Please try again")
            NEED_TO_CLEAR_LINE_EDIT = True
            return None

        scan_type = "LNADDRESS"
        parsed = strip_http_prefix(value)
        self.handle_check_lnurl(parsed) # Check LN Address to internet
        self.progressBar_page2.show()
        self.start_progress_animation(self.progressBar_page2, 10)

        # Save scan context
        self.last_scan = {
            "type": scan_type,
            "raw": value,
            "parsed": parsed,
            "timestamp": time.time()
        }
        print(f"Last scan info: {self.last_scan}")
        self.PRESS_OK_PAGE2_FLAG = True

    def start_progress_animation(self, progressbar, interval_ms=10, max_value=100):
        # Unique key per bar, can use id(progressbar) or the object itself
        key = progressbar

        # If already running, stop old timer
        if key in self.progress_states and self.progress_states[key]['timer'].isActive():
            self.progress_states[key]['timer'].stop()

        # Set up state
        state = {
            'value': 0,
            'max': max_value,
            'timer': QTimer()
        }
        progressbar.setValue(0)

        def update():
            if state['value'] < state['max']:
                state['value'] += 1
                progressbar.setValue(state['value'])
            else:
                state['timer'].stop()

        state['timer'].timeout.connect(update)
        state['timer'].start(interval_ms)
        self.progress_states[key] = state

    def update_progress_bar(self):
        if self.progress_value < self.progress_max:
            self.progress_value += 1
            self.progressBar_page26.setValue(self.progress_value)
        else:
            self.progress_timer.stop()  # Stop when done

    # This function is for page 1
    def update_fee_page(self):
        if DEPOSIT_FEE_USE_PERCENT == "False":
            self.FeeHeader_page1.setText(f"เราคิดค่าธรรมเนี่ยมในการเติมเงิน {DEPOSIT_FEE} บาท / ธุรกรรม")
            self.PriceAfterDeduct20_page1.setText(f"เติม 20 บาท คุณจะได้รับ Bitcoin มูลค่า {20 - int(DEPOSIT_FEE)} บาท")
            self.PriceAfterDeduct100_page1.setText(f"เติม 100 บาท คุณจะได้รับ Bitcoin มูลค่า {100 - int(DEPOSIT_FEE)} บาท")
            self.PriceAfterDeduct500_page1.setText(f"เติม 500 บาท คุณจะได้รับ Bitcoin มูลค่า {500 - int(DEPOSIT_FEE)} บาท")
            self.PriceAfterDeduct1000_page1.setText(f"เติม 1,000 บาท คุณจะได้รับ Bitcoin มูลค่า {1000 - int(DEPOSIT_FEE)} บาท")
        else:
            self.FeeHeader_page1.setText(f"เราคิดค่าธรรมเนี่ยมในการเติมเงิน {DEPOSIT_FEE} เปอร์เซ็น / ธุรกรรม (Base = {BASE_FEE} บาท)")
            self.PriceAfterDeduct20_page1.setText(f"เติม 20 บาท คุณจะได้รับ Bitcoin มูลค่า {20 - int(BASE_FEE) - int(DEPOSIT_FEE) * 20 // 100} บาท")
            self.PriceAfterDeduct100_page1.setText(f"เติม 100 บาท คุณจะได้รับ Bitcoin มูลค่า {100 - int(BASE_FEE) - int(DEPOSIT_FEE) * 100 // 100} บาท")
            self.PriceAfterDeduct500_page1.setText(f"เติม 500 บาท คุณจะได้รับ Bitcoin มูลค่า {500 - int(BASE_FEE) - int(DEPOSIT_FEE) * 500 // 100} บาท")
            self.PriceAfterDeduct1000_page1.setText(f"เติม 1,000 บาท คุณจะได้รับ Bitcoin มูลค่า {1000 - int(BASE_FEE) - int(DEPOSIT_FEE) * 1000 // 100} บาท")
            
        #if WITHDRAW_FEE_USE_PERCENT == "False":
        #    self.PriceAfterDeduct500_page1.setText(f"เราคิดค่าธรรมเนียมในการถอน {WITHDRAW_FEE} บาท / ธุรกรรม")
        #    self.PriceAfterDeduct1000_page1.setText(f"ถอน 100 บาท คุณจะต้องจ่าย Bitcoin เป็นจำนวน {100 + int(WITHDRAW_FEE)} บาท")
        #else:
        #    self.PriceAfterDeduct500_page1.setText(f"เราคิดค่าธรรมเนียมในการถอน {WITHDRAW_FEE} เปอร์เซ็น / ธุรกรรม")
        #    self.PriceAfterDeduct1000_page1.setText(f"ถอน 100 บาท คุณจะต้องจ่าย Bitcoin เป็นจำนวน {100 + (int(WITHDRAW_FEE) * 100 // 100)} บาท")

    # This function is for NFC page 28
    def show_total_value(self):
        denominations = [100, 500, 1000]
        self.note_stock = {den: getattr(self, f"LIMITBANKNOTE{den}", 0) for den in denominations}
        total = sum_banknote_value(self.note_stock)
        self.limitSumHeader_page28.setText(f"ถอนได้ไม่เกิน: {total:,} บาท")

    def handle_status_report(self, thread_names):
        print("Currently alive threads:", thread_names)

    def update_total_money_summary(self):
        total_coins = (
            self.manager.get_current_coin_1() * 1 +
            self.manager.get_current_coin_2() * 2 +
            self.manager.get_current_coin_5() * 5 +
            self.manager.get_current_coin_10() * 10
        )
        total_notes = (
            self.manager.get_current_note_20() * 20 +
            self.manager.get_current_note_50() * 50 +
            self.manager.get_current_note_100() * 100 +
            self.manager.get_current_note_500() * 500 +
            self.manager.get_current_note_1000() * 1000
        )
        total_money = total_coins + total_notes

        self.manager.set_total_coins_value(total_coins)
        self.manager.set_total_banknotes_value(total_notes)
        self.manager.set_total_physical_money_value(total_money)

        print(f"[INFO] Updated totals: coins={total_coins}, notes={total_notes}, total={total_money}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            QApplication.quit()
        elif event.key() == Qt.Key_Q:
            QApplication.quit()
        else:
            super().keyPressEvent(event)

    # Don't forget to clean up thread on close
    def closeEvent(self, event):
        GPIO.cleanup()
        self.morning_worker.stop()
        self.evening_worker.stop()
        try:
            self.qr_reader.stop()
        except Exception:
            pass
        self.coin_command_queue.put("exit")
        self.coin_proc.join()
        self.bill_command_queue.put("exit")
        self.bill_proc.join()
        if hasattr(self, "ArduinoSMSAndReadWorker"):
            self.ArduinoSMSAndReadWorker.stop()
        if hasattr(self, "api_worker"):
            self.api_worker.stop()
        if hasattr(self, "flask_thread"):
            self.flask_thread.stop()
        if hasattr(self, 'thread_watchdog'):
            self.thread_watchdog.stop()
            self.thread_watchdog.wait()
        super().closeEvent(event)
            
if __name__ == "__main__":
    app = QApplication(sys.argv)

    load_fonts()

    window = MainWindow()
    window.setWindowTitle(SOFTWARE_VERSION)
    window.setCursor(Qt.BlankCursor)
    window.showFullScreen()

    # Create and start btc price fetcher
    btc_price_fetcher = BTCPriceFetcher(refresh_interval=1800)  # 30 min
    btc_price_fetcher.price_updated.connect(window.update_btc_price)
    window.btc_price_fetcher = btc_price_fetcher
    btc_price_fetcher.start()

    sys.exit(app.exec_())