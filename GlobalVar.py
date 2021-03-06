import os
import time
import cv2
import numpy as np
from other.operate_config import ConfigWithComment
import configparser
import xml.etree.cElementTree as ET


# 文件之间参数传递
class GloVar:
    # 配置文件路径
    config_file_path = 'config/config.ini'
    # 摄像头校正模型路径
    correction_model_path = 'config/calibrate/calibrate_1600x1000.npz'
    # 文件系统需要调用中文文件
    qt_zh_CN_file_path = 'config/translations/qt_zh_CN.qm'
    # adb路径
    adb_command = r'config\platform-tools\adb.exe'
    # 屏幕类型
    screen_type = ['中控屏', '副驾屏', '空调屏', '仪表屏']
    # 当前工程根目录
    project_path = None
    # 当前工程产生视频目录
    project_video_path = None
    # 当前工程照片存放目录
    project_picture_path = None
    # 保存的摄像头实时照片
    camera_image = None
    # 框选屏幕大小标志
    box_screen_flag = False
    # 保存图片标志(是否需要保存图片,用来实时监测目标位置)
    save_pic_flag = False
    # 添加动作按钮是否可以点击(需要先框选车机屏幕大小, 之后才能点击)
    add_action_button_flag = False
    # request请求状态(在可接收信息的时候才可以允许发送请求: ok可以发送请求/其余情况不可以发送请求)
    request_status = 'ok'
    # 一条case是否执行完了(当前case执行完后才会允许第二条case执行)
    case_execute_finished_flag = True
    # post请求信息(将当前所有需要执行的action装入list/第一个元素'start', 最后一个元素'stop')
    post_info_list = []
    # 当前时间(小时-分-秒), 测试过程中需要用这个当做路径, 保证每一次执行都能拥有一个独立的文件夹
    current_time = None
    # 视频处理开关标志位(OFF/ON, 默认打开, 不需要视频处理关掉即可)
    video_process_switch = 'ON'
    # 机械臂起点标志
    robot_start_flag = False
    # 需要进行框选动作时, 打开此标志
    select_template_flag = False
    # 全局传递模板图片路径
    mask_path = None
    # 当前case路径
    current_case_path = ''
    # 数据处理标志
    data_process_flag = False
    # 判断当前action是否已经保存成为case标志
    actions_saved_to_case = True
    # 数据处理完成标志
    data_process_finished_flag = False
    # 框选case中录像视频模板(other_template, assert_template, result_template暂时就这三个)
    draw_frame_flag = False
    '''三个draw_frame类型'''
    other_template = 'other_template'
    assert_template = 'assert_template'
    assert_template_finished = 'assert_template_finished'
    result_template = 'result_template'
    result_template_finished = 'result_template_finished'
    # 添加动作打开标志位
    add_action_window_opened_flag = False
    # 机械臂是否伴随新建动作运动(默认打开)
    robot_follow_action_flag = True
    # 机械臂是否收回(默认关闭,不收回)
    robot_action_take_back_flag = False
    # 退出所有线程标志
    exit_thread_flag = False
    # 停止执行标志(当前有很多case正在执行, 需要停下来的时候, 改变此标志位)
    stop_execute_flag = False
    # 是否实时展示报告
    real_time_show_report_flag = False
    # 存放数据处理后产生的数据(实时数据处理会用到)
    video_process_data = {}
    # 模板边界值
    template_border = 10
    # 触发起点的高度
    trigger_height = 1.3
    # 处理逐鹿产生的视频
    compete_platform_flag = False


# Icon路径
class IconPath:
    # 应用窗口图标
    Icon_file = 'config/Icon/other_icon/Icon.jpg'
    # 视频栏背景图标
    background_file = 'config/Icon/other_icon/background.jpg'
    # 分割线图标
    split_line_icon = 'config/Icon/other_icon/split_line.png'
    # 数据准备好的背景图
    data_is_ready_file = 'config/Icon/other_icon/data_is_ready.jpg'
    # 正在进行数据处理的时候的背景图片(688*500)
    data_processing_file = 'config/Icon/other_icon/data_processing.gif'
    # 数据处理结束
    data_process_finished_file = 'config/Icon/other_icon/data_process_finished.jpg'
    # 视频栏播放器图标
    Icon_player_play = 'config/Icon/video_label_icon/play.png'
    Icon_player_replay = 'config/Icon/video_label_icon/replay.png'
    Icon_player_pause = 'config/Icon/video_label_icon/pause.png'
    Icon_player_last_video = 'config/Icon/video_label_icon/last_video.png'
    Icon_player_next_video = 'config/Icon/video_label_icon/next_video.png'
    Icon_player_last_frame = 'config/Icon/video_label_icon/last_frame.png'
    Icon_player_next_frame = 'config/Icon/video_label_icon/next_frame.png'
    # 实时流工具栏相关action图标
    Icon_live_video_setting = 'config/Icon/live_video_toolbar_icon/setting.png'
    Icon_live_video_reload = 'config/Icon/live_video_toolbar_icon/reload.png'
    Icon_live_video_open_camera = 'config/Icon/live_video_toolbar_icon/open_camera.png'
    Icon_live_video_close_camera = 'config/Icon/live_video_toolbar_icon/close_camera.png'
    Icon_live_video_capture = 'config/Icon/live_video_toolbar_icon/capture.png'
    Icon_live_video_box_screen = 'config/Icon/live_video_toolbar_icon/box_screen.png'
    Icon_live_video_folder_go = 'config/Icon/live_video_toolbar_icon/folder_go.png'
    # robot工具栏相关action图标
    Icon_robot_click = 'config/Icon/robot_toolbar_icon/click.png'
    Icon_robot_double_click = 'config/Icon/robot_toolbar_icon/double_click.png'
    Icon_robot_long_click = 'config/Icon/robot_toolbar_icon/long_click.png'
    Icon_robot_slide = 'config/Icon/robot_toolbar_icon/slide.png'
    Icon_robot_lock = 'config/Icon/robot_toolbar_icon/lock.png'
    Icon_robot_unlock = 'config/Icon/robot_toolbar_icon/unlock.png'
    Icon_robot_get_base_position = 'config/Icon/robot_toolbar_icon/get_base_position.png'
    Icon_robot_with_record = 'config/Icon/robot_toolbar_icon/with_record.png'
    Icon_robot_without_record = 'config/Icon/robot_toolbar_icon/without_record.png'
    Icon_robot_restart = 'config/Icon/robot_toolbar_icon/restart.png'
    # 本地视频播放工具栏相关图标
    Icon_local_import_video = 'config/Icon/local_video_toolbar_icon/import_video.png'
    Icon_local_video_setting = 'config/Icon/local_video_toolbar_icon/setting.png'
    # 视频处理工具栏相关图标
    Icon_data_process_import_video = 'config/Icon/data_process_toolbar_icon/import_video.png'
    Icon_data_process_setting = 'config/Icon/data_process_toolbar_icon/setting.png'
    Icon_data_process_execute = 'config/Icon/data_process_toolbar_icon/data_process_execute.png'
    # 逐鹿操作工具栏相关图标
    Icon_compete_data_process = 'config/Icon/total_toolbar_icon/compete_data_process.png'
    # 自定义控件相关图标
    Icon_custom_delete = 'config/Icon/custom_widget_icon/delete.png'
    Icon_custom_play = 'config/Icon/custom_widget_icon/play.png'
    Icon_custom_video_camera = 'config/Icon/custom_widget_icon/video_camera.png'
    Icon_custom_restore = 'config/Icon/custom_widget_icon/restore.png'
    Icon_custom_sleep = 'config/Icon/custom_widget_icon/sleep.png'
    Icon_custom_case = 'config/Icon/custom_widget_icon/case.png'
    Icon_tab_widget_new = 'config/Icon/tab_widget_icon/new.png'
    Icon_tab_widget_add = 'config/Icon/tab_widget_icon/add.png'
    Icon_tab_widget_delete = 'config/Icon/tab_widget_icon/delete.png'
    Icon_tab_widget_insert_above = 'config/Icon/tab_widget_icon/insert_above.png'
    Icon_tab_widget_insert_below = 'config/Icon/tab_widget_icon/insert_below.png'
    Icon_tab_widget_all_select = 'config/Icon/tab_widget_icon/all_select.png'
    Icon_tab_widget_all_un_select = 'config/Icon/tab_widget_icon/all_un_select.png'
    Icon_tab_widget_execute = 'config/Icon/tab_widget_icon/execute.png'
    Icon_tab_widget_stop = 'config/Icon/tab_widget_icon/stop.png'
    Icon_tab_widget_import = 'config/Icon/tab_widget_icon/import.png'
    Icon_tab_widget_save = 'config/Icon/tab_widget_icon/save.png'
    Icon_tab_widget_draw_frame = 'config/Icon/tab_widget_icon/draw_frame.png'
    Icon_tab_widget_switch_on = 'config/Icon/tab_widget_icon/switch_on.png'
    Icon_tab_widget_switch_off = 'config/Icon/tab_widget_icon/switch_off.png'
    # 视频和照片展示栏相关图标
    Icon_main_tab_widget_zoom_picture = 'config/Icon/main_tab_widget_icon/zoom.png'
    Icon_main_tab_widget_zoom_out_picture = 'config/Icon/main_tab_widget_icon/zoom_out.png'
    Icon_main_tab_widget_original_size_picture = 'config/Icon/main_tab_widget_icon/original_size.png'
    Icon_main_tab_widget_open_file = 'config/Icon/main_tab_widget_icon/open_file.png'
    Icon_main_tab_widget_edit_text = 'config/Icon/main_tab_widget_icon/edit_text.png'
    Icon_main_tab_widget_save_text = 'config/Icon/main_tab_widget_icon/save_text.png'
    Icon_main_tab_widget_close_tab = 'config/Icon/main_tab_widget_icon/close_tab.png'
    Icon_main_tab_widget_close_tab_hover = 'config/Icon/main_tab_widget_icon/close_tab_hover.png'
    # 逻辑相关图标
    Icon_logic_if = 'config/Icon/logic_control_icon/if.png'
    Icon_logic_then = 'config/Icon/logic_control_icon/then.png'
    Icon_logic_else = 'config/Icon/logic_control_icon/else.png'
    Icon_logic_end_if = 'config/Icon/logic_control_icon/end_if.png'
    # 循环相关图标
    Icon_loop_start = 'config/Icon/loop_control_icon/loop.png'
    Icon_loop_break = 'config/Icon/loop_control_icon/break.png'
    Icon_loop_end = 'config/Icon/loop_control_icon/end_loop.png'
    # 调用函数相关
    Icon_call_function_icon = 'config/Icon/call_function_control_icon/call_function.png'
    Icon_select_function_icon = 'config/Icon/call_function_control_icon/select_function.png'
    # adb相关
    Icon_adb = 'config/Icon/adb_control_icon/adb.png'
    # 切换目录树图标
    Icon_switch_tree = 'config/Icon/total_toolbar_icon/switch_tree.png'
    Icon_setting = 'config/Icon/total_toolbar_icon/setting.png'
    # case停止执行
    Icon_stop_execute = 'config/Icon/total_toolbar_icon/stop_execute.png'
    # 照片图标
    Icon_picture = 'config/Icon/other_icon/picture.png'


class RobotArmAction:
    # 机械臂动作类型(点击/双击/长按/滑动)
    uArm_action_type = None
    uArm_click = 'click'
    uArm_double_click = 'double_click'
    uArm_long_click = 'long_click'
    uArm_slide = 'slide'
    uArm_get_position = 'get_position'
    uArm_unlock = 'servo_detach'
    uArm_lock = 'servo_attach'
    # 机械臂是否操作同时脚本录制(False不录制脚本/True录制脚本)
    uArm_with_record = False


# 机械臂操作参数
class RobotArmParam:
    base_x_point = 0.0
    base_y_point = 0.0
    base_z_point = 0.0
    actual_screen_width = 0
    actual_screen_height = 0
    port_address = 'http://localhost:8000/'


class WindowStatus:
    # 机械臂('机械臂连接成功!' / '机械臂连接失败!')
    robot_connect_status = '机械臂未连接'
    # 视频帧率
    video_frame_rate = '120fps'
    # action_tab页面
    action_tab_status = '空白'
    # case_tab页面
    case_tab_status = '没有打开case目录'
    # 运行状态
    operating_status = '空闲状态/可以使用'


# action相关操作
class MotionAction:
    # 是否有添加动作
    add_action_flag = False
    # 添加动作子窗口的信息选项名称
    # 机械臂动作描述
    des_text = 'des_text'
    # 机械臂动作类型
    action_type = 'action_type'
    # 机械臂速度
    speed = 'speed'
    # 机械臂操作坐标
    points = 'points'
    # 机械臂收回
    leave = 'leave'
    # 相机录像触发标记(给视频打标记)
    trigger = 'trigger'


# 视频录制相关操作(如开关录像)
class RecordAction:
    record_status = 'record_status'
    record_start = 'record_start'
    record_stop = 'record_stop'
    video_type = 'video_type'
    video_name = 'video_name'
    standard_time = 'standard_time'
    # 保存开始录像的控件中的(type/name信息)
    current_video_type = '启动'
    current_video_name = 'name'
    current_standard_time = '800'


# 断言相关操作
class AssertAction:
    assert_template_name = 'assert_template_name'


# 恢复首页相关操作
class RestoreAction:
    restore_screen = 'restore_screen'


# 延时相关操作
class SleepAction:
    sleep_time = 'sleep_time'


# 逻辑相关
class LogicAction:
    logic_action = 'logic_action'
    logic_if = 'if'
    logic_then = 'then'
    logic_else = 'else'
    logic_end_if = 'end_if'


# 循环相关
class LoopAction:
    loop_action = 'loop_action'
    loop_start = 'loop_start'
    loop_end = 'loop_end'
    loop_num = 'loop_num'


# 跳出循环动作
class BreakAction:
    break_action = 'break_action'
    break_out = 'break'


# 调用函数功能
class CallFunctionAction:
    call_function = 'call_function'
    function_name = 'function_name'


# adb功能
class ADBAction:
    ADB = 'ADB'
    adb_desc = 'adb_desc'
    adb_command = 'adb_command'


# 配置文件的读取和写入
class Profile:
    def __init__(self, type=None, file=None, section=None, option=None, value=None):
        if type == 'read':
            self.value = self.get_config_value(file=file, section=section, option=option)
        if type == 'write':
            self.set_config_value(file=file, section=section, option=option, value=value)
        else:
            pass

    '''更改配置文件会去掉注释'''
    @staticmethod
    def get_config_value(file, section, option):
        config = configparser.ConfigParser()
        config.read(file, encoding='utf-8')
        value = config.get(section, option)
        return value

    # 设置config的参数
    @staticmethod
    def set_config_value(file, section, option, value):
        config = configparser.ConfigParser()
        config.read(file, encoding='utf-8')
        if section not in config.sections():
            config.add_section(section)
        config.set(section, option, str(value))
        with open(file, 'w+', encoding='utf-8') as cf:
            config.write(cf)

    # 获取节点options
    @staticmethod
    def get_config_options(file, section):
        config = configparser.ConfigParser()
        config.read(file, encoding='utf-8-sig')
        options = config.options(section)
        return options

    # '''修改配置文件会保留注释(增加可读性)'''
    # # 获取config的参数
    # def get_config_value(self, file, section, option):
    #     config_file = ConfigWithComment(file=file)
    #     value = config_file.read_config_value(section=section, option=option)
    #     return value
    #
    # # 设置config的参数
    # def set_config_value(self, file, section, option, value):
    #     config_file = ConfigWithComment(file=file)
    #     config_file.write_config_value(section=section, option=option, value=value)


# 自定义log对象
class Logger:
    def __init__(self, string):
        print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())) + ' >> -- ' + str(string))


# 合并路径(传入要合并的几个部分)
class MergePath:
    merged_path = None

    def __init__(self, section_path):
        path_list = []
        for section in section_path:
            if '\\\\' in section:
                section = section.replace('\\\\', '/')
            elif '\\' in section:
                section = section.replace('\\', '/')
            else:
                section = section
            path_list.append(section)
        merged_path = '/'.join(path_list)
        if '//' in merged_path:
            self.merged_path = merged_path.replace('//', '/')
        else:
            self.merged_path = merged_path


# 样式
class BeautifyStyle:
    font_family = 'font-family: Times New Roman;'
    font_size = 'font-size: 13pt;'
    file_dialog_qss = 'QFileDialog {background-color: beige;}'


# 共用函数
class Common:

    # 返回list为每个action的信息(字典形式)>>list第一个参数为case文件名, 后面参数为每个action的信息存储字典
    @staticmethod
    def read_script_tag(case_path):
        case_file = case_path
        try:
            tree = ET.ElementTree(file=case_file)
            root = tree.getroot()
            dict_list, new_dict_info = [], []
            for child_of_root in root:
                child_info_list = []
                if child_of_root.tag == 'action':
                    child_info_list.append(child_of_root.attrib)
                    for child_child_of_root in child_of_root:
                        dict_info = {child_child_of_root.attrib['name']: child_child_of_root.text}
                        child_info_list.append(dict_info)
                    dict_list.append(child_info_list)
            for info in dict_list:
                dict_buffer = {}
                for dict_info in info:
                    dict_buffer.update(dict_info)
                new_dict_info.append(dict_buffer)
            return new_dict_info
        except:
            file_name = os.path.split(case_file)[1]
            new_dict_info = [file_name, case_file]
            return new_dict_info

    # 给动作添加标识
    @staticmethod
    def add_action_mark(info_dict):
        # 判断是action控件
        if MotionAction.points in info_dict:
            # info_dict长度大于2为action控件
            # 将字典中的'(0, 0)'转为元祖(0, 0)
            points = info_dict['points']
            if isinstance(points, str):
                info_dict['points'] = eval(points)
            # 一个action字典中需要标明什么类型动作
            info_dict['execute_action'] = 'motion_action'
            info_dict['base'] = (RobotArmParam.base_x_point, RobotArmParam.base_y_point, RobotArmParam.base_z_point)
        # 为record或者sleep控件
        else:
            # 为record控件
            if RecordAction.record_status in info_dict:
                info_dict['execute_action'] = 'record_action'
                # 添加视频存放根目录
                info_dict['video_path'] = GloVar.project_video_path
            elif AssertAction.assert_template_name in info_dict:
                info_dict['execute_action'] = 'assert_action'
            elif RestoreAction.restore_screen in info_dict:
                info_dict['execute_action'] = 'restore_action'
            # 为sleep控件
            elif SleepAction.sleep_time in info_dict:
                info_dict['execute_action'] = 'sleep_action'
            # 为logic控件
            elif LogicAction.logic_action in info_dict:
                info_dict['execute_action'] = 'logic_action'
            # 为loop控件
            elif LoopAction.loop_action in info_dict:
                info_dict['execute_action'] = 'loop_action'
            # 为break控件
            elif BreakAction.break_action in info_dict:
                info_dict['execute_action'] = 'break_action'
            # 为call_function控件
            elif CallFunctionAction.function_name in info_dict:
                info_dict['execute_action'] = 'call_function_action'
            # 为adb控件
            elif ADBAction.adb_command in info_dict:
                info_dict['execute_action'] = 'adb_action'
        return info_dict

    # 断言操作需要用到的模板匹配
    @staticmethod
    def match_template(source_img, target_img):
        """
        :param source_img: 源图像(大图)
        :param target_img: 靶子图像(小图)
        :return:
        """
        if type(source_img) is str:
            source_img = cv2.imdecode(np.fromfile(source_img, dtype=np.uint8), -1)
        if type(target_img) is str:
            target_img = cv2.imdecode(np.fromfile(target_img, dtype=np.uint8), -1)
        # 匹配方法
        match_method = cv2.TM_CCOEFF_NORMED
        # 模板匹配
        match_result = cv2.matchTemplate(source_img, target_img, match_method)
        # 查找匹配度和坐标位置
        min_threshold, max_threshold, min_threshold_position, max_threshold_position = cv2.minMaxLoc(match_result)
        # 返回最大匹配率
        return max_threshold


    # 通过case名获取视频目录
    @staticmethod
    def get_video_folder_by_case(case_path):
        case_name = os.path.split(case_path)[1].split('.')[0]
        # 视频存放根目录
        root_folder = MergePath([GloVar.project_video_path, GloVar.current_time]).merged_path
        # 遍历视频目录下所有case目录(寻找当前case视频所在目录)
        video_folder = None
        for home, dirs, files in os.walk(root_folder):
            for _ in files:
                if case_name in home:
                    video_folder = MergePath([home]).merged_path
                    break
        # 数据处理
        if os.path.exists(video_folder) is False:
            video_folder = None
        return video_folder
