# -*- coding: utf-8 -*-
"""
Created on Mon Oct 23 23:30:39 2017

@author: Daria
"""
import numpy as np
import cv2
import math
from skimage.measure import regionprops
import matplotlib.pyplot as plt
 
result = 0

# Read image
img = cv2.imread("img/lipa.jpg", cv2.IMREAD_GRAYSCALE);

# Resize if necessary
TARGET_PIXEL_AREA = 300000.0
ratio = float(img.shape[1]) / float(img.shape[0])
new_h = int(math.sqrt(TARGET_PIXEL_AREA / ratio) + 0.5)
new_w = int((new_h * ratio) + 0.5)
img = cv2.resize(img, (new_w,new_h))

height, width = img.shape

# Threshold 
th, im_th = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)

# Copy the thresholded image.
im_floodfill = im_th.copy()
 
# Mask used to flood filling.
# Notice the size needs to be 2 pixels > than the image.
h, w = im_th.shape[:2]
mask = np.zeros((h+2, w+2), np.uint8)
 
# Floodfill from point (0, 0)
cv2.floodFill(im_floodfill, mask, (0,0), 255);
 
# Invert floodfilled image
im_floodfill_inv = cv2.bitwise_not(im_floodfill)
 
# Combine the two images to get the foreground.
im_out = im_th | im_floodfill_inv

# Connected components
nb_components, output, stats, centroids = cv2.connectedComponentsWithStats(im_out, connectivity=8)
sizes = stats[1:, -1]; nb_components = nb_components - 1
min_size = height*width*0.08
#min_size = 30000 

# Remove small objects
img2 = np.zeros((output.shape))
for i in range(0, nb_components):
    if sizes[i] >= min_size:
        img2[output == i + 1] = 255
#Перевод изображения в рабочую кодировку
closing = img2.astype(np.uint8)

#Выделение контуров
edged = closing.copy()

_, contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
cv2.drawContours(edged,contours,-1,(255,255,255),1)
#cv2.imshow('After contouring', edged)

#Проверка контуров по размеру

if len(contours) == 0:
    result=1
    print 'Ошибка. Слишком мелкий объект для анализа, сфотографируйте лист крупнее, пожалуйста.'
    cv2.imshow('Image', edged)
    
else:
    #Tophat
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(50,50))
    #kernel = np.ones((15,25),np.uint8)
    tophat = cv2.morphologyEx(closing, cv2.MORPH_TOPHAT, kernel)
    thresh = cv2.threshold(tophat, 200, 255, cv2.THRESH_BINARY)[1]
    thresh2 = thresh.copy()
    _, contours,_ = cv2.findContours(thresh2,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(thresh2,contours,-1,(255,255,255),1)
    #cv2.imshow('Tophat', thresh2)
    
    if len(contours) == 0:
        result=2
        print 'Ошибка. Сфотографируйте целый лист с черешком, пожалуйста.'
        cv2.imshow('Image', edged)
        
    else:        
        img3 = closing.copy()

        #Вычисление диагонали прямоугольного контура объекта
        def findDiag(cont):
            #создание прямоугольного контура вокруг объекта
            rect = cv2.minAreaRect(cont)
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            #вычисление длины диагонали
            side = np.sqrt((box[0,0]-box[2,0])**2+(box[2,1]-box[0,1])**2)
            return side
        
        maxSide=0
        #Поиск самой длинной диагонали
        for cont in contours:
            side = findDiag(cont)
            if side > maxSide:
                maxSide = side
         
        #Определение объекта с самой длинной диагональю        
        for cont in contours:
            #Определение координат пикселей объекта
            mask = np.zeros(thresh.copy().shape,np.uint8)
            cv2.drawContours(mask,[cont],0,255,-1)
            pixelpoints = np.transpose(np.nonzero(mask))
            #Вычисление длин диагоналей
            side = findDiag(cont)
            #Удаление объекта с самой длинной диагональю
            if side == maxSide:
                forPoint = pixelpoints
                for i in pixelpoints:
                    img3[i[0],i[1]] = 0
        
        #Переход к цветному изображению
        backtorgb = cv2.cvtColor(img3,cv2.COLOR_GRAY2RGB)
        
        #Поиск точки роста, coord - координаты точки роста
        for i in forPoint:
            if img3[i[0]-1,i[1]] == 255:
                coord = i[0]-1,i[1]
                continue
            elif img3[i[0],i[1]+1] == 255:
                 coord = i[0],i[1]+1
                 continue
            elif img3[i[0]+1,i[1]] == 255:
                 coord = i[0]+1,i[1]
                 continue
            elif img3[i[0],i[1]-1] == 255:
                 coord = i[0],i[1]-1
                 continue
        
        # Выделение точки роста на изображении
        backtorgb[coord[0],coord[1]] = [0,0,255]
        height, width, channels = backtorgb.shape
        cv2.line(backtorgb,(0,coord[0]),(height,coord[0]),(0,0,255),1)
        cv2.line(backtorgb,(coord[1],width),(coord[1],0),(0,0,255),1)
        
        # Connected components
        nb_components, output, stats, centroids = cv2.connectedComponentsWithStats(img3, connectivity=8)
        sizes = stats[1:, -1]; nb_components = nb_components - 1
        min_size = height*width*0.08
        
        # Remove small objects
        img = np.zeros((output.shape))
        for i in range(0, nb_components):
            if sizes[i] >= min_size:
                img[output == i + 1] = 255
                # Перевод изображения в рабочую кодировку
                img3 = img.astype(np.uint8)
        
        edged = img3.copy()
        _, contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(edged,contours,-1,(255,255,255),1)
       
#        #Удаление незамкнутых контуров
#        edged3 = edged.copy()
#        mask = np.zeros((np.array(edged.shape)+2), np.uint8)
#        cv2.floodFill(edged, mask, (0,0), (255))
#        edged = cv2.erode(edged, np.ones((3,3)))
#        edged = cv2.bitwise_not(edged)
#        edged = cv2.bitwise_and(edged,edged3)
#                
        #Проверка оставшихся на изображении контуров
        _, contours, _ = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours) > 1:
            result=4
            print 'Ошибка. Сфотографируйте один лист на нейтральном фоне, пожалуйста.'
            cv2.imshow('Image', edged)
            
        else:
            if len(contours) == 0:
                result=3
                print 'Ошибка. Лист выходит за края изображения, сфотографируйте его полностью, пожалуйста.'
                cv2.imshow('Image', edged)
                
            else:
                if len(contours) == 1:
                    cnt = contours[0]
                    area = cv2.contourArea(cnt)
                    if area < min_size:
                        result=5
                        print 'Ошибка. Сфотографируйте лист на контрастном фоне, пожалуйста.'
                        cv2.imshow('Image', edged)
            
if result == 0:
    cv2.drawContours(edged,contours,-1,(255,255,255),1)
    
    #cv2.imshow('Leaf contour', edged)
    cv2.imshow('Image', img3)
    print 'Done!'

    ##### Eccentricity #####
    props = regionprops(img3)
    eccentricity = props[0].eccentricity

    ##### Solidity #####
    solidity = props[0].solidity
    
    ##### Extent #####
    extent = props[0].extent
    
    ##### Equivalent Diameter #####
    equivalent_diameter = props[0].equivalent_diameter

    ##### Convex hull #####
    convexhull = props[0].convex_area

    # Центроид
    props = regionprops(img3)
    x1 = props[0].centroid[1]
    y1 = props[0].centroid[0]

    # Координаты точек контура
    _, contours, _ = cv2.findContours(img3, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    cnt = contours[0]
    
    class myarray(np.ndarray):
        def __new__(cls, *args, **kwargs):
            return np.array(*args, **kwargs).view(myarray)
        def index(self, value):
            return np.where(self==value)
    
    # Вектор расстояний dist от центра масс до границ
    N = len(cnt)
    dist = [] 
    for i in range(N): 
    	p = cnt[i]
    	x2 = p.item(0)
    	y2 = p.item(1)
    	distance = ((x2 - x1)**2 + (y2 - y1)**2)**(.5)
    	dist.append(distance)
        
    # Поиск основания
    start = 0
    # Ищем соответствие координатам основания
    point = np.where(np.flip(cnt,2) == coord)
    # В результатах ищем полное совпадение
    for i in range(len(np.unique(point[0]))):
        if (np.flip(cnt[np.unique(point[0])[i]],1) == coord)[0][0] == True & (np.flip(cnt[np.unique(point[0])[i]],1) == coord)[0][1] == True:
          #  print np.unique(point[0])[i]
           # print i
          start = np.unique(point[0])[i]
    
    # Перемешиваем по индексу    
    newdist = dist[start:N] + dist[0:start]
    plt.plot(newdist)
   # plt.plot(dist)
    
# Display images.
cv2.waitKey(0)
cv2.destroyAllWindows()