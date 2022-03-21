#!/usr/bin/env python

import rospy
from rospy.timer import Rate
from sensor_msgs.msg import Image
from sensor_msgs.msg import PointCloud2
from sensor_msgs import point_cloud2 as pc2
import cv2, cv_bridge
import numpy as np
from TensorModule import *
from realsense_depth import *


class Camera():

        def __init__(self):
                rospy.init_node('camera_node')
                #self.image_sub = rospy.Subscriber('/camera/image_raw', Image, self.image_callback)
                #self.image_sub = rospy.Subscriber('/camera/color/image_raw', Image, self.image_callback)
                #self.depthpc_sub = rospy.Subscriber('/camera/depth/color/points', PointCloud2, self.points_callback)
                #elf.points_msg = PointCloud2()
                self.rate = rospy.Rate(30)
                #self.bridge = cv_bridge.CvBridge()
                self.depth = DepthCamera()


        def distance_callback(self):
                   ret, depth_frame, color_image = self.depth.get_frame() 
                   return ret, depth_frame, color_image


        def image_denoise(self, msg):
                #kernel = np.ones((3, 3), np.float32)/25
                #filtered = cv2.GaussianBlur(self.image, (5, 5), 0)
                #filtered = cv2.medianBlur(self.image, 5)
                #filtered = cv2.bilateralFilter(self.image, 9, 75, 75)
                #filtered = cv2.cvtColor(filtered, cv2.COLOR_BGR2GRAY)
                #_ ,filtered = cv2.threshold(filtered,127,255,cv2.THRESH_BINARY)
                #return filtered
                pass

if __name__ == '__main__':

        
        labels = load_labels()
        camera = Camera()
        tensor = Tensor(labels)
        #depth = DepthCamera()
        for i in range (10):
                camera.rate.sleep()
        while not rospy.is_shutdown():
                pass
                while True:
                        succes, depth_frame, image = camera.distance_callback()
                        image= tensor.do_magic(image, depth_frame)

                        cv2.imshow('Image', image)
                        if cv2.waitKey(1) & 0xFF ==ord('q'):
                                cv2.destroyAllWindows()
                                break

