#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Bing Chen

import maya.cmds as cmds
import json
import os ,sys
import subprocess

import PySide2.QtCore as QtCore
from PySide2.QtWidgets import QFileDialog
from PySide2.QtUiTools import QUiLoader



def onMayaDroppedPythonFile(obj):

    sys_path = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..')) 

    sys.path.append(sys_path) #install this mod to maya
    



class GUI():
    '''
    界面
    '''

    def __init__(self,root_path):
        
        self.time_unit = {
        'game': 15.0 ,
        'film': 24.0 ,
        'pal':  25.0 ,
        'ntsc': 30.0 ,
        'show': 48.0 ,
        'palf': 50.0 ,
        'ntscf': 60.0 }

        self.json_file = ''
        self.root_path = root_path



        self.ui_file = QtCore.QFile( os.path.join(self.root_path,r"ui\FaceCapture_ui.ui")) # 实例化 QFILE 对象
        self.ui_file.open(QtCore.QFile.ReadOnly) #打开ui_file

        loader = QUiLoader() #QUIloader 对象
        self.window = loader.load(self.ui_file) # 用QuiLoader对象读取ui_file

        self.ref_file = os.path.abspath(os.path.join(self.root_path,r"scene\facemesh.mb"))

        self.window.lineEdit_2.setText(self.ref_file)

        self.display_maya_fps(self.get_maya_fps())

        self.window.pushButton_4.clicked.connect(self.select_video_file) #将clicked信号连接到 选择视频文件 槽函数。 函数名作为参数 不带括号

        self.window.pushButton_3.clicked.connect(self.ref_scene_file) #将clicked信号连接到 参考文件 槽函数。 函数名作为参数 不带括号

        self.window.pushButton.clicked.connect(self.select_anim_file) #将clicked信号连接到 选择文件 槽函数。 函数名作为参数 不带括号

        #self.window.pushButton_2.clicked.connect(lambda: self.display_maya_fps(self.get_maya_fps())) #pyside 如果需要传参数 用 lamda表达式
        self.window.pushButton_2.clicked.connect(self.process)


        self.window.show()

    def ref_scene_file(self):

        cmds.file(self.ref_file, r=True, mergeNamespacesOnClash=False, namespace='facemesh')
        cmds.select("facemesh:root",r=True,hi=True)
        self.jnt_arr = cmds.ls(sl=True)[1:]
        for joint in self.jnt_arr:
            cmds.setKeyframe( joint + ".tx")
            cmds.setKeyframe( joint + ".ty")
            cmds.setKeyframe( joint + ".tz")
    

    def display_maya_fps(self,val):

        '''
        在界面上显示maya的fps
        '''
        
        self.window.label_2.setText(str(val))

    
    def get_maya_fps(self):

        '''
        获取maya 的fps
        '''
        try:
            self.fps_maya = self.time_unit[cmds.currentUnit(q=True,time=True)]
        except:
            self.fps_maya = float(cmds.currentUnit(q=True,time=True).replace("fps",""))

        return self.fps_maya

    def select_video_file(self):
        '''
        选择video文件
        '''

        dlg = QFileDialog()

        self.video_file = dlg.getOpenFileName()[0] #返回的是元组 获得video

        self.window.lineEdit_3.setText(self.video_file)

        p = subprocess.Popen(['py', '-3', os.path.abspath(os.path.join(self.root_path,r'src\face_capture.py')), '-v',self.video_file])

        print("processing video capture" , self.video_file)



    def select_anim_file(self):
        
        '''
        选择json文件
        '''

        dlg = QFileDialog()
        

        self.json_file = dlg.getOpenFileName()[0] #返回的是元组 获得json

        self.window.lineEdit.setText(self.json_file)

        #print(self.json_file)        
        
        file = open(self.json_file,"r")
        datas = json.load(file) #datas的数据结构为 [ {frame:%d,sx:%f,jnt_pos:[%f,%f,%f]},{...} ]
        file.close()
        
        self.window.label_4.setText(str(len(datas)))        


    def process(self):

        c2m = Capture_to_Mesh()
        c2m.place_joints(filename=self.json_file)



class Capture_to_Mesh():
    def __init__(self):

        #获取骨骼列表
        cmds.select("facemesh:root",r=True,hi=True)
        self.jnt_arr = cmds.ls(sl=True)[1:]

    def place_joints(self,filename):
        #读取json文件
        file = open(filename,"r")
        datas = json.load(file) #datas的数据结构为 [ {frame:%d,sx:%f,jnt_pos:[%f,%f,%f]},{...} ]

        for data in datas:

            sx = data['sx']
            pos_arr = data['jnt_pos']

            cmds.currentTime(data['frame'])

            if(len(pos_arr)==0):
                pass

            else:
            #初始化根骨骼位置，由于landmark值均为绝对坐标 因此在每一帧要先还原根骨骼位置，最后再将根骨骼位置进行旋转和缩放。

                cmds.setAttr("facemesh:root.rx",0)
                cmds.setAttr("facemesh:root.sx",1)
                cmds.setAttr("facemesh:root.sz",1) 

            #根据文件内容驱动骨骼位置

            '''
            要将mediapipe的landmark位置还原到maya空间,需要三个步骤:
            
            首先, 将landmark位置传给骨骼。mediapipe的landmark位置也就是骨骼位置(x,y,z)被归一化到[0,1]区间,
            为了匹配到图像,x的位置要乘上图片的宽,y的位置要乘上图片的高。在这里简单的将根骨骼y轴缩放设定为1 则 x轴的缩放就是 图像宽/图像高   

            其次, 根据mediapipe的文档, 摄像机的坐标和maya的世界坐标关系, 要将根骨骼的x轴旋转180°

            再次, 根据mediapipe 的文档,mediapipe采用了weak perspective projection camera model 因此 z轴的缩放与x轴缩放相同。
            原文:“while the Z coordinate is relative and is scaled as the X coodinate under the weak perspective projection camera model”
    
            '''
            for id , pos in enumerate(pos_arr):
                x = pos[0]
                y = pos[1]
                z = pos[2]
                #468-478是10个瞳孔的坐标（左右各5个）
                if id>467:
                    break

                cmds.xform(self.jnt_arr[id],ws=True,t=(float(x),float(y),float(z)))
                    
            cmds.setAttr("facemesh:root.sx",sx)  #第一步
            cmds.setAttr("facemesh:root.rx",180) #第二步
            cmds.setAttr("facemesh:root.sz",sx)  #第三步


# ====================================

import capture_to_mesh 

root_path = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..')) #after install we can get the current file's path
gui = capture_to_mesh.GUI(root_path) 

