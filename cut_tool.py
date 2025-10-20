from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkinter import font as tkFont
import os
import cv2
import numpy as np
import sys
from pydub import AudioSegment
import subprocess
import webbrowser
import math
import datetime
import threading

#global variable
path = os.getcwd()
working_path = path + "\\working_folder\\"
                    
array_1 = []
array_2 = []

#constants

TEMP_FILENAME = "temp_list.txt"
TEMP_PREFIX = "out_"
FOURCC = cv2.VideoWriter_fourcc("m", "p", "4", "v")
DEFAULT_THREAD_NUM = 4
DEFAULT_IGNORE_FRAME_CNT = 0
SHOW_PROGRESS_SEG = 5

P_M_Y_CO = 0.074             #(right top) pause middle coefficient
P_M_X_CO = 0.112
P_L_X_CO = 0.125
M_P_M_Y_2_CO = 0.5           #this is the black point, other 3 are white point 
M_P_M_X_2_CO = 0.5           
M_P_L_Y_CO = 0.007           #middle pause
M_P_L_X_CO = 0.19
M_P_M_Y_CO = 0.043
M_P_R_Y_CO = 0.023
M_P_R_X_CO = 0.149

ACC_L_Y_CO = 0.095           #accelerate for lazy only
ACC_L_X_CO = 0.262
ACC_R_X_CO = 0.247

VP_Y_CO = 0.5       #valid pause
VP_X_1_CO = 0.046
VP_X_2_CO = 0.093
VP_X_3_CO = 0.139
VP_X_4_CO = 0.185

#disable following as new UI always work with first way of checking
#VP_2_Y_CO = 0.389   #second option to check valid pause
#VP_2_X_1_CO = 0.188 #wendi
#VP_2_X_2_CO = 0.197 #niaolong(mozu)
#VP_2_X_3_CO = 0.206 #m3
#VP_2_X_4_CO = 0.217 #panxie

WHITE_10 = np.array([240, 240, 240])
WHITE_9 = np.array([200, 200, 200])  # the number indicates the white level
GRAY = np.array([128, 128, 128])
BLACK_9 = np.array([30, 30, 30])
P_DIFF_TH = 10 # threshold
M_P_DIFF_TH = np.array([30, 30, 30]) # threshold
GRAY_LOWER = np.array([55, 55, 55])
GRAY_UPPER = np.array([130, 130, 130])

BLUE = 0
GREEN = 1
RED = 2
DARK_RED_TH = [20, 20, 90] # BGR <= <= >=
RED_RATIO_FOR_TOP_MARGIN = 0.3913
BLUE_TH = [130, 110, 50] # >= >= <=
BLUE_LOWER_PERC = 0.1
BLUE_UPPER_PERC = 0.25
LIGHT_GRAY_TH = [130, 130, 130]
LIGHT_GRAY_LOWER_PERC = 0.1
LIGHT_GRAY_UPPER_PERC = 0.25


MARGIN_TH = 500
    
def check_margin(top_margin, bottom_margin, left_margin, right_margin):
    if not (
        top_margin.replace("-", "").isdigit()
        and bottom_margin.replace("-", "").isdigit()
        and left_margin.replace("-", "").isdigit()
        and right_margin.replace("-", "").isdigit()
    ):
        messagebox.showerror(title="出错了！", message="边距参数有误（需整数）")
        return False
    if (
        int(top_margin) > MARGIN_TH
        or int(bottom_margin) > MARGIN_TH
        or int(left_margin) > MARGIN_TH
        or int(right_margin) > MARGIN_TH
    ):
        messagebox.showerror(title="出错了！", message="边距像素数过大，请重新设置")
        return False
    return True

def check_crop(top_margin, bottom_margin, left_margin, right_margin, video_name):
    if (
        int(top_margin) < 0
        or int(bottom_margin) < 0
        or int(left_margin) < 0
        or int(right_margin) < 0
    ):
        messagebox.showerror(title="出错了！", message="不能裁剪负数边距（剪暂停不影响）")
        return False
    if video_name == "aftercrop.mp4":
        messagebox.showerror(title="出错了！", message="裁剪文件名不能为aftercrop.mp4")
        return False
    if os.path.exists(path + "/" + video_name):
        messagebox.showerror(title="出错了！", message="上级目录已存在同文件名，请重命名")
        return False
    return True

def check_start_end_seconds(start_second, end_second):
    if not (start_second.isdigit() and end_second.isdigit()):
        messagebox.showerror(title="出错了！", message="开始结束秒数有误（需正整数）")
        return False
    if int(start_second) >= int(end_second):
        messagebox.showerror(title="出错了！", message="结束秒数必须大于开始秒数")
        return False
    return True

def check_file_and_return_path():
    file_cnt = 0
    working_folder_list = os.listdir(working_path)
    for lists in working_folder_list:
        file_cnt += 1
    if file_cnt == 1:
        if working_folder_list[0].startswith("out"):
            messagebox.showerror(title="出错了！", message="文件名不得以out开头，请重命名")
            return False
        return working_path + working_folder_list[0]
    messagebox.showerror(title="出错了！", message="工作目录下文件数必须为1")
    return False

def check_measure_margin_second(measure_margin_second):
    if not measure_margin_second.replace(".", "", 1).isdigit():
        messagebox.showerror(title="出错了！", message="检测边距秒数有误（需大于0的数字，接受小数）")
        return False
    return True
    
def check_set_second(set_second):
    if not set_second.replace(".", "", 1).isdigit():
        messagebox.showerror(title="出错了！", message="手动设置检测点画面秒数有误（需大于0的数字，接受小数）")
        return False
    return True  
    
def check_measure_margin_second_2(measure_margin_second, fps, frame_cnt):
    if measure_margin_second >= frame_cnt / fps:
        messagebox.showerror(title="出错了！", message="检测边距秒数必须小于视频长度")
        return False
    return True
    
def check_thread_num(thread_num):
    if not(thread_num.isdigit() and 1 <= int(thread_num) <= 16):        
        messagebox.showerror(title="出错了！", message="线程数必须为1~16的整数")
        return False
    return True
    
def check_ignore_frame_cnt(ignore_frame_cnt):
    if not(ignore_frame_cnt.isdigit()):        
        messagebox.showerror(title="出错了！", message="忽视帧数必须为>=0的整数")
        return False
    return True

def check_coordinates_setting():
    if not(len(array_1) == 4 and len(array_2) == 8):     
        messagebox.showerror(title="出错了！", message="未设置检测点")
        return False
    return True

def set_margin(top_margin, bottom_margin, left_margin, right_margin):
    e_top_margin.delete(0, END)
    e_bottom_margin.delete(0, END)
    e_left_margin.delete(0, END)
    e_right_margin.delete(0, END)
    e_top_margin.insert(0, top_margin)
    e_bottom_margin.insert(0, bottom_margin)
    e_left_margin.insert(0, left_margin)
    e_right_margin.insert(0, right_margin)      
    
def set_thread_num(thread_num):
    e_thread_num.delete(0, END)
    e_thread_num.insert(0, thread_num)    
    
def set_ignore_frame_cnt(ignore_frame_cnt):
    e_ignore_frame_cnt.delete(0, END)
    e_ignore_frame_cnt.insert(0, ignore_frame_cnt)    

def set_coordinates():
    if os.path.exists(path + "/检测点.txt"):
        f = open(path + "/检测点.txt")
        
        for i in range(4):
            coord = [int(f.readline()) , int(f.readline())]
            array_1.append(coord)
            
        for i in range(4):
            coord = [int(f.readline()) , int(f.readline())]
            array_2.append(coord)
        
        valid_pause_y = int(f.readline())
        
        for i in range(4):
            coord = [valid_pause_y , int(f.readline())]
            array_2.append(coord)
        
        set_coordinates_labels()        
        
        #print(array_1)
        #print(array_2)
        
        f.close()
   
def set_coordinates_labels():
    if len(array_1) == 4 and len(array_2) == 8:
        l_acc_right.config(text=str(array_1[0][0])+","+str(array_1[0][1]))
        l_acc_left.config(text=str(array_1[1][0])+","+str(array_1[1][1]))
        l_pause_middle.config(text=str(array_1[2][0])+","+str(array_1[2][1]))
        l_pause_left.config(text=str(array_1[3][0])+","+str(array_1[3][1]))
        l_middle_pause_left.config(text=str(array_2[0][0])+","+str(array_2[0][1]))
        l_middle_pause_middle_2.config(text=str(array_2[1][0])+","+str(array_2[1][1]))
        l_middle_pause_middle.config(text=str(array_2[2][0])+","+str(array_2[2][1]))
        l_middle_pause_right.config(text=str(array_2[3][0])+","+str(array_2[3][1]))
        l_valid_pause.config(text=str(array_2[4][0])+","+str(array_2[4][1])+","+str(array_2[5][1])+","+str(array_2[6][1])+","+str(array_2[7][1]))   
    else:
        l_acc_right.config(text="y,x")
        l_acc_left.config(text="y,x")
        l_pause_middle.config(text="y,x")
        l_pause_left.config(text="y,x")
        l_middle_pause_left.config(text="y,x")
        l_middle_pause_middle_2.config(text="y,x")
        l_middle_pause_middle.config(text="y,x")
        l_middle_pause_right.config(text="y,x")
        l_valid_pause.config(text="y,x1,x2,x3,x4")
 
def get_video_info(video_path):
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    lgt = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    hgt = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_cnt = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    return fps, lgt, hgt, frame_cnt  
    
def get_frame_cnt(video_path):
    cap = cv2.VideoCapture(video_path)
    frame_cnt = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    return frame_cnt  
    
def measure_margin(measure_margin_second):
    if check_measure_margin_second(measure_margin_second):
        video_path = check_file_and_return_path()
        if video_path:
            fps, lgt, hgt, frame_cnt = get_video_info(video_path)
            if check_measure_margin_second_2(
                float(measure_margin_second), fps, frame_cnt
            ):
                cap = cv2.VideoCapture(video_path)
                top_margin = MARGIN_TH
                bottom_margin = MARGIN_TH
                left_margin = MARGIN_TH
                right_margin = MARGIN_TH

                cap.set(
                    cv2.CAP_PROP_POS_FRAMES, int(fps * float(measure_margin_second))
                )
                ret, frame = cap.read()
                cap.release()

                flag = False
                red_cnt = 1
                for rgt_check in range(1, int(lgt / 2)):
                    for y in range(int(hgt / 2)):
                        x = lgt - rgt_check
                        if (
                            frame[y, x][RED] >= DARK_RED_TH[RED]
                            and frame[y, x][BLUE] <= DARK_RED_TH[BLUE]
                            and frame[y, x][GREEN] <= DARK_RED_TH[GREEN]
                        ):
                            right_margin = rgt_check - 1
                            first_y = y
                            y += 1
                            while (
                                frame[y, x][RED] >= DARK_RED_TH[RED]
                                and frame[y, x][BLUE] <= DARK_RED_TH[BLUE]
                                and frame[y, x][GREEN] <= DARK_RED_TH[GREEN]
                            ):
                                y += 1
                                red_cnt += 1
                            # print(red_cnt)
                            top_margin = int(
                                first_y - red_cnt * RED_RATIO_FOR_TOP_MARGIN
                            )

                            flag = True
                            break
                    if flag:
                        break

                for bot_check in range(1, int(hgt / 2)):
                    blue_cnt = 0
                    for x in range(lgt):
                        y = hgt - bot_check
                        if (
                            frame[y, x][BLUE] >= BLUE_TH[BLUE]
                            and frame[y, x][GREEN] >= BLUE_TH[GREEN]
                            and frame[y, x][RED] <= BLUE_TH[RED]
                        ):
                            blue_cnt += 1
                    if BLUE_LOWER_PERC < blue_cnt / lgt < BLUE_UPPER_PERC:
                        bottom_margin = bot_check - 1
                        break

                for x in range(int(lgt / 2)):
                    light_grey_cnt=0
                    for y in range(hgt):
                        if(frame[y,x][BLUE]>=LIGHT_GRAY_TH[BLUE] and frame[y,x][GREEN]>=LIGHT_GRAY_TH[GREEN] 
                                and frame[y,x][RED]>=LIGHT_GRAY_TH[RED]):
                            light_grey_cnt=light_grey_cnt+1
                        y=y+1
                    if LIGHT_GRAY_LOWER_PERC < light_grey_cnt/hgt < LIGHT_GRAY_UPPER_PERC:
                        left_margin=x
                        break
                    x=x+1          
                        

                if (
                    top_margin >= MARGIN_TH
                    or bottom_margin >= MARGIN_TH
                    or left_margin >= MARGIN_TH
                    or right_margin >= MARGIN_TH
                ):
                    messagebox.showerror(
                        title="出错了！", message="计算有误，请重新输入正确的检测边距秒数（显示编队的帧）"
                    )
                    return False
                set_margin(top_margin, bottom_margin, left_margin, right_margin)
                messagebox.showinfo(title="消息", message="边距已填充")
                return True
            else:
                return False

             
def cut_with_crop(mode, start_second, end_second, thread_num, measure_margin_second, ignore_frame_cnt):
    if check_ignore_frame_cnt(ignore_frame_cnt):
        if check_thread_num(thread_num):
            if check_start_end_seconds(start_second, end_second):
                if measure_margin(measure_margin_second):
                    if crop(                    
                        e_top_margin.get(),
                        e_bottom_margin.get(),
                        e_left_margin.get(),
                        e_right_margin.get(),
                    ):
                        if measure_margin(measure_margin_second):
                            cut_without_crop(
                                mode,  
                                e_top_margin.get(),
                                e_bottom_margin.get(),
                                e_left_margin.get(),
                                e_right_margin.get(),
                                start_second,
                                end_second,
                                thread_num,
                                ignore_frame_cnt
                            )

def crop(top_margin, bottom_margin, left_margin, right_margin):
    video_path = check_file_and_return_path()
    if video_path:
        if check_margin(top_margin, bottom_margin, left_margin, right_margin):
            orig_name = os.listdir(working_path)[0]
            if check_crop(
                top_margin, bottom_margin, left_margin, right_margin, orig_name
            ):
                cap = cv2.VideoCapture(video_path)
                lgt = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) 
                hgt = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) 
                cap.release()
                out = working_path + "aftercrop.mp4"
                if (lgt - int(left_margin) - int(right_margin)) % 2 == 1:
                    W = str(lgt - int(left_margin) - int(right_margin) + 1)
                else:
                    W = str(lgt - int(left_margin) - int(right_margin))
                if (hgt - int(top_margin) - int(bottom_margin)) % 2 == 1:
                    H = str(hgt - int(top_margin) - int(bottom_margin) + 1)
                else:                    
                    H = str(hgt - int(top_margin) - int(bottom_margin))
                X = left_margin
                Y = top_margin
                #print(X, Y, W, H)              
                
                tc = TimeCost()
                tc.time_start("裁剪")

                subprocess.call('ffmpeg -loglevel quiet -i "'
                    + video_path + '" -b:v 0 -vf crop=' 
                    + W + ':' + H + ':' + X + ':' + Y + ' '+out,shell = True)
                os.rename(video_path, "./" + orig_name)
                print("已完成，请在working_folder下查看裁剪后的aftercrop.mp4文件，原文件已移动至上级目录")
                
                tc.time_end()
                # set_margin(0, 0, 0, 0)
                # print("边距已重置为0")
                return True

def show_desc():
    b_show_desc.destroy()
    l3 = Label(win, text="懒人模式将会自动剪掉暂停\n并且加速1倍速的部分为2倍速", font=20, height=3, width=30)
    l3_2 = Label(win, text="适用于无需保留音效", font=20, width=30)
    l3_3 = Label(win, text="此模式只会生成1个文件", font=20)
    l4 = Label(win, text="正常模式将会自动分离暂停部分\n并且保留音效", font=20, height=3, width=30)
    l4_2 = Label(win, text="适用于需要保留音效\n（注：正常模式不支持mkv格式）", font=20, width=30)
    l4_3 = Label(win, text="此模式会生成较多文件", font=20)
    l3.grid(row=2)
    l3_2.grid(row=2, column=1)
    l3_3.grid(row=2, column=2)
    l4.grid(row=3)
    l4_2.grid(row=3, column=1)
    l4_3.grid(row=3, column=2)

def save_settings(mode_i, top_margin, bottom_margin, left_margin, right_margin, thread_num, ignore_frame_cnt):
    if check_thread_num(thread_num):
        if check_margin(top_margin, bottom_margin, left_margin, right_margin):
            f = open(path + "/设置.txt", "w+")
            f.write(str(mode_i) + "\n")
            f.write(top_margin + "\n")
            f.write(bottom_margin + "\n")
            f.write(left_margin + "\n")
            f.write(right_margin + "\n")
            f.write(thread_num + "\n")
            f.write(ignore_frame_cnt + "\n")
            f.close()
            messagebox.showinfo(title="消息", message="设置已保存")

def manual_set_save():
    if check_coordinates_setting():
        f = open(path + "/检测点.txt", "w+")
        f.write(str(array_1[0][0]) + "\n")
        f.write(str(array_1[0][1]) + "\n")
        f.write(str(array_1[1][0]) + "\n")
        f.write(str(array_1[1][1]) + "\n")
        f.write(str(array_1[2][0]) + "\n")
        f.write(str(array_1[2][1]) + "\n")
        f.write(str(array_1[3][0]) + "\n")
        f.write(str(array_1[3][1]) + "\n")
        f.write(str(array_2[0][0]) + "\n")
        f.write(str(array_2[0][1]) + "\n")
        f.write(str(array_2[1][0]) + "\n")
        f.write(str(array_2[1][1]) + "\n")
        f.write(str(array_2[2][0]) + "\n")
        f.write(str(array_2[2][1]) + "\n")
        f.write(str(array_2[3][0]) + "\n")
        f.write(str(array_2[3][1]) + "\n")
        f.write(str(array_2[4][0]) + "\n")
        f.write(str(array_2[4][1]) + "\n")
        f.write(str(array_2[5][1]) + "\n")
        f.write(str(array_2[6][1]) + "\n")
        f.write(str(array_2[7][1]) + "\n")
        f.close()
        messagebox.showinfo(title="消息", message="检测点坐标已保存")
        
def cut_without_crop(
    mode, top_margin, bottom_margin, left_margin, right_margin, start_second, end_second, thread_num, ignore_frame_cnt
):
    if e_manual_set_or_not.get() == "否" or check_coordinates_setting():
        if check_ignore_frame_cnt(ignore_frame_cnt):
            if check_thread_num(thread_num):
                if check_start_end_seconds(start_second, end_second):
                    video_path = check_file_and_return_path()
                    if video_path:
                        cap = cv2.VideoCapture(video_path)
                        frame_cnt = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        cap.release()
                        if check_margin(top_margin, bottom_margin, left_margin, right_margin):
                            if frame_cnt / int(fps) <= int(end_second):
                                messagebox.showerror(title="出错了！", message="结束秒数必须小于视频长度")
                            else:
                                if int(fps) != fps:  # warning only not error
                                    messagebox.showinfo(
                                        title="注意",
                                        message="视频帧数为非整数，可能会有剪辑问题，推荐使用其他软件重新导出为整数帧文件，点击确定或关闭窗口以继续",
                                    )
                                tc = TimeCost()
                                tc.time_start("全流程")
                                print(mode + "开始")
                                if mode == "懒人模式（保留有效暂停）" or mode == "懒人模式（暂停全剪）":
                                    lazy_version(
                                        video_path,
                                        mode,
                                        int(top_margin),
                                        int(bottom_margin),
                                        int(left_margin),
                                        int(right_margin),
                                        int(start_second),
                                        int(end_second),
                                        int(thread_num)
                                    )
                                    # already know these variables are int, thus cast here instead of inside
                                    print("已完成，请在working_folder下查看output.mp4文件")
                                else:  # normal mode otherwise
                                    normal_version(
                                        video_path,
                                        mode,
                                        int(top_margin),
                                        int(bottom_margin),
                                        int(left_margin),
                                        int(right_margin),
                                        int(start_second),
                                        int(end_second),
                                        int(thread_num)
                                    )
                                    print("已完成，请在working_folder下查看分离的mp4文件")
                                tc.time_end()

def jump_to_tutorial(event):
    webbrowser.open("https://www.bilibili.com/video/BV1qg411r7dV", new=0)


def set_coordinates_sample():
    img2 = cv2.imread('sample2.jpg')
    img = cv2.imread('sample1.jpg')
    if img2 is None or img is None:
        messagebox.showerror(title="出错了！", message="示例图不存在请重新下载")
    else:
        cv2.namedWindow("Sample_2", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Sample_2", (960,540))
        cv2.imshow('Sample_2', img2)
        
        cv2.namedWindow("Sample_1", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Sample_1", (960,540))
        cv2.imshow('Sample_1', img)

def set_coordinates_manually(set_second_1, set_second_2):
    array_1.clear()
    array_2.clear()
    if check_set_second(set_second_1):
        if check_set_second(set_second_2):
            video_path = check_file_and_return_path()
            if video_path:
                fps, lgt, hgt, frame_cnt = get_video_info(video_path)
                cap = cv2.VideoCapture(video_path)
                    
                cap.set(
                    cv2.CAP_PROP_POS_FRAMES, int(fps * float(set_second_1))
                )
                ret, frame = cap.read()
                
                if ret:
                    cv2.namedWindow("Frame_1", cv2.WINDOW_NORMAL)
                    messagebox.showinfo(title="消息", message="请参考示例图1按顺序点击以下4个点（红叉中心位置）：\n第一个点请点击右上角1倍速X正下方的三角形白色区域\n第二个点请点击右上角1倍速1正下方的灰色区域\n第三个点请点击右上角暂停正中的灰色区域\n第四个点请点击右上角暂停靠左的白色区域")
                    cv2.setWindowProperty("Frame_1", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
                    cv2.imshow('Frame_1', frame)
                    
                    cv2.setMouseCallback('Frame_1', mouse_callback_1, array_1) 
                    
                else:
                    messagebox.showerror(title="出错了！", message="画面读取失败")
                cv2.waitKey()
                if len(array_1) < 4:
                    messagebox.showerror(title="出错了！", message="未设置4个点请重新设置")
                    if cv2.getWindowProperty('Frame_1', cv2.WND_PROP_VISIBLE):
                        cv2.destroyWindow('Frame_1')
                else:  
                    cap.set(
                        cv2.CAP_PROP_POS_FRAMES, int(fps * float(set_second_2))
                    )
                    ret, frame = cap.read()
                    cap.release()
                    
                    if ret:
                        cv2.namedWindow("Frame_2", cv2.WINDOW_NORMAL)
                        messagebox.showinfo(title="消息", message="请参考示例图2按顺序点击以下8个点（红叉中心位置）：\n第一个点请点击中间P字母的T型连接处\n第二个点请点击中间U字母中间的灰色区域\n第三个点请点击中间U字母靠下的白色区域\n第四个点请点击中间E字母的T型连接处靠上的白色区域\n第五至第八个点请点击左侧技能二字上方的灰色条状（纵坐标必须与灰色条状持平 横坐标比较平均的点上就可以）")
                        cv2.setWindowProperty("Frame_2", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
                        cv2.imshow('Frame_2', frame)
                    
                        cv2.setMouseCallback('Frame_2', mouse_callback_2, array_2) 
                        
                    else:
                        messagebox.showerror(title="出错了！", message="画面读取失败")
                    cv2.waitKey()
                    if len(array_2) < 8:
                        messagebox.showerror(title="出错了！", message="未设置8个点请重新设置")
                        if cv2.getWindowProperty('Frame_2', cv2.WND_PROP_VISIBLE):
                            cv2.destroyWindow('Frame_2')                                                
                set_coordinates_labels()
                        
def mouse_callback_1(event, x, y, flags, param):
    if len(param) >= 4:
        cv2.destroyWindow('Frame_1')
    elif event == cv2.EVENT_LBUTTONDOWN:
        coord = [y, x]
        param.append(coord)
        #print(f"ROI selected: ({y},{x}) ")
        #print(param)
        
def mouse_callback_2(event, x, y, flags, param):
    if len(param) >= 8:
        cv2.destroyWindow('Frame_2')
    elif event == cv2.EVENT_LBUTTONDOWN:
        coord = [y, x]
        param.append(coord)
        #print(f"ROI selected: ({y},{x}) ")
        #print(param)
            
class PointCoordinates:
    def __init__(self):
        self.p_m_y, self.p_m_x = 0, 0
        self.p_l_y, self.p_l_x = 0, 0
        self.m_p_m_y_2, self.m_p_m_x_2 = 0, 0

        self.m_p_l_y, self.m_p_l_x = 0, 0
        self.m_p_m_y, self.m_p_m_x = 0, 0
        self.m_p_r_y, self.m_p_r_x = 0, 0

        self.acc_l_y, self.acc_l_x = 0, 0
        self.acc_r_y, self.acc_r_x = 0, 0

        self.vp_y, self.vp_x_1, self.vp_x_2, self.vp_x_3, self.vp_x_4 = 0, 0, 0, 0, 0
        # self.vp_2_y, self.vp_2_x_1, self.vp_2_x_2, self.vp_2_x_3, self.vp_2_x_4 = (
            # 0,
            # 0,
            # 0,
            # 0,
            # 0
        # )

    def calculate_or_use_coordinates(
        self, lgt, hgt, top_margin, bottom_margin, left_margin, right_margin
    ):
        if e_manual_set_or_not.get() == "是":
            self.acc_r_y = array_1[0][0]
            self.acc_r_x = array_1[0][1]
            self.acc_l_y = array_1[1][0]
            self.acc_l_x = array_1[1][1]
            self.p_m_y = array_1[2][0]
            self.p_m_x = array_1[2][1]
            self.p_l_y = array_1[3][0]
            self.p_l_x = array_1[3][1]
            self.m_p_l_y = array_2[0][0]
            self.m_p_l_x = array_2[0][1]
            self.m_p_m_y_2 = array_2[1][0]
            self.m_p_m_x_2 = array_2[1][1]
            self.m_p_m_y = array_2[2][0]
            self.m_p_m_x = array_2[2][1]
            self.m_p_r_y = array_2[3][0]
            self.m_p_r_x = array_2[3][1]
            self.vp_y = array_2[4][0]
            self.vp_x_1 = array_2[4][1]
            self.vp_x_2 = array_2[5][1]
            self.vp_x_3 = array_2[6][1]
            self.vp_x_4 = array_2[7][1]
        else:
            act_hgt = hgt - top_margin - bottom_margin
            act_lgt = lgt - left_margin - right_margin
            
            if act_lgt * 1080 < act_hgt * 1920:
                mdf_hgt = int(round(act_lgt / 1920 * 1080, 0))
            else:
                mdf_hgt = act_hgt

            self.p_m_y = int(round(P_M_Y_CO * mdf_hgt + top_margin, 0))
            self.p_m_x = int(round(lgt - P_M_X_CO * mdf_hgt - right_margin, 0))
            # right top || middle
            self.p_l_y = self.p_m_y
            self.p_l_x = int(round(lgt - P_L_X_CO * mdf_hgt - right_margin, 0))
            # right top || left

            self.m_p_m_y_2 = int(round(M_P_M_Y_2_CO * act_hgt + top_margin, 0))
            self.m_p_m_x_2 = int(
                round(M_P_M_X_2_CO * (lgt - left_margin - right_margin) + left_margin, 0)
            )
            # middle PAUSE point (black point)

            self.m_p_l_y = int(round(self.m_p_m_y_2 + M_P_L_Y_CO * mdf_hgt, 0))
            self.m_p_l_x = int(round(self.m_p_m_x_2 - M_P_L_X_CO * mdf_hgt, 0))
            # middle PAUSE left point (white point)
            self.m_p_m_y = int(round(self.m_p_m_y_2 + M_P_M_Y_CO * mdf_hgt, 0))
            self.m_p_m_x = self.m_p_m_x_2
            # middle PAUSE middle point (white point)
            self.m_p_r_y = int(round(self.m_p_m_y_2 - M_P_R_Y_CO * mdf_hgt, 0))
            self.m_p_r_x = int(round(self.m_p_m_x_2 + M_P_R_X_CO * mdf_hgt, 0))
            # middle PAUSE right point (white point)

            self.acc_l_y = int(round(ACC_L_Y_CO * mdf_hgt + top_margin, 0))
            self.acc_l_x = int(round(lgt - ACC_L_X_CO * mdf_hgt - right_margin, 0))
            self.acc_r_y = self.acc_l_y
            self.acc_r_x = int(round(lgt - ACC_R_X_CO * mdf_hgt - right_margin, 0))

            self.vp_y = int(round(VP_Y_CO * act_hgt + top_margin, 0))
            self.vp_x_1 = int(round(VP_X_1_CO * mdf_hgt + left_margin, 0))
            self.vp_x_2 = int(round(VP_X_2_CO * mdf_hgt + left_margin, 0))
            self.vp_x_3 = int(round(VP_X_3_CO * mdf_hgt + left_margin, 0))
            self.vp_x_4 = int(round(VP_X_4_CO * mdf_hgt + left_margin, 0))

            # self.vp_2_y = int(
                # round(VP_Y_CO * act_hgt + top_margin - (VP_Y_CO - VP_2_Y_CO) * mdf_hgt, 0)
            # )
            # self.vp_2_x_1 = int(round(VP_2_X_1_CO * mdf_hgt + left_margin, 0))
            # self.vp_2_x_2 = int(round(VP_2_X_2_CO * mdf_hgt + left_margin, 0))
            # self.vp_2_x_3 = int(round(VP_2_X_3_CO * mdf_hgt + left_margin, 0))
            # self.vp_2_x_4 = int(round(VP_2_X_4_CO * mdf_hgt + left_margin, 0))

            #print(self.p_m_y, self.p_m_x)
            #print(self.p_l_y, self.p_l_x)
            #print(self.m_p_m_y_2, self.m_p_m_x_2)
            #print(self.m_p_l_y, self.m_p_l_x)
            #print(self.m_p_m_y, self.m_p_m_x)
            #print(self.m_p_r_y, self.m_p_r_x)
            #print(self.acc_l_y, self.acc_l_x)
            #print(self.acc_r_y, self.acc_r_x)
            #print(self.vp_y, self.vp_x_1, self.vp_x_2, self.vp_x_3, self.vp_x_4)
            #print(self.vp_2_y, self.vp_2_x_1, self.vp_2_x_2, self.vp_2_x_3, self.vp_2_x_4)
        
        
def is_pause(frame, pc):
    if abs(
            float(sum(frame[pc.p_l_y, pc.p_l_x]) / len(frame[pc.p_l_y, pc.p_l_x]))
            - float(sum(frame[pc.p_m_y, pc.p_m_x]) / len(frame[pc.p_m_y, pc.p_m_x]))
            ) < P_DIFF_TH:
        return True
    white_points = [
        (pc.m_p_l_y, pc.m_p_l_x),
        (pc.m_p_m_y, pc.m_p_m_x),
        (pc.m_p_r_y, pc.m_p_r_x)
    ]
    if all(all(frame[y, x] > WHITE_10) for y, x in white_points):
        return True 
    if (
        all(frame[pc.m_p_m_y, pc.m_p_m_x] > GRAY)
        and all(abs(frame[pc.m_p_m_y, pc.m_p_m_x] - frame[pc.m_p_l_y, pc.m_p_l_x]) < M_P_DIFF_TH)
        and all(abs(frame[pc.m_p_m_y, pc.m_p_m_x] - frame[pc.m_p_r_y, pc.m_p_r_x]) < M_P_DIFF_TH)
        and all(abs(frame[pc.m_p_l_y, pc.m_p_l_x] - frame[pc.m_p_r_y, pc.m_p_r_x]) < M_P_DIFF_TH)
        and all(frame[pc.m_p_m_y_2, pc.m_p_m_x_2] < GRAY)
    ):
        return True
    return False

def is_acceleration(frame, pc):
    if all(frame[pc.acc_r_y, pc.acc_r_x] > WHITE_9) and any(
        frame[pc.acc_l_y, pc.acc_l_x] < WHITE_9
    ):
        return False
    return True

def is_valid_pause(frame, pc):
    if all(frame[pc.vp_y -5, pc.vp_x_1]  < BLACK_9):
        for dy in [0, -1, 1]:  # offset
            row = pc.vp_y  + dy 
            if (all(GRAY_LOWER <= frame[row, x])
                and all(frame[row, x] <= GRAY_UPPER) 
                for x in (pc.vp_x_1,  pc.vp_x_2,  pc.vp_x_3,  pc.vp_x_4)
            ):
                return True 
    #white_cols = (pc.vp_2_x_1,  pc.vp_2_x_2,  pc.vp_2_x_3,  pc.vp_2_x_4) 
    #return any(all(frame[pc.vp_2_y, col] > WHITE_10) for col in white_cols)

def expand_valid_pause_range(frame_cnt, pause_y_n, vp_y_n):
    for i in range(1, frame_cnt - 1):
        if vp_y_n[i] == True and vp_y_n[i - 1] == False and pause_y_n[i - 1] == True:
            a = i - 1
            while pause_y_n[a] == True and a >= 0:
                vp_y_n[a] = True
                a -= 1
        elif vp_y_n[i] == True and vp_y_n[i + 1] == False and pause_y_n[i + 1] == True:
            a = i + 1
            while pause_y_n[a] == True and a < frame_cnt:
                vp_y_n[a] = True
                a += 1
            i = a
            
def remove_ignore_frame_cnt_part(frame_cnt, keep_frame_y_n, vp_y_n):
    a = 0
    start = 0
    flag = 0 
    #flag 0 means keep frame_y_n = True, 1 means vp_y_n = True
    for i in range(1, frame_cnt - 1):
        if keep_frame_y_n[i] == True:
            if flag == 0:
                a += 1
            else:
                if a <= int(e_ignore_frame_cnt.get()):
                    for j in range(start, i - 1):
                        vp_y_n[j] = False
                a = 0
                start = i
                flag = 0
        elif vp_y_n[i] == True:
            if flag == 1:
                a += 1
            else:
                if a <= int(e_ignore_frame_cnt.get()):
                    for j in range(start, i - 1):
                        keep_frame_y_n[j] = False
                a = 0
                start = i
                flag = 1

def print_progress(i, start, end, start_message, end_message):
    if i == start:
        print(start_message)
    elif i == end:
        print(end_message)
    elif (
        (i - start) % ((end - start) / SHOW_PROGRESS_SEG) < 1 and i > start and i < end
    ):
        print(f"{(i - start) / (end - start):.0%}")

def get_file_suffix(vp_value, pause_value):
    if vp_value == True:
        return "有效暂停"
    elif pause_value == True:
        return "无效暂停"
    else:
        return ""

def cleanup(working_path):
    tc = TimeCost()
    tc.time_start("清理片段")    
    for root, dirs, files in os.walk(working_path):
        for name in files:
            if name.startswith(TEMP_PREFIX):
                os.remove(os.path.join(root, name))
            elif get_frame_cnt(os.path.join(root, name)) <= int(e_ignore_frame_cnt.get()):
                os.remove(os.path.join(root, name))
                print("片段 " + name + " 小于等于忽视帧数，已删除")
    tc.time_end()  


def update_entry_state(event):
    if e_manual_set_or_not.get() == "是":
        e_top_margin.config(state="disable")
        e_bottom_margin.config(state="disable")
        e_left_margin.config(state="disable")
        e_right_margin.config(state="disabled")
        b_save_settings.config(state="disabled")
        e_measure_margin_second.config(state="disabled")
        b_measure_margin.config(state="disabled")
        b_crop.config(state="disabled")
        b_cut_with_crop.config(state="disabled")
        e_manual_set_second_1.config(state="normal")
        e_manual_set_second_2.config(state="normal")
        b_manual_set.config(state="normal")
        b_manual_set_sample.config(state="normal")
        b_manual_set_save.config(state="normal")  
    else:
        e_top_margin.config(state="normal")
        e_bottom_margin.config(state="normal")
        e_left_margin.config(state="normal")
        e_right_margin.config(state="normal")
        b_save_settings.config(state="normal")
        e_measure_margin_second.config(state="normal")
        b_measure_margin.config(state="normal")
        b_crop.config(state="normal")
        b_cut_with_crop.config(state="normal")
        e_manual_set_second_1.config(state="disabled")
        e_manual_set_second_2.config(state="disabled")
        b_manual_set.config(state="disabled")
        b_manual_set_sample.config(state="disabled")  
        b_manual_set_save.config(state="disabled")  

class TimeCost:
    def __init__(self):
        self.start = datetime
        self.end = datetime

    def time_start(self, process_name):
        self.start = datetime.datetime.now()
        print("    为 " + process_name + " 计时")
        print("    计时开始于 " + str(self.start))

    def time_end(self):
        self.end = datetime.datetime.now()
        print("    计时结束于 " + str(self.end))
        print("        用时 " + str(self.end - self.start))


def lazy_pause_analyze(
    process_num, start_f, end_f, start, end, cap, pc, pause_y_n, vp_y_n, keep_frame_y_n
):   
    cap.set(cv2.CAP_PROP_POS_FRAMES, start)
    skip = True
    for i in range(start, end + 1):
        if i <= end_f:
            ret, frame = cap.read()
        if i < start_f or i > end_f:
            keep_frame_y_n[i] = True
        else:
            # try: 
               # is_pause(frame, pc)
            # except Exception as e:
                # print(frame[pc.p_l_y, pc.p_l_x])
                # if os.path.exists(path + "/log.txt"):
                    # f = open(path + "/log.txt", "a")                  
                    # f.write("error frame is " + str(i) + "\n")
                    # f.close()
            # else:
            if not is_pause(frame, pc):
                if not is_acceleration(frame, pc):
                    if skip:
                        skip = False
                    else:
                        skip = True
                        keep_frame_y_n[i] = True
                else:
                    keep_frame_y_n[i] = True
            else:
                pause_y_n[i] = True
                if is_valid_pause(frame, pc):
                    vp_y_n[i] = True
        print_progress(
            i,
            start,
            end,
            "线程" + str(process_num) + ":开始分析暂停位置",
            "线程" + str(process_num) + "：100%",
        )
    cap.release()

def lazy_video_generate(
    process_num, start, end, cap, keep_frame_y_n, vp_y_n, fps, lgt, hgt
):
    size = (lgt, hgt)  
    out = cv2.VideoWriter(
        working_path + TEMP_PREFIX + str(process_num) + ".mp4", FOURCC, fps, size
    )
    cap.set(cv2.CAP_PROP_POS_FRAMES, start)
    for i in range(start, end):
        ret, frame = cap.read()
        if keep_frame_y_n[i] == True or vp_y_n[i] == True:
            out.write(frame)
        print_progress(
            i,
            start,
            end - 1,
            "线程" + str(process_num) + "：开始剪掉暂停及加速",
            "线程" + str(process_num) + "：100%",
        )

    out.release()
    # print("线程" + str(process_num) + "生成了文件 out_" + str(index) + vp + ".mp4")
    cap.release()

def lazy_video_generate_2(
    process_num, start_f, end_f, start, end, cap, pc, fps, lgt, hgt
):
    size = (lgt, hgt)
    out = cv2.VideoWriter(
        working_path + TEMP_PREFIX + str(process_num) + ".mp4", FOURCC, fps, size
    )
    cap.set(cv2.CAP_PROP_POS_FRAMES, start)
    skip = True
    for i in range(start, end):
        ret, frame = cap.read()
        if i < start_f or i > end_f:
            out.write(frame)
        else:
            if not is_pause(frame, pc):
                if not is_acceleration(frame, pc):
                    if skip:
                        skip = False
                    else:
                        skip = True
                        out.write(frame)
                else:
                    out.write(frame)
            print_progress(
                i,
                start,
                end - 1,
                "线程" + str(process_num) + "：开始剪掉暂停及加速",
                "线程" + str(process_num) + "：100%",
            )
    out.release()
    cap.release()

def lazy_version(
    video_path,
    mode,
    top_margin,
    bottom_margin,
    left_margin,
    right_margin,
    start_second,
    end_second,
    thread_num
):
    fps, lgt, hgt, frame_cnt = get_video_info(video_path)

    start_f = start_second * fps  # start frame (will keep frames before this)
    end_f = end_second * fps  # end frame   (will keep frames after this)

    pc = PointCoordinates()
    pc.calculate_or_use_coordinates(
        lgt, hgt, top_margin, bottom_margin, left_margin, right_margin
    )

    pause_y_n = np.full(frame_cnt, False)  # True means a pause, False means not a pause
    vp_y_n = np.full(frame_cnt, False)
    keep_frame_y_n = np.full(frame_cnt, False)  # True means keep, False means no keep
    frame_per_thread = math.floor(frame_cnt / thread_num)

    tc = TimeCost()

    if mode == "懒人模式（保留有效暂停）":
        tc.time_start("分析暂停")

        threads = []

        for t in range(thread_num):
            cap_t = cv2.VideoCapture(video_path)

            start = t * frame_per_thread
            end = (t + 1) * frame_per_thread - 1
            
            #print("start is", start, ", end is ", end)
            
            thread = threading.Thread(
                target=lazy_pause_analyze,
                args=(
                    t,
                    start_f,
                    end_f,
                    start,
                    end,
                    cap_t,
                    pc,
                    pause_y_n,
                    vp_y_n,
                    keep_frame_y_n,
                )
            )

            threads.append(thread)
            thread.start()

        for t in threads:
            t.join()

        expand_valid_pause_range(frame_cnt, pause_y_n, vp_y_n)
        
        # for i in range(2760, len(keep_frame_y_n)):
            # print("i is ", i, ", keep is ", keep_frame_y_n[i])
        
        if int(e_ignore_frame_cnt.get()) > 0:
            remove_ignore_frame_cnt_part(frame_cnt, keep_frame_y_n, vp_y_n)
        
        
        tc.time_end()

        tc.time_start("生成视频")

        threads = []

        for t in range(thread_num):
            cap_t = cv2.VideoCapture(video_path)

            start = t * frame_per_thread
            end = (t + 1) * frame_per_thread if t != thread_num - 1 else frame_cnt

            thread = threading.Thread(
                target=lazy_video_generate,
                args=(t, start, end, cap_t, keep_frame_y_n, vp_y_n, fps, lgt, hgt)
            )
            threads.append(thread)
            thread.start()

            f = open(working_path + TEMP_FILENAME, "a")
            f.write("file " + TEMP_PREFIX + str(t) + ".mp4" + "\n")

        f.close()

        for t in threads:
            t.join()

        tc.time_end()

    elif mode == "懒人模式（暂停全剪）":
        tc.time_start("生成视频")

        threads = []

        for t in range(thread_num):
            cap_t = cv2.VideoCapture(video_path)

            start = t * frame_per_thread
            end = (t + 1) * frame_per_thread 

            thread = threading.Thread(
                target=lazy_video_generate_2,
                args=(t, start_f, end_f, start, end, cap_t, pc, fps, lgt, hgt)
            )
            threads.append(thread)
            thread.start()

            f = open(working_path + TEMP_FILENAME, "a")
            f.write("file " + TEMP_PREFIX + str(t) + ".mp4" + "\n")

        f.close()

        for t in threads:
            t.join()

        tc.time_end()

    #cleanup below
    subprocess.call(
        "ffmpeg -loglevel quiet -f concat -safe 0 -i "
        + working_path
        + TEMP_FILENAME
        + " -c copy "
        + working_path
        + "output.mp4",
        shell=True,
    )

    os.remove(working_path + TEMP_FILENAME)
    
    cleanup(working_path)
        

def normal_get_video_audio_bounds(frame_cnt, frame_per_thread, pause_y_n, thread_num):
    bounds = [0]
    seg_cnts = [0]
    seg_cnt = 0
    check = False
    for i in range(1, frame_cnt):
        if len(bounds) == thread_num:
            break
        if pause_y_n[i] != pause_y_n[i - 1]:
            seg_cnt += 1
        if pause_y_n[i] == pause_y_n[i - 1] and i >= frame_per_thread * len(bounds):
            check = True
        elif check and pause_y_n[i] != pause_y_n[i - 1]:
            bounds += [i]
            check = False
            seg_cnts += [seg_cnt]
    return bounds, seg_cnts

def normal_pause_analyze(
    process_num, start_f, end_f, start, end, cap, pc, pause_y_n, vp_y_n
):
    if end_f < start or end < start_f:
        print("开始结束秒数与被分配区间没有交集，线程" + str(process_num) + "未启动" 
            + "\n请尽量只将需要剪辑的部分放入使用")
    else:
        if start < start_f:
            start = start_f
        cap.set(cv2.CAP_PROP_POS_FRAMES, start)
        for i in range(start, end + 1):
            if i <= end_f:
                ret, frame = cap.read()
            if i >= start_f and i <= end:
                if is_pause(frame, pc):
                    pause_y_n[i] = True
                    if is_valid_pause(frame, pc):
                        vp_y_n[i] = True
                print_progress(
                    i,
                    start,
                    end,
                    "线程" + str(process_num) + "：开始分析暂停位置",
                    "线程" + str(process_num) + "：100%",
                )
        cap.release()

def normal_video_generate(
    process_num, start_index, start, end, cap, pause_y_n, vp_y_n, fps, lgt, hgt
):
    size = (lgt, hgt) 
    index = start_index
    vp = get_file_suffix(vp_y_n[start], pause_y_n[start])
    out = cv2.VideoWriter(
        working_path + TEMP_PREFIX + str(index) + vp + ".mp4", FOURCC, fps, size
    )
    cap.set(cv2.CAP_PROP_POS_FRAMES, start)
    ret, frame = cap.read()
    out.write(frame)
    for i in range(start + 1, end):
        ret, frame = cap.read()
        if pause_y_n[i] != pause_y_n[i - 1]:
            out.release()
            # print("线程" + str(process_num) + "生成了文件 out_" + str(index) + vp + ".mp4")
            index += 1
            vp = get_file_suffix(vp_y_n[i], pause_y_n[i])
            out = cv2.VideoWriter(
                working_path + TEMP_PREFIX + str(index) + vp + ".mp4", FOURCC, fps, size
            )
        out.write(frame)
        print_progress(
            i,
            start + 1,
            end - 1,
            "线程" + str(process_num) + "：开始生成视频片段",
            "线程" + str(process_num) + "：100%",
        )

    out.release()
    # print("线程" + str(process_num) + "生成了文件 out_" + str(index) + vp + ".mp4")
    cap.release()

def normal_audio_generate(
    process_num, start_index, start, end, sound, pause_y_n, vp_y_n, fps
):
    start_seg = start
    inc = 1 / fps * 1000
    index = start_index
    vp = get_file_suffix(vp_y_n[start], pause_y_n[start])

    for i in range(start + 1, end):
        if pause_y_n[i] != pause_y_n[i - 1]:
            out_a = sound[start_seg * inc : i * inc + fps]
            # print("start is ", start_seg * inc, ", end is ", i * inc + fps)
            out_a.export(working_path + TEMP_PREFIX + str(index) + vp + ".mp3")
            # print("线程" + str(process_num) + "生成了文件 out_" + str(index) + vp + ".mp3")
            vp = get_file_suffix(vp_y_n[i], pause_y_n[i])
            index += 1
            start_seg = i
    out_a = sound[start_seg * inc : i * inc + fps]
    # print("start is ", start_seg * inc, ", end is ", i * inc + fps)
    out_a.export(working_path + TEMP_PREFIX + str(index) + vp + ".mp3")
    # print("线程" + str(process_num) + "生成了文件 out_" + str(index) + vp + ".mp3")

def normal_combine(process_num, prefix, start, end, has_sound, mode):
    for i in range(start, end):
        j = prefix + i
        old_name = working_path + TEMP_PREFIX + str(i)
        new_name = working_path + str(j)
        if has_sound:
            subprocess.call(
                "ffmpeg -loglevel quiet -i "
                + old_name
                + ".mp4"
                + " -i "
                + old_name
                + ".mp3"
                + " -c:v copy -c:a aac "
                + new_name
                + ".mp4",
                shell=True,
            )
            subprocess.call(
                "ffmpeg -loglevel quiet -i "
                + old_name
                + "有效暂停.mp4"
                + " -i "
                + old_name
                + "有效暂停.mp3"
                + " -c:v copy -c:a aac "
                + new_name
                + "有效暂停.mp4",
                shell=True,
            )
            if mode == "正常模式（保留无效暂停视频）":
                subprocess.call(
                    "ffmpeg -loglevel quiet -i "
                    + old_name
                    + "无效暂停.mp4"
                    + " -i "
                    + old_name
                    + "无效暂停.mp3"
                    + " -c:v copy -c:a aac "
                    + new_name
                    + "无效暂停.mp4",
                    shell=True,
                )
            else:
                try:
                    os.rename(                        
                        old_name + "无效暂停.mp3",
                        new_name + "无效暂停.mp3",
                    )
                except:
                    dummy = 0
            print_progress(
                i,
                start,
                end - 1,
                "线程" + str(process_num) + "：开始合并音频视频片段",
                "线程" + str(process_num) + ":100%",
            )
            i = i + 1
        else:
            try:
                os.rename(
                    old_name + ".mp4",
                    new_name + ".mp4",
                )
            except:
                dummy = 0
            try:
                os.rename(
                    old_name + "有效暂停.mp4",
                    new_name + "有效暂停.mp4",
                )
            except:
                dummy = 0
            if mode == "正常模式（保留无效暂停视频）":
                try:
                    os.rename(
                        old_name + "无效暂停.mp4",
                        new_name + "无效暂停.mp4",
                    )
                except:
                    dummy = 0
            print_progress(
                i,
                start,
                end - 1,
                "线程" + str(process_num) + "：视频未检测出音频，仅重命名",
                "线程" + str(process_num) + ":100%",
            )



def normal_version(
    video_path,
    mode,
    top_margin,
    bottom_margin,
    left_margin,
    right_margin,
    start_second,
    end_second,
    thread_num
):
    fps, lgt, hgt, frame_cnt = get_video_info(video_path)

    start_f = start_second * fps  # start frame (will keep frames before this)
    end_f = end_second * fps  # end frame   (will keep frames after this)

    pc = PointCoordinates()
    pc.calculate_or_use_coordinates(
        lgt, hgt, top_margin, bottom_margin, left_margin, right_margin
    )

    pause_y_n = np.full(frame_cnt, False)  # True means a pause, False means not a pause
    vp_y_n = np.full(frame_cnt, False)

    tc = TimeCost()

    tc.time_start("分析暂停")

    threads = []
    frame_per_thread = math.floor(frame_cnt / thread_num)
    
    for t in range(thread_num):
        # 创建独立VideoCapture对象避免资源冲突
        cap_t = cv2.VideoCapture(video_path)

        # 计算每个线程的帧范围
        start = t * frame_per_thread if t != 0 else start_f
        end = (t + 1) * frame_per_thread - 1 if t != thread_num - 1 else end_f

        # 创建线程
        thread = threading.Thread(
            target=normal_pause_analyze,
            args=(t, start_f, end_f, start, end, cap_t, pc, pause_y_n, vp_y_n)
        )

        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for t in threads:
        t.join()

    expand_valid_pause_range(frame_cnt, pause_y_n, vp_y_n)
    
    tc.time_end()

    tc.time_start("生成视频片段")

    bounds, seg_cnts = normal_get_video_audio_bounds(
        frame_cnt, frame_per_thread, pause_y_n, thread_num
    )
    # print ("bounds are ", bounds)
    # print ("seg_cnts are ", seg_cnts)
    
    threads = []

    for t in range(len(bounds)):
        cap_t = cv2.VideoCapture(video_path)

        start = bounds[t]
        end = bounds[t + 1] if t != len(bounds) - 1 else frame_cnt
        start_index = seg_cnts[t]

        thread = threading.Thread(
            target=normal_video_generate,
            args=(t, start_index, start, end, cap_t, pause_y_n, vp_y_n, fps, lgt, hgt)
        )
        # print("args are ", t, start_index, start, end)
        threads.append(thread)
        thread.start()

    for t in threads:
        t.join()

    tc.time_end()

    has_sound = True
    try:
        sound = AudioSegment.from_file(
            video_path, format=os.path.splitext(video_path)[-1].split(".")[1]
        )
    except:
        has_sound = False

    if has_sound:
        tc.time_start("生成音频片段")

        threads = []

        for t in range(len(bounds)):
            start = bounds[t]
            end = bounds[t + 1] if t != len(bounds) - 1 else frame_cnt
            start_index = seg_cnts[t]

            thread = threading.Thread(
                target=normal_audio_generate,
                args=(t, start_index, start, end, sound, pause_y_n, vp_y_n, fps)
            )
            threads.append(thread)
            thread.start()

        for t in threads:
            t.join()

        tc.time_end()

    working_folder_list = os.listdir(working_path)

    if has_sound:
        count = int((len(working_folder_list) - 1) / 2)
    else:
        count = len(working_folder_list) - 1

    tc.time_start("合并视频音频")

    threads = []
    file_per_thread = math.floor(count / thread_num)

    for t in range(thread_num):

        start = t * file_per_thread
        end = (t + 1) * file_per_thread if t != thread_num - 1 else count
        prefix = pow(10, len(str(count)))

        thread = threading.Thread(
            target=normal_combine, args=(t, prefix, start, end, has_sound, mode)
        )

        threads.append(thread)
        thread.start()

    for t in threads:
        t.join()

    tc.time_end()

    cleanup(working_path)
    
# main here
win = Tk()
win.title("明日方舟自动分离/剪掉暂停")

win.geometry(str(1300 + len(path.encode("utf-8")) * 5) + "x900")

l_text_working_path = Label(win, text="当前工作目录", font=20, height=3)
l_working_path = Label(win, text=working_path, bg="lightgray", font=20, height=3)

l_mode = Label(win, text="选择模式", font=20, height=3)
e_mode = ttk.Combobox(win, font=20, height=4, width=28)
e_mode["value"] = ("正常模式（仅保留无效暂停音效）", "正常模式（保留无效暂停视频）", "懒人模式（保留有效暂停）", "懒人模式（暂停全剪）")
win.option_add("*TCombobox*Listbox.font", 20)
e_mode.current(1)  # give default
b_show_desc = Button(win, text="显示说明", command=show_desc, font=20)

l_top_margin = Label(win, text="上边距（像素数）", font=20, height=2)
e_top_margin = Entry(win, bg="white", font=20)

l_bottom_margin = Label(win, text="下边距", font=20, height=2)
e_bottom_margin = Entry(win, bg="white", font=20)

l_left_margin = Label(win, text="左边距", font=20, height=2)
e_left_margin = Entry(win, bg="white", font=20)

l_right_margin = Label(win, text="右边距", font=20, height=2)
e_right_margin = Entry(win, bg="white", font=20)

set_margin(0, 0, 0, 0)

l_thread_num = Label(win, text="线程数", font=20, height=2)
e_thread_num = Entry(win, bg="white", font=20)

e_thread_num.insert(0, DEFAULT_THREAD_NUM)

l_ignore_frame_cnt = Label(win, text="忽视小于等于该帧数的片段", font=20, height=2)
e_ignore_frame_cnt = Entry(win, bg="white", font=20)

e_ignore_frame_cnt.insert(0, DEFAULT_IGNORE_FRAME_CNT)

b_save_settings = Button(
    win,
    text="保存设置",
    command=lambda: save_settings(
        e_mode.current(),
        e_top_margin.get(),
        e_bottom_margin.get(),
        e_left_margin.get(),
        e_right_margin.get(),
        e_thread_num.get(),
        e_ignore_frame_cnt.get()
    ),
    font=20
)

l_measure_margin_second = Label(win, text="检测边距秒数（支持小数）", font=20, height=2)
e_measure_margin_second = Entry(win, bg="white", font=20)

b_measure_margin = Button(
    win,
    text="检测边距",
    command=lambda: measure_margin(e_measure_margin_second.get()),
    font=20
)
b_crop = Button(
    win,
    text="按边距裁剪（边距将被重置为0）",
    command=lambda: crop(
        e_top_margin.get(),
        e_bottom_margin.get(),
        e_left_margin.get(),
        e_right_margin.get()
    ),
    font=20
)

b_cut_without_crop = Button(
    win,
    text="点击开始自动分离/剪掉暂停（不包含边距裁剪）",
    command=lambda: cut_without_crop(
        e_mode.get(),
        e_top_margin.get(),
        e_bottom_margin.get(),
        e_left_margin.get(),
        e_right_margin.get(),
        e_start_second.get(),
        e_end_second.get(),
        e_thread_num.get(),
        e_ignore_frame_cnt.get()
    ),
    font=20
)
b_cut_with_crop = Button(
    win,
    text="点击开始自动分离/剪掉暂停（包含边距裁剪）",
    command=lambda: cut_with_crop(
        e_mode.get(),
        e_start_second.get(), 
        e_end_second.get(),
        e_thread_num.get(),
        e_measure_margin_second.get(),
        e_ignore_frame_cnt.get()
    ),
    font=20
)

l_tutorial = Label(win, text="详细操作教程：", font=20, height=2)

ft = tkFont.Font(family="Fixdsys", size=11, weight=tkFont.NORMAL, underline=1)
l_tutorial_url = Label(
    win, text="www.bilibili.com/video/BV1qg411r7dV", font=ft, fg="blue", height=2
)
l_tutorial_url.bind("<ButtonPress-1>", jump_to_tutorial)


l_start_second = Label(win, text="开始秒数", font=20, height=2)
e_start_second = Entry(win, bg="white", font=20)

l_end_second = Label(win, text="结束秒数", font=20, height=2)
e_end_second = Entry(win, bg="white", font=20)




l_manual_set_second = Label(win, text="手动设置检测点画面秒数（支持小数）", font=20, height=2)
e_manual_set_second_1 = Entry(win, bg="white", font=20, width=10)
e_manual_set_second_2 = Entry(win, bg="white", font=20, width=10)
b_manual_set = Button(
    win,
    text="手动设置",
    command=lambda: set_coordinates_manually(e_manual_set_second_1.get(),e_manual_set_second_2.get()),
    font=20
)
b_manual_set_sample = Button(
    win,
    text="设置示例图",
    command=lambda: set_coordinates_sample(),
    font=20
)
b_manual_set_save = Button(
    win,
    text="保存检测点",
    command=lambda: manual_set_save(),
    font=20
)
l_pause_middle = Label(win, text="y,x", font=20, height=2)
l_pause_left = Label(win, text="y,x", font=20, height=2) 

l_frame_desc = Label(win, text="请参考示例图", font=20, height=2)
l_frame_1_desc = Label(win, text="前者秒数为1倍速无暂停画面", font=20, height=2)
l_frame_2_desc = Label(win, text="后者秒数为有效暂停画面", font=20, height=2)
 
l_acc_left = Label(win, text="y,x", font=20, height=2)
l_acc_right = Label(win, text="y,x", font=20, height=2)

l_middle_pause_middle_2 = Label(win, text="y,x", font=20, height=2)
l_middle_pause_left = Label(win, text="y,x", font=20, height=2)
l_middle_pause_middle = Label(win, text="y,x", font=20, height=2)
l_middle_pause_right = Label(win, text="y,x", font=20, height=2)

l_valid_pause = Label(win, text="y,x1,x2,x3,x4", font=20, height=2)
#l_valid_pause_2 = Label(win, text="y,x1,x2,x3,x4", font=20, height=2)

l_manual_set_or_not = Label(win, text="是否手动设置检测点", font=20, height=3)

e_manual_set_or_not = ttk.Combobox(win, values=["否","是"], font=20, height=4, width=10)
e_manual_set_or_not.current(0)
e_manual_set_second_1.config(state="disabled")
e_manual_set_second_2.config(state="disabled")
b_manual_set.config(state="disabled")
b_manual_set_sample.config(state="disabled")  
b_manual_set_save.config(state="disabled")  
e_manual_set_or_not.bind("<<ComboboxSelected>>", update_entry_state)

l_text_working_path.grid(row=0)
l_working_path.grid(row=0, column=1)
l_mode.grid(row=1)
e_mode.grid(row=1, column=1)
b_show_desc.grid(row=1, column=2)

l_top_margin.grid(row=4)
e_top_margin.grid(row=4, column=1)
l_bottom_margin.grid(row=5)
e_bottom_margin.grid(row=5, column=1)
l_left_margin.grid(row=6)
e_left_margin.grid(row=6, column=1)
l_right_margin.grid(row=7)
e_right_margin.grid(row=7, column=1)

l_thread_num.grid(row=8)
e_thread_num.grid(row=8, column=1)

l_ignore_frame_cnt.grid(row=9)
e_ignore_frame_cnt.grid(row=9, column=1)

b_save_settings.grid(row=10)

l_measure_margin_second.grid(row=11)
e_measure_margin_second.grid(row=11, column=1)
b_measure_margin.grid(row=12)
b_crop.grid(row=12, column=1)

l_start_second.grid(row=13)
e_start_second.grid(row=13, column=1)
l_end_second.grid(row=14)
e_end_second.grid(row=14, column=1)

b_cut_without_crop.grid(row=15, column=0)
b_cut_with_crop.grid(row=15, column=1)
l_tutorial.grid(row=16, column=0)
l_tutorial_url.grid(row=16, column=1)

l_manual_set_or_not.grid(row=4, column=2)
e_manual_set_or_not.grid(row=4, column=3)
l_manual_set_second.grid(row=5, column=2)
e_manual_set_second_1.grid(row=5, column=3)
e_manual_set_second_2.grid(row=5, column=4)
b_manual_set.grid(row=6, column=2)
b_manual_set_sample.grid(row=6, column=3)
b_manual_set_save.grid(row=6,column=4)
l_acc_right.grid(row=7, column=2)
l_acc_left.grid(row=8, column=2)
l_frame_desc.grid(row=7, column=3, columnspan=2)
l_frame_1_desc.grid(row=8, column=3, columnspan=2)
l_frame_2_desc.grid(row=9, column=3, columnspan=2)
l_pause_middle.grid(row=9, column=2)
l_pause_left.grid(row=10, column=2)
l_middle_pause_left.grid(row=11, column=2)
l_middle_pause_middle_2.grid(row=12, column=2)
l_middle_pause_middle.grid(row=13, column=2)
l_middle_pause_right.grid(row=14, column=2)
l_valid_pause.grid(row=15, column=2)
#l_valid_pause_2.grid(row=16, column=2)


if os.path.exists(path + "/设置.txt"):
    f = open(path + "/设置.txt")
    e_mode.current(int(f.readline()))
    set_margin(
        int(f.readline()), int(f.readline()), int(f.readline()), int(f.readline())
    )
    set_thread_num(int(f.readline()))
    set_ignore_frame_cnt(int(f.readline()))
    f.close()

set_coordinates()


win.mainloop()
