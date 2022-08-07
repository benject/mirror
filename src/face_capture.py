#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Bing Chen

import os
import json
import mediapipe as mp
import cv2

mpDrawUtils = mp.solutions.mediapipe.python.solutions.drawing_utils
mpFacemesh = mp.solutions.mediapipe.python.solutions.face_mesh

mpDrawSpec = mpDrawUtils.DrawingSpec(color=(0,255,0),thickness=1,circle_radius=1)

class face_capture():

  def __init__(self,file):

    self.file = file

      
  def image_capture(self):
    """
    using mediapipe to get 468 face feature points and dump them to a json file
    利用mediapipe库,获取468个特征点并写入json 文件
    """


    basename,ext = os.path.splitext(self.file) #get the extension of image file  
    json_file = self.file.replace(ext,".json") #replace extension with .json

    IMAGE = cv2.imread(self.file)
    
    with mpFacemesh.FaceMesh(static_image_mode=True, max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5) as face_mesh:

      image = cv2.cvtColor(IMAGE,cv2.COLOR_BGR2RGB)
      results = face_mesh.process(image)
      image = cv2.cvtColor(image,cv2.COLOR_RGB2BGR)

      height  = image.shape[0]
      width = image.shape[1]

      sx = width / height #根骨骼x轴缩放
      frame = 1 #当前帧

      if results.multi_face_landmarks:

        for facelms in results.multi_face_landmarks:

          mpDrawUtils.draw_landmarks(image,facelms,mpFacemesh.FACEMESH_TESSELATION,mpDrawSpec,mpDrawSpec)
          
          value = []
          for lms in facelms.landmark:      
            
            pos = (lms.x,lms.y,lms.z)
            value.append(pos) #特征点位置

          with open(json_file,'w') as jsonfile:

            json.dump([{'frame':frame,'sx':sx,'jnt_pos':value}],jsonfile,indent=4)
      

      cv2.namedWindow("img",cv2.WINDOW_NORMAL)
      cv2.resizeWindow("img",width,height) #adjust window's width and height
      cv2.imshow("img",image)   

      if cv2.waitKey(50000) & 0xFF == 27:
        exit() 


  def video_capture(self):

    # For video input:
    
    cap = cv2.VideoCapture(self.file)

    basename,ext = os.path.splitext(self.file)
    json_file = self.file.replace(ext,".json") #replace extension with .json

    #准备写入文件的数据
    data = []
    
    sx = 1.0
    frame = 0
    value = []

    dict = {'frame':frame,'sx':sx,'jnt_pos':value}          
    data.append(dict)

    
    with mpFacemesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5) as face_mesh:
      
      while cap.isOpened():
        success, image = cap.read()        

        if not success:
          print("Ignoring empty camera frame.")
          # If loading a video, use 'break' instead of 'continue'.

          with open(json_file,'w') as jsonfile:
            json.dump(data,jsonfile,indent=4)
          break
        
        height = image.shape[0]
        width  = image.shape[1]

        sx=(width / height) #根骨骼x轴缩放

        frame += 1

        value = []

        # To improve performance, optionally mark the image as not writeable to
        # pass by reference.
        image.flags.writeable = False
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(image)

        # Draw the face mesh annotations on the image.
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        if results.multi_face_landmarks:
          for facelms in results.multi_face_landmarks:
            mpDrawUtils.draw_landmarks(
                image=image,
                landmark_list=facelms,
                connections=mpFacemesh.FACEMESH_TESSELATION,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp.solutions.mediapipe.python.solutions.drawing_styles
                .get_default_face_mesh_tesselation_style())
            mpDrawUtils.draw_landmarks(
                image=image,
                landmark_list=facelms,
                connections=mpFacemesh.FACEMESH_CONTOURS,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp.solutions.mediapipe.python.solutions.drawing_styles
                .get_default_face_mesh_contours_style())
            mpDrawUtils.draw_landmarks(
                image=image,
                landmark_list=facelms,
                connections=mpFacemesh.FACEMESH_IRISES,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp.solutions.mediapipe.python.solutions.drawing_styles
                .get_default_face_mesh_iris_connections_style())

            for lms in facelms.landmark:
              pos = (lms.x,lms.y,lms.z)
              value.append(pos) #特征点位置
        dict = {'frame':frame,'sx':sx,'jnt_pos':value}

        data.append(dict)

        # Flip the image horizontally for a selfie-view display.
        cv2.imshow('MediaPipe Face Mesh', image)
        if cv2.waitKey(5) & 0xFF == 27:          
          break


if(__name__ == '__main__'):

  '''
    usage: 
    py -3 face_capture.py -v video.mp4
  '''

  import argparse
  parser = argparse.ArgumentParser(
      description='input the filename')
  group = parser.add_mutually_exclusive_group() #添加互斥参数
  group.add_argument(
    '-i','--image',
    help = 'the input image file')
  group.add_argument(
    '-v', '--video', 
    help='the input video file')
  
  
  args = parser.parse_args()

  #print(args)

  if ((args.image==None) and (args.video==None)):

    print("you must input a image or a video file")
  
  elif not (args.image == None):

    face_cap = face_capture(args.image)
    face_cap.image_capture()
  else:
    face_cap = face_capture(args.video)
    face_cap.video_capture()