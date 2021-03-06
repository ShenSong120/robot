import re
from threading import Thread
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from GlobalVar import *
from uiclass.controls import CaseControl
from processdata.get_startup_time_by_stable_point import GetStartupTimeByStablePoint
from processdata.get_startup_time import GetStartupTime


class ShowCaseTab(QWidget):

    signal = pyqtSignal(str)

    def __init__(self, parent):
        super(ShowCaseTab, self).__init__(parent)
        self.parent = parent
        # 样式美化
        style = BeautifyStyle.font_family + BeautifyStyle.font_size + BeautifyStyle.file_dialog_qss
        self.setStyleSheet(style)
        self.index = -1
        # case控件列表
        self.case_control_list = []
        # item列表
        self.item_list = []
        # case文件列表
        self.case_file_list = []
        # 是否全部选中状态(False:没有全部选中, True:全部选中)
        self.select_all_flag = False
        # 当前打开的脚本路径
        self.script_path = None
        # 初始化
        self.case_tab_init()

    def case_tab_init(self):
        self.new_button = QToolButton()
        self.new_button.setToolTip('新建case')
        self.new_button.setStyleSheet('QToolButton{border-image: url(' + IconPath.Icon_tab_widget_new + ')}')
        self.new_button.clicked.connect(self.connect_new_button)
        # 添加case
        self.import_button = QToolButton()
        self.import_button.setToolTip('添加case')
        self.import_button.setStyleSheet('QToolButton{border-image: url(' + IconPath.Icon_tab_widget_import + ')}')
        self.import_button.clicked.connect(lambda : self.connect_import_button(None))
        # 批量删除case
        self.delete_button = QToolButton()
        self.delete_button.setToolTip('批量删除case')
        self.delete_button.setStyleSheet('QToolButton{border-image: url(' + IconPath.Icon_tab_widget_delete + ')}')
        self.delete_button.clicked.connect(self.connect_delete_selected_items)
        # 全部选中(不选中)
        self.select_all_button = QToolButton()
        self.select_all_button.setToolTip('全部选中')
        self.select_all_button.setStyleSheet('QToolButton{border-image: url(' + IconPath.Icon_tab_widget_all_select + ')}')
        self.select_all_button.clicked.connect(self.connect_select_all_items)
        # 批量执行
        self.execute_button = QToolButton()
        self.execute_button.setToolTip('批量执行case')
        self.execute_button.setStyleSheet('QToolButton{border-image: url(' + IconPath.Icon_tab_widget_execute + ')}')
        self.execute_button.clicked.connect(self.connect_execute_selected_items)
        # 停止执行
        self.stop_button = QToolButton()
        self.stop_button.setToolTip('停止执行case')
        self.stop_button.setStyleSheet('QToolButton{border-image: url(' + IconPath.Icon_tab_widget_stop + ')}')
        self.stop_button.clicked.connect(self.connect_stop_execute_case)
        # 切换按钮(是否需要产生报告)
        self.switch_button = QToolButton()
        self.switch_button.setMinimumWidth(40)
        self.switch_button.setToolTip('关闭处理报告功能')
        self.switch_button.setStyleSheet('QToolButton{border-image: url(' + IconPath.Icon_tab_widget_switch_on + ')}')
        self.switch_button.clicked.connect(self.connect_switch)
        # 次数标签
        self.execute_times_label = QLabel()
        self.execute_times_label.setText('次数:')
        self.execute_times_control = QSpinBox()
        self.execute_times_control.setStyleSheet('QSpinBox {background-color:transparent}')
        self.execute_times_control.setRange(1, 10)
        self.execute_times_control.setValue(1)
        # case所在文件夹
        self.case_folder_text = QLineEdit()
        self.case_folder_text.setStyleSheet('background-color:transparent')
        self.case_folder_text.setReadOnly(True)
        self.case_folder_text.setText('空白')
        # 布局
        h_box = QHBoxLayout()
        h_box.setSpacing(5)
        h_box.addWidget(self.new_button)
        h_box.addWidget(self.import_button)
        h_box.addWidget(self.delete_button)
        h_box.addWidget(self.select_all_button)
        h_box.addWidget(self.execute_button)
        h_box.addWidget(self.stop_button)
        h_box.addWidget(self.switch_button)
        h_box.addWidget(self.execute_times_label)
        h_box.addWidget(self.execute_times_control)
        h_box.addStretch(1)
        self.list_widget = QListWidget()
        self.list_widget.verticalScrollBar().setStyleSheet("QScrollBar{width:10px;}")
        self.list_widget.horizontalScrollBar().setStyleSheet("QScrollBar{height:10px;}")
        v_box = QVBoxLayout()
        v_box.setSpacing(0)
        # 左上右下
        v_box.setContentsMargins(0, 0, 0, 0)
        v_box.addWidget(self.case_folder_text)
        v_box.addSpacing(3)
        v_box.addLayout(h_box)
        v_box.addSpacing(3)
        v_box.addWidget(self.list_widget)
        self.setLayout(v_box)

    # 连接新建case按钮
    def connect_new_button(self):
        script_path = Profile(type='read', file=GloVar.config_file_path, section='param', option='script_path').value
        filename = QFileDialog.getSaveFileName(self, '保存case', script_path, 'script file(*.xml)',
                                               options=QFileDialog.DontUseNativeDialog)
        xml_file = filename[0]
        if xml_file:
            if xml_file.endswith('.xml'):
                xml_file = xml_file
            else:
                xml_file = xml_file + '.xml'
            current_path = '/'.join(xml_file.split('/')[:-1])
            if current_path != script_path:
                Profile(type='write', file=GloVar.config_file_path, section='param', option='script_path',
                        value=current_path)
            self.connect_import_button(case_file=xml_file)
        else:
            Logger('[未新建case!]')

    # 连接导入case按钮
    def connect_import_button(self, case_file=None):
        if case_file is None:
            # 通过选择框导入case
            script_path = Profile(type='read', file=GloVar.config_file_path, section='param', option='script_path').value
            files, ok = QFileDialog.getOpenFileNames(self, "选择case", script_path, "标签文件 (*.xml)", options=QFileDialog.DontUseNativeDialog)
            if ok:
                # 如果打开路径和配置文件路径不一样, 就将当前script路径保存到配置文件
                case_folder = os.path.split(files[0])[0]
                if case_folder != script_path:
                    Profile(type='write', file=GloVar.config_file_path, section='param', option='script_path', value=case_folder)
                # 文件去重
                files = self.case_file_list + files
                files = list(set(files))
                # 文件按照时间排序(倒序排列)
                # files = sorted(files, key=lambda file: os.path.getmtime(file), reverse=True)
                # 文件逆序排列(保证加入的case顺序正确, 按照case名排序)
                files = sorted(files, reverse=False)
                self.clear_all_items()
                for file in files:
                    self.add_item(file)
                self.case_file_list = files
                WindowStatus.case_tab_status = 'case路径>%s' % case_folder
                self.case_folder_text.setText(case_folder)
            else:
                Logger('没有选择case')
        else:
            # 插入第一个并去重
            files = self.case_file_list
            files.insert(0, case_file)
            files = list(set(files))
            self.clear_all_items()
            # 文件按照时间排序(倒序排列)
            # files = sorted(files, key=lambda file: os.path.getmtime(file), reverse=True)
            # 文件逆序排列(保证加入的case顺序正确, 按照case名排序)
            files = sorted(files, reverse=False)
            for file in files:
                self.add_item(file)

    # 1.筛选出没有被选中的items, 并将他们的info保存到list 2.使用循环创建没有被选中的items
    def delete_selected_items(self):
        # (从后面开始删除)先删除后面的(每次循环递减一个)
        index = len(self.case_control_list) - 1
        # 通过判断剩余item数量, 来确定是否需要更改‘全选’按键状态
        exist_items_count = index + 1
        # 获取到第一个删除项的下一项case名字(重写这一项就不会出现文本框选中现象, 不然会出现文本框选中现象)
        get_rewrite_case_name_flag = False
        # 重写case名字
        rewrite_case_name = None
        # 使用循环删除掉选中的case
        while True:
            if exist_items_count < 1:
                # 全部删除后需要复位全部选中按钮的状态
                self.select_all_flag = False
                self.select_all_button.setToolTip('全部选中')
                self.select_all_button.setStyleSheet('QToolButton{border-image: url(' + IconPath.Icon_tab_widget_all_select + ')}')
                break
            # 遍历完item后退出
            elif index < 0:
                break
            # 未遍历完item, 判断是否选中
            else:
                if self.case_control_list[index].check_box.checkState() == Qt.Checked:
                    if index < (len(self.case_control_list)-1) and get_rewrite_case_name_flag is False:
                        get_rewrite_case_name_flag = True
                        # 获取当前选中的下一项
                        rewrite_case_name = self.case_file_list[index + 1]
                    # 模拟点击case中的单独delete按钮(稳定)
                    self.case_control_list[index].delete_button.click()
                    exist_items_count -= 1
            index -= 1
        # 全部删除后需要复位全部选中按钮的状态
        self.select_all_flag = False
        self.select_all_button.setToolTip('全部选中')
        self.select_all_button.setStyleSheet('QToolButton{border-image: url(' + IconPath.Icon_tab_widget_all_select + ')}')
        # 处理出现的选中文本框
        if rewrite_case_name is not None:
            time.sleep(0.01)
            try: # 此处有可能产生异常(直接跳过即可)
                current_row = self.case_file_list.index(rewrite_case_name)
                text = self.case_control_list[current_row].case_name_edit.text()
                self.case_control_list[current_row].case_name_edit.setText(text)
            except:
                pass

    def connect_delete_selected_items(self):
        # 没有item的时候让button无效
        if self.index < 0:
            pass
        else:
            Thread(target=self.delete_selected_items, args=()).start()

    def connect_select_all_items(self):
        # 没有item的时候让button无效
        if self.index < 0:
            pass
        else:
            Thread(target=self.select_or_un_select_all_items, args=()).start()

    # 执行选中的case
    def execute_selected_items(self, execute_times):
        if GloVar.request_status is None:
            Logger('[当前还有正在执行的动作, 请稍后执行!]')
            return
        self.signal.emit('ready_execute_case>')
        time.sleep(0.3)
        # 停止执行标志位复位
        GloVar.stop_execute_flag = False
        # 开始执行
        for i in range(self.index+1):
            if self.case_control_list[i].check_box.checkState() == Qt.Checked:
                # 根据执行次数执行
                for x in range(execute_times):
                    while True:
                        if GloVar.request_status == 'ok' and GloVar.stop_execute_flag is False:
                            GloVar.request_status = None
                            case_path = self.case_file_list[i]
                            info_dict_list = Common.read_script_tag(case_path)
                            self.play_single_case(case_path, info_dict_list)
                            self.signal.emit('play_single_case>')
                            break
                        # 退出case的执行
                        elif GloVar.request_status == 'ok' and GloVar.stop_execute_flag is True:
                            break
                        else:
                            time.sleep(0.002)
                        # 执行每一条case后cpu休息一秒钟
                        time.sleep(1)
                    # 退出case的执行
                    if GloVar.stop_execute_flag is True:
                        break
                # 一条case执行完毕后(实时处理视频)
                while True:
                    if GloVar.request_status == 'ok':
                        if GloVar.real_time_show_report_flag is True:
                            Logger('[开始计算测试结果] : %s' % case_path)
                            video_path = Common.get_video_folder_by_case(case_path)
                            image_process_method = Profile(type='read', file=GloVar.config_file_path, section='param',
                                                           option='image_process_method').value
                            if image_process_method == 'method-1':
                                test = GetStartupTime(video_path=video_path)
                            elif image_process_method == 'method-2':
                                test = GetStartupTimeByStablePoint(video_path=video_path)
                            # 实时数据处理
                            test.data_processing_by_real_time()
                            Logger('[测试结果处理完毕] : %s' % case_path)
                            # 发送更新消息
                            # 获取路径中的时间
                            pattern = re.compile(r'\d+-\d+-\d+')
                            time_list = pattern.findall(video_path)
                            # 开始时间
                            test_time = '/'.join(time_list)
                            # 更改report路径
                            report_path = MergePath([GloVar.project_path, 'report', test_time, 'report.html']).merged_path
                            self.signal.emit('real_time_show_report_update>' + report_path)
                            break
                        else:
                            break
                    else:
                        time.sleep(0.2)
                # 是否退出case的执行
                if GloVar.stop_execute_flag is True:
                    break
        # 测试执行结束(改变标志位, 触发数据处理函数)
        while True:
            if GloVar.request_status == 'ok':
                if GloVar.real_time_show_report_flag is True:
                    # 清除视频处理缓存数据
                    GloVar.video_process_data = {}
                    # 发送实时更新停止信号
                    self.signal.emit('real_time_show_report_stop>')
                else:
                    self.signal.emit('test_finished>')
                # 退出case的执行标志位复位
                GloVar.stop_execute_flag = False
                break
            else:
                time.sleep(0.02)

    # 线程中执行选中的case
    def connect_execute_selected_items(self):
        # 今天的日期(用作文件夹名)
        today_data = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        # 获取工程视频保存路径
        GloVar.project_video_path = MergePath([GloVar.project_path, 'video', today_data]).merged_path
        # 每执行一次都需要获取当前时间(作为文件夹)
        GloVar.current_time = time.strftime('%H-%M-%S', time.localtime(time.time()))
        # 获取执行次数
        execute_times = self.execute_times_control.value()
        Thread(target=self.execute_selected_items, args=(execute_times,)).start()

    # 停止执行case
    @staticmethod
    def connect_stop_execute_case():
        GloVar.stop_execute_flag = True

    # 视频处理开关切换
    def connect_switch(self):
        # 打开开关
        if GloVar.video_process_switch == 'OFF':
            GloVar.video_process_switch = 'ON'
            self.switch_button.setToolTip('关闭处理报告功能')
            self.switch_button.setStyleSheet('QToolButton{border-image: url(' + IconPath.Icon_tab_widget_switch_on + ')}')
        # 关闭开关
        else:
            GloVar.video_process_switch = 'OFF'
            self.switch_button.setToolTip('开启处理报告功能')
            self.switch_button.setStyleSheet('QToolButton{border-image: url(' + IconPath.Icon_tab_widget_switch_off + ')}')

    # 接受case控件发送的信号
    def recv_case_control_signal(self, signal_str):
        # 打开当前case(拆分为action)
        if signal_str.startswith('open_case>'):
            id = int(signal_str.split('>')[1])
            case_path = self.case_file_list[id]
            case_name = os.path.split(case_path)[1]
            case_info_list = Common.read_script_tag(case_path)
            case_info_list.insert(0, case_name)
            case_info_list.insert(1, case_path)
            self.signal.emit('case_transform_to_action>'+str(case_info_list))
        # 执行单个case
        elif signal_str.startswith('play_single_case>'):
            if GloVar.request_status is None:
                Logger('[当前还有正在执行的动作, 请稍后执行!]')
                return
            id = int(signal_str.split('>')[1])
            case_path = self.case_file_list[id]
            info_dict_list = Common.read_script_tag(case_path)
            self.play_single_case(case_path, info_dict_list)
            self.signal.emit('play_single_case>')
        # 删除case
        elif signal_str.startswith('delete_case>'):
            id = int(signal_str.split('delete_case>')[1])
            self.delete_item(id)
        else:
            pass

    # 执行单个case(参数为从xml中读出来的)
    def play_single_case(self, case_path, info_dict_list):
        GloVar.post_info_list = []
        GloVar.post_info_list.append('start>'+case_path)
        for info_dict in info_dict_list:
            info_dict = Common.add_action_mark(info_dict)
            GloVar.post_info_list.append(info_dict)
        GloVar.post_info_list.append('stop')

    # 清除所有动作
    def clear_all_items(self):
        self.list_widget.clear()
        self.item_list = []
        self.case_control_list = []
        self.case_file_list = []
        self.index = -1

    # 全部选中或者全部不选中items
    def select_or_un_select_all_items(self):
        if self.select_all_flag is False:
            for i in range(self.index + 1):
                self.case_control_list[i].check_box.setCheckState(Qt.Checked)
            self.select_all_flag = True
            self.select_all_button.setToolTip('全不选中')
            self.select_all_button.setStyleSheet('QToolButton{border-image: url(' + IconPath.Icon_tab_widget_all_un_select + ')}')
            Logger('[全部选中]-->所有case')
        else:
            for i in range(self.index + 1):
                self.case_control_list[i].check_box.setCheckState(Qt.Unchecked)
            self.select_all_flag = False
            self.select_all_button.setToolTip('全部选中')
            self.select_all_button.setStyleSheet('QToolButton{border-image: url(' + IconPath.Icon_tab_widget_all_select + ')}')
            Logger('[全不选中]-->所有case')

    # 添加动作控件
    def add_item(self, case_file):
        # 给动作设置id
        self.index += 1
        item = QListWidgetItem()
        item.setSizeHint(QSize(330, 70))
        obj = CaseControl(parent=None, id=self.index, case_file=case_file)
        obj.signal[str].connect(self.recv_case_control_signal)
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, obj)
        self.item_list.append(item)
        self.case_control_list.append(obj)
        self.case_file_list.append(case_file)

    # 删除case
    def delete_item(self, id):
        self.list_widget.takeItem(id)
        self.item_list.pop(id)
        self.case_control_list.pop(id)
        self.case_file_list.pop(id)
        for i in range(id, self.index):
            self.case_control_list[i].id = i
        self.index -= 1
