#!/usr/bin/env python

from io import StringIO
from numpy.core.records import fromarrays
import rospy
from rospy.timer import Rate
from sensor_msgs.msg import Image
from std_msgs.msg import String
import cv2, cv_bridge
import numpy as np
import math
from TensorModule import *



class Camera():

        def __init__(self):
                rospy.init_node('camera_node')
                self.image_depth_sub = rospy.Subscriber('/camera/aligned_depth_to_color/image_raw', Image, self.image_depth_callback, queue_size=1)
                self.image_sub = rospy.Subscriber('/camera/color/image_raw', Image, self.image_callback)
                self.coord_publisher = rospy.Publisher('coordinates', String, queue_size=10)
                self.rate = rospy.Rate(30)
                self.bridge = cv_bridge.CvBridge()

        def image_depth_callback(self, msg):
                depth_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough') 
                cv_img_arr  = np.array(depth_image, dtype = np.dtype('f8'))
                cv_img_norm = cv2.normalize(cv_img_arr, cv_img_arr, 0, 1, cv2.NORM_MINMAX)

                self.depth_image = cv_img_norm 

        def image_callback(self, msg):
                image = self.bridge.imgmsg_to_cv2(msg,desired_encoding='bgr8') #desired_encoding='bgr8'
                self.image = np.asanyarray(image)

        def image_ret(self):
                return self.image

        def depth_ret(self):
                return self.depth_image

        def get_coordinate(self, dist_angle):
                #dist, x angle, z angle
                #camera point = 0 0 0
                x = math.fabs(dist_angle[0]*math.cos(dist_angle[1]*180/math.pi))
                y = dist_angle[0]*math.sin(dist_angle[1]*180/math.pi)
                z = dist_angle[0]*math.sin(dist_angle[2]*180/math.pi)
                #print('coord is: ',x, y, z)
                self.coord_publisher.publish(str(x)+' ' +str(y) + ' ' + str(z))
                

if __name__ == '__main__':
        labels = load_labels()
        camera = Camera()
        tensor = Tensor(labels)
        for i in range (10):
                camera.rate.sleep()
        while not rospy.is_shutdown():
                pass
                while True:
                        depth_frame = camera.depth_ret()
                        image = camera.image_ret()
                        image, dist_angle= tensor.do_magic(image, depth_frame)
                        if dist_angle:
                                camera.get_coordinate(dist_angle)
                        cv2.imshow('Imagee',image)
                        if cv2.waitKey(1) & 0xFF ==ord('q'):
                                cv2.destroyAllWindows()
                                break

