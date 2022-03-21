import re
import cv2
from numpy.core.fromnumeric import size
from numpy.lib.function_base import angle
from tflite_runtime.interpreter import Interpreter
import numpy as np
import os
from realsense_depth import *

class Tensor():

    def __init__(self, labels, CAMERA_WIDTH = 1920, CAMERA_HEIGHT = 1080):
        self._OUTPUT_LOCATION_NAME = 'location'
        self._OUTPUT_CATEGORY_NAME = 'category'
        self._OUTPUT_SCORE_NAME = 'score'
        self._OUTPUT_NUMBER_NAME = 'number of detections'
        self.CAMERA_WIDTH = CAMERA_WIDTH
        self.CAMERA_HEIGHT = CAMERA_HEIGHT
        path_to_detect = path = os.path.join(os.path.expanduser('~'), 'ROS_Works', 'workspace_uirs','src', 'rgbd_camera','includes', 'detect.tflite')
        self.interpreter = Interpreter(path_to_detect)
        self.interpreter.allocate_tensors()
        self.labels = labels
        self.bbox_list = []

        self.angle_X = np.zeros((1080, 1920))
        self.angle_Z = np.zeros((1080, 1920))
             
        for i in range(1080):
            for j in range(1920):
                    self.angle_X[i][j]=-22.8+0.02375*j

        for i in range(1080):
            for j in range(1920):
                self.angle_Z[i][j] = 12.825-0.02375*i
        self.angle_Z = np.asanyarray(self.angle_Z)
        self.angle_X = np.asanyarray(self.angle_X)
        #print(len(self.angle_Y[1]))

    def set_input_tensor(self, image):
        """Sets the input tensor."""
        tensor_index = self.interpreter.get_input_details()[0]['index']
        input_tensor = self.interpreter.tensor(tensor_index)()[0]
        input_tensor[:, :] = np.expand_dims((image-255)/255, axis=0)


    def get_output_tensor(self, index):
        """Returns the output tensor at the given index."""
        sorted_output_indices = sorted(
            [output['index'] for output in self.interpreter.get_output_details()])
        _output_indices = {
            self._OUTPUT_LOCATION_NAME: sorted_output_indices[0],
            self._OUTPUT_CATEGORY_NAME: sorted_output_indices[1],
            self._OUTPUT_SCORE_NAME: sorted_output_indices[2],
            self._OUTPUT_NUMBER_NAME: sorted_output_indices[3],
        }
        output_index = _output_indices[index]
        tensor = np.squeeze(self.interpreter.get_tensor(output_index))
        return tensor


    def detect_objects(self, image, threshold):
        """Returns a list of detection results, each a dictionary of object info."""
        self.set_input_tensor(image)
        self.interpreter.invoke()
    # Get all output details
        

        boxes = self.get_output_tensor(self._OUTPUT_LOCATION_NAME)
        classes = self.get_output_tensor(self._OUTPUT_CATEGORY_NAME)
        scores = self.get_output_tensor(self._OUTPUT_SCORE_NAME)
        count = int(self.get_output_tensor(self._OUTPUT_NUMBER_NAME))

        self.results = []
        for i in range(count):
            if scores[i] >= threshold:
                result = {
                'bounding_box': boxes[i],
                'class_id': classes[i],
                'score': scores[i]
                }
                self.results.append(result)
        return self.results

    def get_labels(self, labels):
        self.labels = labels

    def get_bbox(self, frame):
        for result in self.results:
            self.ymin, self.xmin, self.ymax, self.xmax = result['bounding_box']
            self.xmin = int(self.xmin*self.CAMERA_WIDTH)
            self.xmax = int(self.xmax*self.CAMERA_WIDTH)    
            self.ymin = int(self.ymin*self.CAMERA_HEIGHT)  
            self.ymax = int(self.ymax*self.CAMERA_HEIGHT)
            self.bbox_list = [self.xmin, self.xmax, self.ymin, self.ymax]

            cv2.rectangle(frame,(self.xmin, self.ymin),(self.xmax, self.ymax),(0,255,0),3)
            cv2.putText(frame,self.labels[int(result['class_id'])],(self.xmin, min(self.ymax, self.CAMERA_HEIGHT-20)), cv2.FONT_HERSHEY_SIMPLEX, 0.5,(255,255,255),2,cv2.LINE_AA)

    def get_dist_and_crop(self, res, frame, depth_frame):
        anglex=0
        anglez=0
        min_dist_point=[]
        self.distance_angle = [] #dist, x angle, z angle
        if res:
            crop_image = frame[self.ymin:self.ymax, self.xmin: self.xmax]
            h, w, c = crop_image.shape
            if h>6 and w>6:
                crop_depth = depth_frame[self.ymin:self.ymax, self.xmin: self.xmax]
                crop_angle_X = self.angle_X[self.ymin:self.ymax, self.xmin: self.xmax]
                crop_angle_Z = self.angle_Z[self.ymin:self.ymax, self.xmin: self.xmax]
                min_dist = None
                min_dist_point=[0, 0 , 0]

                for i in range(np.size(crop_image, 0)):
                    for j in range(np.size(crop_image, 1)):
                        if crop_depth[i, j] !=0:
                            min_dist = crop_depth[i, j]
                            break

                if min_dist!=None:      
                    for i in range(np.size(crop_image, 0)):
                        for j in range(np.size(crop_image, 1)):
                            if (min_dist>crop_depth[i,j]) and (crop_depth[i,j] != 0) :
                                min_dist = crop_depth[i,j]
                                min_dist_point=[i, j, crop_depth[i,j]]
                    
                    anglex = crop_angle_X[min_dist_point[0]][min_dist_point[1]]
                    anglez = crop_angle_Z[min_dist_point[0]][min_dist_point[1]]
                    cv2.circle(crop_image, (min_dist_point[0], min_dist_point[1]), 5, (0, 0, 255), cv2.FILLED)
                    cv2.imshow('Crop_image', crop_image)
                    print('Dist = ', min_dist_point[2])
                    print('Angle x: ', anglex, ' Angle Y: ', anglez)
                    self.distance_angle = [min_dist_point[2], anglex, anglez]
                    #print(self.angle_distance)

    def do_magic(self, frame, depth_frame):
        img = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), (320,320))
        res = self.detect_objects(img, 0.85)
        #print(res)

        self.get_bbox(frame)
        self.get_dist_and_crop(res, frame, depth_frame)
        return frame, self.distance_angle

            
def load_labels(path=os.path.join(os.path.expanduser('~'), 'ROS_Works', 'workspace_uirs','src', 'rgbd_camera','includes', 'labels.txt')):
    """Loads the labels file. Supports files with or without index numbers."""
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        labels = {}
        for row_number, content in enumerate(lines):
            pair = re.split(r'[:\s]+', content.strip(), maxsplit=1)
            if len(pair) == 2 and pair[0].strip().isdigit():
                labels[int(pair[0])] = pair[1].strip()
            else:
                labels[row_number] = pair[0].strip()
    return labels

def main():
    labels = load_labels()
    tensor = Tensor(labels, 640, 480)
    cap = cv2.VideoCapture(0)
    while True:
        success, image = cap.read()
        image, crop_image, flag = tensor.do_magic(image)
        cv2.imshow('Image', image)
        if flag:
            cv2.imshow('Crop', crop_image)
        if cv2.waitKey(1) & 0xFF ==ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            break

if __name__ == "__main__":
    pass
