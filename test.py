#-*- coding: UTF-8 -*

import random
import re
import time
import threading
import os
import sys
from tkinter import *
from tkinter import ttk
from base64 import b64decode
from PIL import Image,ImageTk
from tkinter import messagebox
from tkinter.filedialog import askopenfilename



"""
2021-11-10点名/抽奖程序
主要亮点：
1.两种模式：
①顺序点名
②随机点名
2.自动识别人名单
3.支持手动导入人名单
4.人名单导入校验
5.人名显示位置自动矫正
6.最多显示五个大字
"""


imgs=['./point_name.png']
class APP:
    def __init__(self):
        self.root = Tk()
        self.running_flag=False #开始标志
        self.time_span=0.05 #名字显示间隔
        self.root.title('Point_name-V2.0')
        self.path = os.path.dirname(os.path.realpath(sys.executable))
        
        width = 680
        height = 350
        left = (self.root.winfo_screenwidth() - width) / 2
        top = (self.root.winfo_screenheight() - height) / 2
        self.root.geometry("%dx%d+%d+%d" % (width, height, left, top))
        self.root.resizable(0,0)
        self.create_widget()
        self.set_widget()
        self.place_widget()
        self.root.mainloop()

    def create_widget(self):
        self.label_show_name_var=StringVar()
        self.label_show_name=ttk.Label(self.root,textvariable=self.label_show_name_var,font=('Arial', 100,"bold"),foreground = '#1E90FF')
        self.btn_start=ttk.Button(self.root,text="开始",)
        self.btn_load_names=ttk.Button(self.root,text="名单加载",)
        self.lf1=ttk.LabelFrame(self.root,text="点名方式")
        self.radioBtn_var=IntVar()
        self.radioBtn_var.set(2)
        self.radioBtn_sequence=ttk.Radiobutton(self.lf1,text="顺序点名",variable=self.radioBtn_var, value=1)
        self.radioBtn_random=ttk.Radiobutton(self.lf1,text="随机点名",variable=self.radioBtn_var, value=2)
        self.label_show_name_num=ttk.Label(self.root,font=('Arial', 20),foreground = '#FF7F50')
        self.proverb=ttk.Label(self.root,font=('Arial',50, "bold"), foreground = '#FF7F50')
        self.proverb.config(text="眼观千遍，不如手写一遍!")

        #paned = PanedWindow(self.root)
        #self.img = imgs
        #img_=b''       
        #the_img = b64decode(img_)#将图片硬编码到GUI
        #paned.image = ImageTk.PhotoImage(data=the_img)
        #self._img = Label(self.root, image=paned.image,background='black')


    def set_widget(self):
        default_name_="会是谁？"
        self.label_show_name_var.set(default_name_)
        self.label_show_name_adjust(default_name_)
        self.btn_start.config(command=lambda :self.thread_it(self.start_point_name))
        self.btn_load_names.config(command=self.load_names)

        filename = os.path.join(self.path, "names.txt")
        while not os.path.exists(filename) and self.path.count("/") > 4:
            self.path = os.path.dirname(self.path)
            filename = os.path.join(self.path, "names.txt")

        self.filename = filename

        init_names=self.load_names_txt(self.filename)
        self.root.protocol('WM_DELETE_WINDOW',self.quit_window)
        self.root.bind('<Escape>',self.quit_window)
        if init_names:
            self.default_names=init_names   #1.文件存在但是无内容。2.文件不存在
            self.label_show_name_num.config(text="一共加载了{}个姓名".format(len(self.default_names)))
        else:
            self.btn_start.config(state=DISABLED)
            #self.label_show_name_num.config(text="请先手动导入人名单！")
            self.label_show_name_num.config(text=self.path)



    def place_widget(self):
        self.lf1.place(x=480,y=110,width=120,height=80)
        self.radioBtn_sequence.place(x=20,y=0)
        self.radioBtn_random.place(x=20,y=30)
        self.btn_start.place(x=480,y=200,width=120,height=30)
        self.btn_load_names.place(x=480,y=240,width=120,height=30)
        self.label_show_name_num.place(x=10,y=300)
        self.proverb.place(x=50, y=10)
        #self._img.place(x=0, y=0)


    def label_show_name_adjust(self,the_name):
        if len (the_name)==1:
            self.label_show_name.place(x=240, y=120)
        elif len(the_name) == 2:
            self.label_show_name.place(x=140, y=120)
        elif len(the_name) == 3:
            self.label_show_name.place(x=80, y=120)
        elif len(the_name) == 4:
            self.label_show_name.place(x=40, y=120)
        else:
            self.label_show_name.place(x=0, y=120)


    def start_point_name(self):
        """
        启动之前进行判断，获取点名模式
        :return:
        """
        if len(self.default_names)==1:
            messagebox.showinfo("提示",'人名单就一个人，不用选了！')
            self.label_show_name_var.set(self.default_names[0])
            self.label_show_name_adjust(self.default_names[0])
            return
        if self.btn_start["text"]=="开始":
            self.btn_load_names.config(state=DISABLED)
            self.running_flag=True
            if isinstance(self.default_names,list):
                self.btn_start.config(text="就你了")
                if self.radioBtn_var.get()==1:
                    mode="sequence"
                elif self.radioBtn_var.get()==2:
                    mode="random"
                else:
                    pass
                self.thread_it(self.point_name_begin(mode))


            else:
                messagebox.showwarning("警告","请先导入人名单！")
        else:
            self.running_flag=False
            self.btn_load_names.config(state=NORMAL)
            self.btn_start.config(text="开始")


    def point_name_begin(self,mode):
        """
        开始点名，点名主函数
        :param mode:
        :return:
        """
        self.update_names(self.filename)

        if mode == "sequence":
            if self.running_flag:
                self.always_ergodic()
        elif mode=="random":
            while True:
                    if self.running_flag:
                        random_choice_name=random.choice(self.default_names)
                        self.label_show_name_var.set(random_choice_name)
                        self.label_show_name_adjust(random_choice_name)
                        time.sleep(self.time_span)
                    else:
                        break


    def always_ergodic(self):
        """
        一直遍历此列表,使用死循环会造成线程阻塞
        :return:
        """
        for i in self.default_names:
            if self.running_flag:
                self.label_show_name_var.set(i)
                self.label_show_name_adjust(i)
                time.sleep(self.time_span)
                if i==self.default_names[-1]:
                    self.always_ergodic()
            else:
                break

    def update_names(self, filename):
        names=self.load_names_txt(filename)
        if names:
            self.default_names=names
            no_Chinese_name_num=len([n for n in names if not self.load_name_check(n)])
            if no_Chinese_name_num==0:
                pass
            else:
                messagebox.showwarning("请注意","导入名单有{}个不是中文名字".format(no_Chinese_name_num))
            self.label_show_name_num.config(text="一共加载了{}个姓名".format(len(self.default_names)))
            default_name_ = "会是谁？"
            self.label_show_name_var.set(default_name_)
            self.label_show_name_adjust(default_name_)
            self.btn_start.config(state=NORMAL)
        else:
            messagebox.showwarning("警告","导入失败，请检查！")

    def load_names(self):
        """
        手动加载txt格式人名单
        :return:
        """
        filename = askopenfilename(
                filetypes = [('文本文件', '.TXT'), ],
                title = "选择一个文本文件",
            initialdir=self.path
                )
        if filename:
            self.filename = filename
            names=self.load_names_txt(filename)
            if names:
                self.default_names=names
                no_Chinese_name_num=len([n for n in names if not self.load_name_check(n)])
                if no_Chinese_name_num==0:
                    pass
                else:
                    messagebox.showwarning("请注意","导入名单有{}个不是中文名字".format(no_Chinese_name_num))
                self.label_show_name_num.config(text="一共加载了{}个姓名".format(len(self.default_names)))
                default_name_ = "会是谁？"
                self.label_show_name_var.set(default_name_)
                self.label_show_name_adjust(default_name_)
                self.btn_start.config(state=NORMAL)
            else:
                messagebox.showwarning("警告","导入失败，请检查！")


    def load_names_txt(self,txt_file):
        """
        读取txt格式的人名单
        :param txt_file:
        :return:
        """
        try:
            with open(txt_file,'r',encoding="utf-8")as f:
                names=[name.strip() for name in f.readlines()]
                if len(names)==0:
                    return False
                else:
                    return names
        except:
            return False


    def load_name_check(self,name):
        """
        对txt文本中的人名进行校验
        中文汉字->True
        非中文汉字->False
        :param name:
        :return:
        """
        regex = r'[\u4e00-\u9fa5]+'
        if re.match(regex,name):
            return True
        else:
            return False


    def thread_it(self,func,*args):
        t=threading.Thread(target=func,args=args)
        t.setDaemon(True)
        t.start()


    def quit_window(self,*args):
        """
        程序退出触发此函数
        :param args:
        :return:
        """
        ret=messagebox.askyesno('退出','确定要退出？')
        if ret:
            self.root.destroy()


if __name__ == '__main__':
    a=APP()
