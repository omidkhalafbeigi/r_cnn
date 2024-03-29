import cv2 as cv
import numpy as np
from matplotlib import pyplot as plt
import os
import pandas as pd
import random as rnd
import pickle
import time
from sklearn.utils import shuffle
from keras.preprocessing.image import ImageDataGenerator
from keras import *

from google.colab import drive
drive.mount('/content/drive')

def get_iou(bb1, bb2):
    assert bb1['x1'] < bb1['x2']
    assert bb1['y1'] < bb1['y2']
    assert bb2['x1'] < bb2['x2']
    assert bb2['y1'] < bb2['y2']
    x_left = max(bb1['x1'], bb2['x1'])
    y_top = max(bb1['y1'], bb2['y1'])
    x_right = min(bb1['x2'], bb2['x2'])
    y_bottom = min(bb1['y2'], bb2['y2'])
    if x_right < x_left or y_bottom < y_top:
        return 0.0
    intersection_area = (x_right - x_left) * (y_bottom - y_top)
    bb1_area = (bb1['x2'] - bb1['x1']) * (bb1['y2'] - bb1['y1'])
    bb2_area = (bb2['x2'] - bb2['x1']) * (bb2['y2'] - bb2['y1'])
    iou = intersection_area / float(bb1_area + bb2_area - intersection_area)
    assert iou >= 0.0
    assert iou <= 1.0
    return iou

def selective_search_dataset():
  path = 'drive/MyDrive/data/train'
  train_imgs = sorted(os.listdir(path))

  for img_name in reversed(train_imgs[136:]):
    img_path = os.path.join(path, img_name)
    img = cv.imread(img_path)[1400:]

    if img_name.split('.')[0] not in os.listdir('/Rectangles'):
      selective_search = cv.ximgproc.segmentation.createSelectiveSearchSegmentation()
      selective_search.setBaseImage(img)
      selective_search.switchToSelectiveSearchFast()
      rectangles = selective_search.process()

      file = open(os.path.join('/Rectangles', img_name.split('.')[0]), 'wb')
      pickle.dump(rectangles, file)
      file.close()
      print(img_name)

    else: continue

def extract_save_backgrounds_objects():
  rectangles_path = 'drive/MyDrive/Rectangles'
  trainingset_path = 'drive/MyDrive/data/train'

  train_list = list()
  label_list = list()

  label_path = '/data/label.xlsx'
  from_to_rqd_path = '/data/from-to-rqd.xlsx'

  rectangles_list = os.listdir(rectangles_path)
  imgs_list = os.listdir(trainingset_path)

  label = pd.read_excel(label_path)

  for img_name in sorted(imgs_list)[:15]:
    imgs_in_label = label[label['image_name'] == img_name]
    start = time.time()

    img_rectangles_path = os.path.join(rectangles_path, img_name.split('.')[0])
    file = open(img_rectangles_path, 'rb')
    rectangles = pickle.load(file)
    file.close()

    for img_idx in range(len(imgs_in_label)):
      print(f'{img_idx}/{len(imgs_in_label)}')
      img_details = imgs_in_label.iloc[img_idx, :]

      x1_ground_truth = img_details['xmin']
      x2_ground_truth = img_details['xmin'] + img_details['width']

      y1_ground_truth = img_details['ymin']
      y2_ground_truth = img_details['ymin'] + img_details['height']

      bb1 = {'x1': x1_ground_truth, 'x2': x2_ground_truth, 'y1': y1_ground_truth, 'y2': y2_ground_truth}

      label_name = img_details['label_name']

      rectangles_loop = shuffle(rectangles)[:20]
      for rectangle in rectangles_loop:
        x1_bounding_box = rectangle[0]
        x2_bounding_box = rectangle[0] + rectangle[2]

        y1_bounding_box = rectangle[1]
        y2_bounding_box = rectangle[1] + rectangle[3]

        bb2 = {'x1': x1_bounding_box, 'x2': x2_bounding_box, 'y1': y1_bounding_box, 'y2': y2_bounding_box}

        iou = get_iou(bb1, bb2)
        img_load = cv.imread(os.path.join(trainingset_path, img_name))

        if (iou >= 0.7 and label_name == '+10cm rock') or (iou >= 0.7 and label_name == 'wood'):
          img_object = img_load[y1_bounding_box : y2_bounding_box, x1_bounding_box : x2_bounding_box] 
          img_object = cv.resize(img_object, (224, 224))
                              
          train_list.append(img_object)
          label_list.append(label_name)

        else:
          img_object = img_load[y1_bounding_box : y2_bounding_box, x1_bounding_box : x2_bounding_box]
          if len(img_object) > 0:
            img_object = cv.resize(img_object, (224, 224))
            train_list.append(img_object)
            label_list.append('background')

    finish = time.time()
  
    file = open('/data/train_backgrounds_1', 'wb')
    pickle.dump(train_list, file)
    file.close()

    file = open('/data/label_backgrounds_1', 'wb')
    pickle.dump(label_list, file)
    file.close()

    print(img_name)
    print(finish - start)
    print('------------')

def extract_save_objects():
  trainingset_path = '/data/train'
  label_path = '/data/label.xlsx'

  imgs_list = os.listdir(trainingset_path)
  label = pd.read_excel(label_path)

  counter = 0

  train_list = list()
  label_list = list()

  for img_name in sorted(imgs_list)[:15]:
      imgs_in_label = label[label['image_name'] == img_name]

      img_load = cv.imread(os.path.join(trainingset_path, img_name))

      for img_idx in range(len(imgs_in_label)):
        img_details = imgs_in_label.iloc[img_idx, :]
        label_name = img_details['label_name']

        x1_ground_truth = img_details['xmin']
        x2_ground_truth = img_details['xmin'] + img_details['width']

        y1_ground_truth = img_details['ymin']
        y2_ground_truth = img_details['ymin'] + img_details['height']

        img_object = img_load[y1_ground_truth : y2_ground_truth, x1_ground_truth : x2_ground_truth]

        if len(img_object) > 0:
          train_list.append(cv.resize(img_object, (224, 224)))
          label_list.append(label_name)
        else:
          print(x1_ground_truth, x2_ground_truth, y1_ground_truth, y2_ground_truth)
          print(img_name)
          print('-----------------------')

      counter += 1
      print(img_name)
      print(counter)

      file = open('/data/train_objects', 'wb')
      pickle.dump(train_list, file)
      file.close()

      file = open('/data/label_objects', 'wb')
      pickle.dump(label_list, file)
      file.close()

# extract_save_backgrounds_objects()

def data_aug():
  path = '/data/train_objects'
  file = open(path, 'rb')
  objects = pickle.load(file)
  file.close()

  path = '/data/label_objects'
  file = open(path, 'rb')
  objects_label = list(pd.Series(pickle.load(file)).replace(to_replace=['+10cm rock', 'wood'], value=[0, 1]))
  file.close()

  objects_rock = np.array(objects)[np.argwhere(np.array(objects_label) == 0)]
  objects_wood = np.array(objects)[np.argwhere(np.array(objects_label) == 1)]

  generator = ImageDataGenerator(width_shift_range=[-50, 50], height_shift_range=0.5, horizontal_flip=True,
                               rotation_range=90, brightness_range=[0.2,1.0], zoom_range=[0.5,1.0])

  rock_counter = 0
  wood_counter = 0

  for rock in objects_rock:
    iterator = generator.flow(rock, batch_size = 1)
    for _ in range(5):
      new_sample = iterator.next()[0].astype('uint8')
      objects.append(new_sample)
      objects_label.append(0)
    rock_counter += 1
    print(rock_counter)

  for wood in objects_wood:
    iterator = generator.flow(wood, batch_size = 1)
    for _ in range(28):
      new_sample = iterator.next()[0].astype('uint8')
      objects.append(new_sample)
      objects_label.append(1)
    wood_counter += 1
    print(wood_counter)

  file = open('/data/train_objects_augmented', 'wb')
  pickle.dump(objects, file)
  file.close()

  file = open('/data/label_objects_augmented', 'wb')
  pickle.dump(objects_label, file)
  file.close()

train_set = list()

for i in range(2):
  file = open(f'/data/train_backgrounds_{i + 1}', 'rb')
  train_set += pickle.load(file)
  file.close()

label = list(np.full(shape=(len(train_set),), fill_value=2))

file_objects_aug = open('/data/train_objects_augmented', 'rb')
file_lable_objects_aug = open('/data/label_objects_augmented', 'rb')

train_set = np.array(train_set + list(pickle.load(file_objects_aug)))
label = np.array(label + list(pickle.load(file_lable_objects_aug))).reshape(-1, 1)

file_objects_aug.close()
file_lable_objects_aug.close()

model = Sequential()
model.add(layers.InputLayer(input_shape=(224, 224, 3), batch_size=32))
model.add(layers.BatchNormalization())
model.add(layers.Conv2D(filters=64, kernel_size=(3, 3), strides=(1, 1), padding='valid', activation='relu'))
model.add(layers.MaxPool2D())
model.add(layers.Conv2D(filters=64, kernel_size=(3, 3), strides=(1, 1), padding='valid', activation='relu'))
model.add(layers.MaxPool2D())

model.add(layers.Flatten())
model.add(layers.Dropout(rate=0.3))

model.add(layers.Dense(units=100, activation='LeakyReLU'))
model.add(layers.Dense(3, activation='softmax'))

model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

model.fit(train_set, label, batch_size=32, epochs=30)
