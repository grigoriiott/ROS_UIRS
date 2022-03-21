import os
import tensorflow as tf
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as viz_utils
from object_detection.builders import model_builder
from object_detection.utils import config_util
import cv2 
import numpy as np
from matplotlib import pyplot as plt

class TensorCheck():
    def __init__(self):

        CUSTOM_MODEL_NAME = 'my_ssd_mobnet' 

        TF_RECORD_SCRIPT_NAME = 'generate_tfrecord.py'
        LABEL_MAP_NAME = 'label_map.pbtxt'

        paths = {
            'ANNOTATION_PATH': os.path.join(os.path.expanduser('~'), 'ROS_Works','TensorFlow','TFODCourse','Tensorflow', 'workspace','annotations'),
            'CHECKPOINT_PATH': os.path.join(os.path.expanduser('~'), 'ROS_Works','TensorFlow','TFODCourse','Tensorflow', 'workspace','models',CUSTOM_MODEL_NAME), 
        }

        files = {
            'PIPELINE_CONFIG':os.path.join(os.path.expanduser('~'), 'ROS_Works','TensorFlow','TFODCourse','Tensorflow', 'workspace','models', CUSTOM_MODEL_NAME, 'pipeline.config'),
            'LABELMAP': os.path.join(paths['ANNOTATION_PATH'], LABEL_MAP_NAME)
        }

        self.configs = config_util.get_configs_from_pipeline_file(files['PIPELINE_CONFIG'])
        self.detection_model = model_builder.build(model_config=self.configs['model'], is_training=False)
        self.category_index = label_map_util.create_category_index_from_labelmap(files['LABELMAP'])

        # Restore checkpoint
        ckpt = tf.compat.v2.train.Checkpoint(model=self.detection_model)
        ckpt.restore(os.path.join(paths['CHECKPOINT_PATH'], 'ckpt-3')).expect_partial()

    @tf.function
    def detect_fn(self, image):
        image, shapes = self.detection_model.preprocess(image)
        prediction_dict = self.detection_model.predict(image, shapes)
        detections = self.detection_model.postprocess(prediction_dict, shapes)
        return detections

#category_index = label_map_util.create_category_index_from_labelmap(files['LABELMAP'])

    def work_with_image(self, image_np):
        input_tensor = tf.convert_to_tensor(np.expand_dims(image_np, 0), dtype=tf.float32)
        detections = self.detect_fn(input_tensor)
        
        num_detections = int(detections.pop('num_detections'))
        detections = {key: value[0, :num_detections].numpy()
                    for key, value in detections.items()}
        detections['num_detections'] = num_detections

        # detection_classes should be ints.
        detections['detection_classes'] = detections['detection_classes'].astype(np.int64)

        label_id_offset = 1
        image_np_with_detections = image_np.copy()

        viz_utils.visualize_boxes_and_labels_on_image_array(
                    image_np_with_detections,
                    detections['detection_boxes'],
                    detections['detection_classes']+label_id_offset,
                    detections['detection_scores'],
                    self.category_index,
                    use_normalized_coordinates=True,
                    max_boxes_to_draw=5,
                    min_score_thresh=.8,
                    agnostic_mode=False)

        #cv2.imshow('object detection',  cv2.resize(image_np_with_detections, (800, 600)))
        return image_np_with_detections
        

def main():
    detector = TensorCheck()
    cap = cv2.VideoCapture(0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    while True:
        ret, frame = cap.read()
        image_np = np.array(frame)
        image_np_with_detections = detector.work_with_image(image_np)
        #cv2.imshow('object detection',  cv2.resize(image_np_with_detections, (800, 600)))
        cv2.imshow('object detection', image_np_with_detections)
        
        if cv2.waitKey(10) & 0xFF == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            break


if __name__ == "__main__":
    pass