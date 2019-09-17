import os
import sys
import cv2
import time
import json
import ctypes
import requests
import datetime
import configparser
import gxipy as gx
import numpy as np
from threading import Thread
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from GlobalVar import gloVar, icon_path, uArm_action, uArm_param, logger, robot_other
from uiclass.stream import Stream
from uiclass.timer import Timer
from uiclass.video_label import Video_Label



class Ui_MainWindow(QMainWindow):
    # 视频初始化
    STATUS_INIT = 0
    # 视频播放中
    STATUS_PLAYING = 1
    # 视频暂停
    STATUS_PAUSE = 2
    # 视频播放完毕
    STATUS_STOP = 3

    # 相机状态
    camera_opened = 'OPENED'
    camera_closed = 'CLOSED'

    # 字体 'Microsoft YaHei'
    font = 'Times New Roman'
    # icon文件
    icon_file = icon_path.Icon_file
    # background文件
    background_file = icon_path.background_file

    def setupUi(self):
        # 初始化参数
        self.init_param()
        # 使用自定义定时器
        self.timer_video = Timer()
        self.timer_video.timeSignal.signal[str].connect(self.show_video)
        # 使用pyqt定时器
        # self.timer_video = QTimer(self)
        # self.timer_video.timeout.connect(self.show_video)
        # self.timer_video.start(1)

        self.setObjectName("MainWindow")
        self.setGeometry(0, 0, 1500, 800)
        self.setMinimumSize(QtCore.QSize(1500, 800))
        self.setWindowTitle("Auto Robot")
        self.setWindowIcon(QIcon(Ui_MainWindow.icon_file))

        self.centralwidget = QWidget(self)

        self.centralwidget.setObjectName("centralwidget")
        self.grid = QtWidgets.QGridLayout(self.centralwidget)
        # self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setObjectName('grid')
        ## 定义UI 字体 和 字号大小
        QFontDialog.setFont(self, QFont(Ui_MainWindow.font, 13))
        # 设置UI背景颜色为灰色
        # self.centralwidget.setStyleSheet('background-color:lightgrey')

        # 视频播放框架
        self.video_play_frame()
        # case展示
        self.show_case()
        # 控制台输出框架
        self.output_text()

        # 视频进度条
        self.slider_thread = Timer(frequent=4)
        self.slider_thread.timeSignal.signal[str].connect(self.slider_refresh)
        self.slider_thread.start()

        self.setCentralWidget(self.centralwidget)
        # 菜单栏
        self.menubar = QtWidgets.QMenuBar(self)
        self.menubar.setObjectName("menubar")
        self.setMenuBar(self.menubar)
        # 状态栏 & 状态栏显示
        self.statusbar = QtWidgets.QStatusBar(self)
        self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage('ready')
        # 工具栏
        self.ui_toolbar = self.addToolBar('ui_toolbar')
        self.robot_operate_toolbar = self.addToolBar('operate_toolbar')
        # 网上百度到的说明:其作用是如其名称一样，用来将QObject 里的子孙QObject的某些信号按照其objectName连接到相应的槽上
        # 如 button_hello.setObjectName("hello_button")
        QtCore.QMetaObject.connectSlotsByName(self)
        # 接收进程打印的信息
        sys.stdout = Stream(newText=self.update_text)
        sys.stderr = Stream(newText=self.update_text)
        # 菜单栏
        self.menu_bar()
        # 工具栏
        self.tool_bar()


    # 所有参数初始化
    def init_param(self):
        # 保存的case执行完的视频
        self.videos = []
        # 保存的视频中case类型和视频名字
        self.videos_title = []
        # 获取到的视频目录
        self.get_path = None
        self.video_play_flag = False  # False直播/True录播
        self.current_video = 0  # 当前视频所在序列号(第0个视频)
        self.current_frame = 0  # 当前帧数
        self.frame_count = 0  # 总帧数
        # 滑动条标志位(如果有滑动动作标志为True, 否则为False)
        self.slider_flag = False
        # 放置视频标签的尺寸
        self.video_label_size_width = 0
        self.video_label_size_height = 0
        # 视频流&视频尺寸
        self.video_width = 1280
        self.video_height = 720
        # self.video_width = 1600
        # self.video_height = 1000
        # 是否第一次窗口缩放
        self.first_window_zoom_flag = True
        # 是否使用电脑自带摄像头
        self.use_system_camera = True
        self.camera_status = self.camera_closed
        # 初始化播放状态
        self.video_status = self.STATUS_INIT
        # 当前图像帧
        self.image = None
        # 获取截图保存路径
        self.picture_path = self.get_config_value(gloVar.config_file_path, 'param', 'picture_path')


    # 获取config的参数
    def get_config_value(self, file, section, option):
        config = configparser.ConfigParser()
        config.read(file, encoding='utf-8')
        return config.get(section, option)


    # 设置config的参数
    def set_config_value(self, file, section, option, value):
        config = configparser.ConfigParser()
        config.read(file, encoding='utf-8')
        if section not in config.sections():
            config.add_section(section)
        config.set(section, option, str(value))
        with open(file, 'w+', encoding='utf-8') as cf:
            config.write(cf)


    def video_stream(self):
        if self.use_system_camera == True:
            Thread(target=self.system_camera_stream, args=()).start()
        else:
            Thread(target=self.extern_camera_stream, args=()).start()


    # 切换摄像头状态
    def switch_camera_status(self):
        if self.camera_status == self.camera_closed:
            logger('打开摄像头')
            self.camera_status = self.camera_opened
            self.video_stream()
            self.switch_camera_status_action.setIcon(QIcon(icon_path.Icon_ui_close_camera))
            # 设置提示
            self.switch_camera_status_action.setToolTip('close_camera')
            time.sleep(2)
            # time.sleep(15)
            # 打开视频展示定时器
            self.timer_video.start()
            self.video_status = self.STATUS_PLAYING
            robot_other.save_template = False
            self.status_video_button.setStyleSheet('border-image: url(' + icon_path.Icon_player_pause + ')')
            self.status_video_button.clicked.connect(self.switch_video)
        else:
            logger('关闭摄像头')
            # 关闭视频展示定时器
            self.timer_video.stop()
            self.video_status = self.STATUS_INIT
            robot_other.save_template = False
            self.status_video_button.setStyleSheet('border-image: url(' + icon_path.Icon_player_play + ')')
            self.camera_status = self.camera_closed
            self.switch_camera_status_action.setIcon(QIcon(icon_path.Icon_ui_open_camera))
            self.switch_camera_status_action.setToolTip('open_camera')
            self.status_video_button.clicked.disconnect(self.switch_video)


    # 系统摄像头流
    def system_camera_stream(self):
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.video_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.video_height)
        while self.camera_status == self.camera_opened:
            _, frame = cap.read()
            self.image = frame.copy()
        cap.release()


    # 外接摄像头
    def extern_camera_stream(self):
        # create a device manager
        device_manager = gx.DeviceManager()
        dev_num, dev_info_list = device_manager.update_device_list()
        if dev_num is 0:
            print("Number of enumerated devices is 0")
            return
        # open device by serial number
        cam = device_manager.open_device_by_sn(dev_info_list[0].get("sn"))
        # if camera is mono
        if cam.PixelColorFilter.is_implemented() is False:
            print("This sample does not support mono camera.")
            cam.close_device()
            return
        # set continuous acquisition
        cam.TriggerMode.set(gx.GxSwitchEntry.OFF)
        # set exposure(曝光)
        cam.ExposureTime.set(10000.0)
        # set gain(增益)
        cam.Gain.set(10.0)
        # set roi(ROI)
        cam.Width.set(self.video_width)
        cam.Height.set(self.video_height)
        cam.OffsetX.set(int((1200-self.video_height)/2))
        cam.OffsetY.set(int((1920-self.video_width)/2))
        # 自动白平衡
        cam.BalanceWhiteAuto.set(True)
        # set param of improving image quality
        if cam.GammaParam.is_readable():
            gamma_value = cam.GammaParam.get()
            gamma_lut = gx.Utility.get_gamma_lut(gamma_value)
        else:
            gamma_lut = None
        if cam.ContrastParam.is_readable():
            contrast_value = cam.ContrastParam.get()
            contrast_lut = gx.Utility.get_contrast_lut(contrast_value)
        else:
            contrast_lut = None
        color_correction_param = cam.ColorCorrectionParam.get()
        # start data acquisition
        cam.stream_on()
        # acquisition image: num is the image number
        while self.camera_status == self.camera_opened:
            # get raw image
            raw_image = cam.data_stream[0].get_image()
            if raw_image is None:
                print("Getting image failed.")
                continue
            # get RGB image from raw image
            rgb_image = raw_image.convert("RGB")
            if rgb_image is None:
                continue
            # improve image quality
            rgb_image.image_improvement(color_correction_param, contrast_lut, gamma_lut)
            # create numpy array with data from raw image
            numpy_image = rgb_image.get_numpy_array()
            if numpy_image is None:
                continue
            # 将图片格式转换为cv模式
            numpy_image = cv2.cvtColor(np.asarray(numpy_image), cv2.COLOR_RGB2BGR)
            self.image = numpy_image.copy()
            # print height, width, and frame ID of the acquisition image
            # print("Frame ID: %d   Height: %d   Width: %d" % (raw_image.get_frame_id(), raw_image.get_height(), raw_image.get_width()))
        # stop data acquisition
        cam.stream_off()
        # close device
        cam.close_device()


    # 拍照/截屏 动作
    def screen_shot(self):
        # 视频流未打开时不允许拍照
        if self.camera_status == self.camera_closed:
            QMessageBox.warning(self, "警告", "还没有开启视频流! 请打开视频流!", QMessageBox.Yes | QMessageBox.No)
        else:
            Thread(target=self.screen_capture_thread, args=()).start()


    # 摄像头截屏线程
    def screen_capture_thread(self, capture_type='jpg'):
        capture_path = os.path.join(self.picture_path, 'screen_shot')
        if os.path.exists(capture_path) is False:
            os.makedirs(capture_path)
        capture_name = str(datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')) + '.' + capture_type
        capture_name = os.path.join(capture_path, capture_name)
        cv2.imencode('.' + capture_type, self.image.copy())[1].tofile(capture_name)
        logger('[截取的图片为: %s]' %capture_name)


    # 框选车机屏幕大小
    def box_screen(self):
        # 视频流未打开时不允许框选车机屏幕
        if self.camera_status == self.camera_closed:
            QMessageBox.warning(self, "警告", "请先打开视频流! 之后再框选屏幕!", QMessageBox.Yes | QMessageBox.No)
        else:
            reply = QMessageBox.question(self, '提示', '是否要框选车机屏幕?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                gloVar.box_screen_flag = True
                uArm_action.uArm_action_type = None


    # 更新控制台内容
    def update_text(self, text):
        cursor = self.console.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.console.setTextCursor(cursor)
        self.console.ensureCursorVisible()


    # 菜单栏
    def menu_bar(self):
        # 菜单栏显示
        self.test_action = QAction('exit', self)
        self.filebar = self.menubar.addMenu('File')
        self.filebar.addAction(self.test_action)


    # 机械臂动作事件
    def uArm_action_event(self, action):
        if sum(self.label_video.box_screen_size) == 0:
            QMessageBox.about(self, "提示", "请先框选屏幕大小")
            return
        else:
            Thread(target=self.uArm_action_event_thread, args=(action,)).start()


    # 机械臂动作线程
    def uArm_action_event_thread(self, action):
        if action == uArm_action.uArm_click:
            uArm_action.uArm_action_type = uArm_action.uArm_click
        elif action == uArm_action.uArm_double_click:
            uArm_action.uArm_action_type = uArm_action.uArm_double_click
        elif action == uArm_action.uArm_long_click:
            uArm_action.uArm_action_type = uArm_action.uArm_long_click
        elif action == uArm_action.uArm_slide:
            uArm_action.uArm_action_type = uArm_action.uArm_slide
        elif action == uArm_action.uArm_lock:
            response = self.uArm_get_request(uArm_action.uArm_lock)
            logger(response)
        elif action == uArm_action.uArm_unlock:
            response = self.uArm_get_request(uArm_action.uArm_unlock)
            logger(response)
        elif action == uArm_action.uArm_get_position:
            response = self.uArm_get_request(uArm_action.uArm_get_position)
            uArm_param.base_x_point = float(response.split(',')[0])
            uArm_param.base_y_point = float(response.split(',')[1])
            uArm_param.base_z_point = float(response.split(',')[2])
            logger('当前位置为: %s' %response)
        else:
            logger('当前不支持[%s]这个动作' %action)



    # 机械臂相关操作函数(获取)
    def uArm_get_request(self, action):
        try:
            response = requests.get(uArm_param.port_address + str(action))
            return response.text
        except:
            return '机械臂服务连接异常'


    # 获取picture路径
    def get_picture_path(self):
        self.picture_path = QtWidgets.QFileDialog.getExistingDirectory(self.centralwidget, "浏览", self.picture_path)
        self.set_config_value(gloVar.config_file_path, 'param', 'picture_path', self.picture_path)
        logger('修改保存图片路径为: %s' %self.picture_path)


    def tool_bar(self):
        # ui相关action
        self.setting_action               = QAction(QIcon(icon_path.Icon_ui_setting), 'setting', self)
        self.switch_camera_status_action  = QAction(QIcon(icon_path.Icon_ui_open_camera), 'open_camera', self)
        self.capture_action               = QAction(QIcon(icon_path.Icon_ui_capture), 'capture', self)
        self.box_screen_action            = QAction(QIcon(icon_path.Icon_ui_box_screen), 'box_screen', self)
        self.picture_path_action          = QAction(QIcon(icon_path.Icon_ui_folder_go), 'picture_path', self)
        # 绑定触发函数
        self.switch_camera_status_action.triggered.connect(self.switch_camera_status)
        self.capture_action.triggered.connect(self.screen_shot)
        self.box_screen_action.triggered.connect(self.box_screen)
        self.picture_path_action.triggered.connect(self.get_picture_path)
        # robot相关action
        self.click_action        = QAction(QIcon(icon_path.Icon_robot_click), 'click', self)
        self.double_click_action = QAction(QIcon(icon_path.Icon_robot_double_click), 'double_click', self)
        self.long_click_action   = QAction(QIcon(icon_path.Icon_robot_long_click), 'long_click', self)
        self.slide_action        = QAction(QIcon(icon_path.Icon_robot_slide), 'slide', self)
        self.robot_lock_action   = QAction(QIcon(icon_path.Icon_robot_lock), 'lock', self)
        self.robot_unlock_action = QAction(QIcon(icon_path.Icon_robot_unlock), 'unlock', self)
        self.robot_get_position_action = QAction(QIcon(icon_path.Icon_robot_get_position), 'get_position', self)
        # 绑定触发函数
        self.click_action.triggered.connect(lambda: self.uArm_action_event(uArm_action.uArm_click))
        self.double_click_action.triggered.connect(lambda: self.uArm_action_event(uArm_action.uArm_double_click))
        self.long_click_action.triggered.connect(lambda: self.uArm_action_event(uArm_action.uArm_long_click))
        self.slide_action.triggered.connect(lambda: self.uArm_action_event(uArm_action.uArm_slide))
        self.robot_lock_action.triggered.connect(lambda: self.uArm_action_event(uArm_action.uArm_lock))
        self.robot_unlock_action.triggered.connect(lambda: self.uArm_action_event(uArm_action.uArm_unlock))
        self.robot_get_position_action.triggered.connect(lambda : self.uArm_action_event(uArm_action.uArm_get_position))
        # ui工具栏
        self.ui_toolbar.addAction(self.setting_action)
        self.ui_toolbar.addAction(self.switch_camera_status_action)
        self.ui_toolbar.addAction(self.capture_action)
        self.ui_toolbar.addAction(self.box_screen_action)
        self.ui_toolbar.addAction(self.picture_path_action)
        self.ui_toolbar.addSeparator()
        # robot工具栏
        self.robot_operate_toolbar.addAction(self.robot_lock_action)
        self.robot_operate_toolbar.addAction(self.robot_unlock_action)
        self.robot_operate_toolbar.addAction(self.robot_get_position_action)
        self.robot_operate_toolbar.addAction(self.click_action)
        self.robot_operate_toolbar.addAction(self.double_click_action)
        self.robot_operate_toolbar.addAction(self.long_click_action)
        self.robot_operate_toolbar.addAction(self.slide_action)


    # 视频播放框架
    def video_play_frame(self):
        self.video_frame = QFrame(self.centralwidget)
        self.grid.addWidget(self.video_frame, 0, 0, 5, 8)
        self.video_frame.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.video_frame_h_layout = QHBoxLayout(self.video_frame)
        # 视频标签
        self.label_video = Video_Label(self.video_frame)
        self.label_video.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.label_video.setObjectName('label_video')
        # 填充背景图片
        self.label_video.setPixmap(QtGui.QPixmap(self.background_file))
        # 自动填充满label
        self.label_video.setScaledContents(True)
        # 十字光标
        self.label_video.setCursor(Qt.CrossCursor)

        # 单独布局视频label
        self.video_frame_h_layout.addStretch(1)
        self.video_frame_h_layout.addWidget(self.label_video)
        self.video_frame_h_layout.addStretch(1)

        # label垂直布局
        self.label_v_layout = QVBoxLayout(self.label_video)
        # button水平布局
        self.button_h_layout = QHBoxLayout(self.label_video)
        # 暂停按钮/空格键
        self.status_video_button = QtWidgets.QPushButton(self.label_video)
        self.status_video_button.setObjectName('status_video_button')
        self.status_video_button.setFixedSize(48, 48)
        # 图片铺满按钮背景
        self.status_video_button.setStyleSheet('border-image: url('+ icon_path.Icon_player_play + ')')
        self.status_video_button.setShortcut(Qt.Key_Space)
        # 上一个视频
        self.last_video_button = QtWidgets.QPushButton(self.label_video)
        self.last_video_button.setObjectName('last_video_button')
        self.last_video_button.setFixedSize(48, 48)
        self.last_video_button.setStyleSheet('border-image: url('+ icon_path.Icon_player_last_video + ')')
        self.last_video_button.setShortcut(Qt.Key_Up)
        self.last_video_button.clicked.connect(self.last_video)
        self.last_video_button.setEnabled(True)
        # 下一个视频
        self.next_video_button = QtWidgets.QPushButton(self.label_video)
        self.next_video_button.setObjectName('next_video_button')
        self.next_video_button.setFixedSize(48, 48)
        self.next_video_button.setStyleSheet('border-image: url('+ icon_path.Icon_player_next_video + ')')
        self.next_video_button.setShortcut(Qt.Key_Down)
        self.next_video_button.clicked.connect(self.next_video)
        self.next_video_button.setEnabled(False)
        # 上一帧
        self.last_frame_button = QtWidgets.QPushButton(self.label_video)
        self.last_frame_button.setObjectName('last_frame_button')
        self.last_frame_button.setFixedSize(48, 48)
        self.last_frame_button.setStyleSheet('border-image: url('+ icon_path.Icon_player_last_frame + ')')
        self.last_frame_button.setShortcut(Qt.Key_Left)
        self.last_frame_button.clicked.connect(self.last_frame)
        self.last_frame_button.setEnabled(False)
        # 下一帧
        self.next_frame_button = QtWidgets.QPushButton(self.label_video)
        self.next_frame_button.setObjectName('next_frame_button')
        self.next_frame_button.setFixedSize(48, 48)
        self.next_frame_button.setStyleSheet('border-image: url(' + icon_path.Icon_player_next_frame + ')')
        self.next_frame_button.setShortcut(Qt.Key_Right)
        self.next_frame_button.clicked.connect(self.next_frame)
        self.next_frame_button.setEnabled(False)
        # 帧数显示
        self.label_frame_show = QtWidgets.QLabel(self.label_video)
        self.label_frame_show.setObjectName("label_frame_show")
        self.label_frame_show.setAlignment(Qt.AlignCenter)
        self.label_frame_show.setText('')
        self.label_frame_show.setFont(QFont(Ui_MainWindow.font, 12))
        self.label_frame_show.setAlignment(Qt.AlignCenter)
        self.label_frame_show.setStyleSheet('color:black')
        # 显示视频名字
        self.label_video_title = QtWidgets.QLabel(self.label_video)
        self.label_video_title.setObjectName("label_video_title")
        self.label_video_title.setAlignment(Qt.AlignCenter)
        self.label_video_title.setText('实时视频流')
        self.label_video_title.setFont(QFont(Ui_MainWindow.font, 15))
        # 视频进度条
        self.video_progress_bar = QSlider(Qt.Horizontal, self.label_video)
        self.video_progress_bar.valueChanged.connect(self.connect_video_progress_bar)
        # button布局管理
        self.button_h_layout.addStretch(1)
        self.button_h_layout.addWidget(self.last_frame_button)
        self.button_h_layout.addSpacing(30)
        self.button_h_layout.addWidget(self.last_video_button)
        self.button_h_layout.addSpacing(30)
        self.button_h_layout.addWidget(self.status_video_button)
        self.button_h_layout.addSpacing(30)
        self.button_h_layout.addWidget(self.next_video_button)
        self.button_h_layout.addSpacing(30)
        self.button_h_layout.addWidget(self.next_frame_button)
        self.button_h_layout.addStretch(1)
        # label布局管理
        self.label_v_layout.addWidget(self.label_video_title)
        self.label_v_layout.addStretch(1)
        self.label_v_layout.addWidget(self.label_frame_show)
        self.label_v_layout.addWidget(self.video_progress_bar)
        self.label_v_layout.addLayout(self.button_h_layout)


# 进度条刷新
    def slider_refresh(self):
        if self.video_play_flag is True and self.slider_flag is True:
            try:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
                flag, self.image = self.cap.read()
            except Exception as e:
                pass
            self.slider_flag = False


    # case展示
    def show_case(self):
        self.case_show_frame = QtWidgets.QFrame(self.centralwidget)
        self.case_show_frame.setFrameShape(QtWidgets.QFrame.Box)
        self.case_show_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.case_show_frame.setObjectName("case_show_frame")
        self.case_show_frame.setMinimumWidth(80)
        self.grid.addWidget(self.case_show_frame, 0, 8, 3, 2)
        self.case_show_v_layout = QVBoxLayout(self.case_show_frame)
        self.label_case_show = QtWidgets.QLabel(self.case_show_frame)
        self.label_case_show.setText('[case描述]')
        self.label_case_show.setFont(QFont(Ui_MainWindow.font, 12))
        self.edit_case_show = QTextEdit(self.case_show_frame)
        self.edit_case_show.ensureCursorVisible()
        self.edit_case_show.setLineWrapMode(QTextEdit.FixedPixelWidth)
        self.edit_case_show.setWordWrapMode(QTextOption.NoWrap)
        self.edit_case_show.setFont(QFont(Ui_MainWindow.font, 12))
        self.edit_case_show.setStyleSheet('background-color:lightGray')
        self.case_show_v_layout.addWidget(self.label_case_show)
        self.case_show_v_layout.addWidget(self.edit_case_show)


    # 控制台输出
    def output_text(self):
        self.frame_of_console_output = QtWidgets.QFrame(self.centralwidget)
        self.frame_of_console_output.setFrameShape(QtWidgets.QFrame.Box)
        self.frame_of_console_output.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_of_console_output.setObjectName("frame_of_console_output")
        self.frame_of_console_output.setMinimumWidth(80)
        self.grid.addWidget(self.frame_of_console_output, 3, 8, 2, 2)
        self.console_v_layout = QVBoxLayout(self.frame_of_console_output)
        self.label_output = QtWidgets.QLabel(self.frame_of_console_output)
        self.label_output.setObjectName("label_output")
        self.label_output.setText('[Console输出]')
        self.label_output.setAlignment(Qt.AlignLeft)
        self.label_output.setFont(QFont(Ui_MainWindow.font, 12))
        self.console = QTextEdit(self.frame_of_console_output)
        self.console.setReadOnly(True)
        self.console.ensureCursorVisible()
        self.console.setLineWrapMode(QTextEdit.FixedPixelWidth)
        self.console.setWordWrapMode(QTextOption.NoWrap)
        self.console.setFont(QFont(Ui_MainWindow.font, 12))
        self.console.setStyleSheet('background-color:lightGray')
        self.console_v_layout.addWidget(self.label_output)
        self.console_v_layout.addWidget(self.console)


    # 展示视频函数
    def show_video(self):
        # 实时模式
        if self.video_play_flag is False:
            show = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
            show_image = QtGui.QImage(show.data, show.shape[1], show.shape[0], QtGui.QImage.Format_RGB888)
            self.label_video.setPixmap(QtGui.QPixmap.fromImage(show_image))
            if gloVar.save_pic_flag == True:
                cv2.imencode('.jpg', self.image.copy())[1].tofile('mask.jpg')
                gloVar.save_pic_flag = False
        # 录播模式(可以数帧)
        else:
            if self.current_frame < self.frame_count:
                self.current_frame += 1
                flag, self.image = self.cap.read()
                if flag is True:
                    show = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
                    show_image = QtGui.QImage(show.data, show.shape[1], show.shape[0], QtGui.QImage.Format_RGB888)
                    self.label_video.setPixmap(QtGui.QPixmap.fromImage(show_image))
                    self.label_frame_show.setText(str(self.current_frame+1)+'F/'+str(self.frame_count))
                    self.label_frame_show.setStyleSheet('color:white')
                    self.video_progress_bar.setValue(self.current_frame)
                else:
                    self.cap.release()
                    self.video_status = Ui_MainWindow.STATUS_STOP
                    self.timer_video.stop()
                    self.status_video_button.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
                    self.video_progress_bar.setValue(self.frame_count-1)
                    self.last_video_button.setEnabled(True)
                    self.next_video_button.setEnabled(True)
            else:
                self.video_status = Ui_MainWindow.STATUS_STOP
                self.timer_video.stop()
                self.status_video_button.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        QApplication.processEvents() # 界面刷新


# 暂停视频
    def template_label(self):
        time.sleep(0.3)
        # 暂停后不允许机械臂动作操作
        uArm_action.uArm_action_type = None
        robot_other.image = self.image
        # # 数据处理调用
        # if robot_other.data_process_flag is True:
        #     maskImage_path = os.path.join(self.get_path, 'mask')
        # else:
        #     maskImage_path = None
        maskImage_path = self.picture_path
        robot_other.mask_path = maskImage_path

    # 空格键 播放/暂停/重播
    def switch_video(self):
        # 按钮防抖
        self.status_video_button.setEnabled(False)
        # 如果是实时模式
        if self.video_play_flag is False:
            if self.video_status is Ui_MainWindow.STATUS_INIT:
                self.timer_video.start()
                self.label_video_title.setStyleSheet('color:white')
                self.video_status = Ui_MainWindow.STATUS_PLAYING
                robot_other.save_template = False
                self.status_video_button.setStyleSheet('border-image: url(' + icon_path.Icon_player_pause + ')')
                logger('打开视频流')
            elif self.video_status is Ui_MainWindow.STATUS_PLAYING:
                self.timer_video.stop()
                self.video_status = Ui_MainWindow.STATUS_PAUSE
                robot_other.save_template = True
                self.status_video_button.setStyleSheet('border-image: url(' + icon_path.Icon_player_play + ')')
                self.template_label()
                logger('暂停视频流')
            elif self.video_status is Ui_MainWindow.STATUS_PAUSE:
                self.timer_video.start()
                self.label_video_title.setStyleSheet('color:white')
                self.video_status = Ui_MainWindow.STATUS_PLAYING
                robot_other.save_template = False
                self.status_video_button.setStyleSheet('border-image: url(' + icon_path.Icon_player_pause + ')')
                logger('打开视频流')
            elif self.video_status is Ui_MainWindow.STATUS_STOP:
                if self.video_play_flag is False:
                    self.cap = cv2.VideoCapture(0)
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.video_width)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.video_height)
                else:
                    self.cap = cv2.VideoCapture(self.videos[self.current_video])
                self.timer_video.start()
                self.label_video_title.setStyleSheet('color:white')
                self.video_status = Ui_MainWindow.STATUS_PLAYING
                self.status_video_button.setStyleSheet('border-image: url(' + icon_path.Icon_player_pause + ')')
        else: # 如果是录播模式
            if self.video_status is Ui_MainWindow.STATUS_INIT:
                self.timer_video.start()
                self.last_frame_button.setEnabled(False)
                self.next_frame_button.setEnabled(False)
                self.last_video_button.setEnabled(False)
                self.next_video_button.setEnabled(False)
                self.label_video_title.setStyleSheet('color:white')
                self.video_status = Ui_MainWindow.STATUS_PLAYING
                self.status_video_button.setStyleSheet('border-image: url(' + icon_path.Icon_player_pause + ')')
                robot_other.save_template = False
            elif self.video_status is Ui_MainWindow.STATUS_PLAYING:
                self.timer_video.stop()
                # 暂停后/使能上下一帧
                self.last_frame_button.setEnabled(True)
                self.next_frame_button.setEnabled(True)
                self.last_video_button.setEnabled(True)
                self.next_video_button.setEnabled(True)
                self.video_status = Ui_MainWindow.STATUS_PAUSE
                self.status_video_button.setStyleSheet('border-image: url(' + icon_path.Icon_player_play + ')')
                robot_other.save_template = True
                self.template_label()
            elif self.video_status is Ui_MainWindow.STATUS_PAUSE:
                self.timer_video.start()
                self.last_frame_button.setEnabled(False)
                self.next_frame_button.setEnabled(False)
                self.last_video_button.setEnabled(False)
                self.next_video_button.setEnabled(False)
                self.label_video_title.setStyleSheet('color:white')
                self.video_status = Ui_MainWindow.STATUS_PLAYING
                self.status_video_button.setStyleSheet('border-image: url(' + icon_path.Icon_player_pause + ')')
                robot_other.save_template = False
            elif self.video_status is Ui_MainWindow.STATUS_STOP:
                self.current_frame = 0
                self.cap = cv2.VideoCapture(self.videos[self.current_video]) # 重新加载这个视频
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
                # 获取视频总帧数
                self.frame_count = int(self.cap.get(7))
                _, self.image = self.cap.read()
                show = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
                show_image = QtGui.QImage(show.data, show.shape[1], show.shape[0], QtGui.QImage.Format_RGB888)
                self.label_video.setPixmap(QtGui.QPixmap.fromImage(show_image))
                self.label_video_title.setStyleSheet('color:white')
                self.label_frame_show.setText(str(self.current_frame+1)+'F/'+str(self.frame_count))
                self.label_frame_show.setStyleSheet('color:white')
                # 设置视频进度滑动条范围
                self.video_progress_bar.setRange(0, self.frame_count-1)
                # 开启视频流
                self.timer_video.start()
                self.last_video_button.setEnabled(False)
                self.next_video_button.setEnabled(False)
                self.last_frame_button.setEnabled(False)
                self.next_frame_button.setEnabled(False)
                self.video_status = Ui_MainWindow.STATUS_PLAYING
                self.status_video_button.setStyleSheet('border-image: url(' + icon_path.Icon_player_pause + ')')
        self.status_video_button.setEnabled(True)



    # 切换到上个视频
    def last_video(self):
        # 防抖
        self.last_video_button.setEnabled(False)
        if self.video_play_flag is True:
            self.timer_video.stop()
            self.video_status = Ui_MainWindow.STATUS_STOP
            self.status_video_button.setStyleSheet('border-image: url(' + icon_path.Icon_player_play + ')')
            if self.current_video > 0:
                self.current_video = self.current_video - 1
            else:
                self.current_video = len(self.videos) - 1
            self.cap = self.videos[self.current_video]
            self.label_video_title.setText('['+str(self.current_video+1)+'/'+str(len(self.videos))+']'
                                           +self.videos_title[self.current_video])
            self.label_video_title.setStyleSheet('color:black')
            self.label_video.setPixmap(QtGui.QPixmap(self.background_file))
            self.last_frame_button.setEnabled(False)
            self.next_frame_button.setEnabled(False)
        self.last_video_button.setEnabled(True)
        self.next_video_button.setEnabled(True)
        self.status_video_button.setEnabled(True)
        # 重置帧数显示位置
        self.current_frame = 0
        self.video_progress_bar.setValue(0)
        self.label_frame_show.setText('')
        self.label_frame_show.setStyleSheet('color:white')
        self.last_video_button.setEnabled(True)

    # 切换到下个视频
    def next_video(self):
        # 防抖
        self.next_video_button.setEnabled(False)
        if self.video_play_flag is True:
            self.timer_video.stop()
            self.video_status = Ui_MainWindow.STATUS_STOP
            self.status_video_button.setStyleSheet('border-image: url(' + icon_path.Icon_player_play + ')')
            if self.current_video < len(self.videos) - 1:
                self.current_video = self.current_video + 1
            else:
                self.current_video = 0
            self.cap = self.videos[self.current_video]
            self.label_video_title.setText('['+str(self.current_video+1)+'/'+str(len(self.videos))+']'
                                           +self.videos_title[self.current_video])
            self.label_video_title.setStyleSheet('color:black')
            self.label_video.setPixmap(QtGui.QPixmap(self.background_file))
            self.last_frame_button.setEnabled(False)
            self.next_frame_button.setEnabled(False)
        self.last_video_button.setEnabled(True)
        self.next_video_button.setEnabled(True)
        self.status_video_button.setEnabled(True)
        # 重置帧数显示位置
        self.current_frame = 0
        self.video_progress_bar.setValue(0)
        self.label_frame_show.setText('')
        self.label_frame_show.setStyleSheet('color:white')
        self.next_video_button.setEnabled(True)

    # 切换到上一帧(不能防抖, 如果防抖的话就不能左右键快速播帧)
    def last_frame(self):
        # self.last_frame_button.setEnabled(False)
        if self.current_frame > 0:
            self.current_frame = self.current_frame - 1
        else:
            self.current_frame = 0
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
        flag, self.image = self.cap.read()
        if flag is True:
            show = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
            show_image = QtGui.QImage(show.data, show.shape[1], show.shape[0], QtGui.QImage.Format_RGB888)
            self.label_video.setPixmap(QtGui.QPixmap.fromImage(show_image))
            self.label_frame_show.setText(str(self.current_frame+1)+'F/'+str(self.frame_count))
            self.label_frame_show.setStyleSheet('color:white')
            self.video_progress_bar.setValue(self.current_frame)
        else:
            self.cap.release()
            self.video_status = Ui_MainWindow.STATUS_STOP
            self.timer_video.stop()
            self.status_video_button.setStyleSheet('border-image: url(' + icon_path.Icon_player_replay + ')')
            self.video_progress_bar.setValue(self.frame_count-1)
        # self.last_frame_button.setEnabled(True)

    # 切换到下一帧(不能防抖, 如果防抖的话就不能左右键快速播帧)
    def next_frame(self):
        # self.next_frame_button.setEnabled(False)
        if self.current_frame < self.frame_count - 1:
            self.current_frame = self.current_frame + 1
        else:
            self.current_frame = self.frame_count - 1
        flag, self.image = self.cap.read()
        if flag is True:
            show = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
            show_image = QtGui.QImage(show.data, show.shape[1], show.shape[0], QtGui.QImage.Format_RGB888)
            self.label_video.setPixmap(QtGui.QPixmap.fromImage(show_image))
            self.label_frame_show.setText(str(self.current_frame+1)+'F/'+str(self.frame_count))
            self.label_frame_show.setStyleSheet('color:white')
            self.video_progress_bar.setValue(self.current_frame)
        else:
            self.cap.release()
            self.video_status = Ui_MainWindow.STATUS_STOP
            self.timer_video.stop()
            self.status_video_button.setStyleSheet('border-image: url(' + icon_path.Icon_player_replay + ')')
            self.video_progress_bar.setValue(self.frame_count-1)
        # self.next_frame_button.setEnabled(True)


    # 连接到视频进度栏
    def connect_video_progress_bar(self):
        self.current_frame = self.video_progress_bar.value()
        self.label_frame_show.setText(str(self.current_frame + 1) + 'F/' + str(self.frame_count))
        self.label_frame_show.setStyleSheet('color:white')
        self.slider_flag = True


    # 重写窗口关闭时间
    def closeEvent(self, event):
        reply = QMessageBox.question(self, '本程序', '是否要退出程序?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            # 关闭摄像头
            self.camera_status = self.camera_closed
            event.accept()
        else:
            event.ignore()


    # 监听窗口缩放事件
    def resizeEvent(self, event):
        # 第一次触发实在窗口生成的时候, 没有意义
        if self.first_window_zoom_flag is True:
            self.first_window_zoom_flag  = False
            # 通过中心widget计算初始视频标签的大小(同时减去的50代表widget的边界部分)
            self.video_label_size_width  = int((self.centralwidget.size().width() -50)*0.75)
            self.video_label_size_height = int((self.centralwidget.size().height()-50)*1.00)
        else: # (距离边框还有30左右)
            self.video_label_size_width  = self.video_frame.size().width()  - 50
            self.video_label_size_height = self.video_frame.size().height() - 50
        # 更改label_video大小以确保视频展示不失比例
        # 真实视频比例
        video_size_scale = float(self.video_height/self.video_width)
        # 临界比例(根据页面网格布局得到, 不可随便修改)
        limit_size_scale = float(982/1477)
        if video_size_scale >= limit_size_scale:
            self.video_label_size_height = self.video_label_size_height
            self.video_label_size_width = int((self.video_label_size_height/self.video_height) * self.video_width)
        else:
            self.video_label_size_width = self.video_label_size_width
            self.video_label_size_height = int((self.video_label_size_width/self.video_width) * self.video_height)
        self.label_video.setFixedSize(self.video_label_size_width, self.video_label_size_height)
        # 计算视频和label_video之间比例因子(框选保存图片需要用到)
        self.label_video.x_unit = float(self.video_width /self.video_label_size_width)
        self.label_video.y_unit = float(self.video_height/self.video_label_size_height)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = Ui_MainWindow()
    gui.setupUi()
    gui.show()
    sys.exit(app.exec_())