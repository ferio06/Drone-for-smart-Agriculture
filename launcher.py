import threading
import time

from djitellopy import tello
from time import sleep
import time
import numpy as np
#import keyPressModule as kp
import cv2
from elements.yolo import OBJ_DETECTION


#kp.init()
me = tello.Tello()
me.connect()
print("battery level" + str(me.get_battery()))
global img

# sick : 0,2,3,4,7,8,9,11,12,17,19,20,21,22,23,24,26,27,28
# present decease:1,5,6,10,13,14,15,16,18,25,29
Object_classes_name = ['Apple Scab Leaf', 'Apple leaf', 'Apple rust leaf', 'Bell_pepper leaf spot', 'Bell_pepper leaf', 'Blueberry leaf', 'Cherry leaf', 'Corn Gray leaf spot',
'Corn leaf blight', 'Corn rust leaf','Peach leaf','Potato leaf early blight','Potato leaf late blight', 'Potato leaf',
'Raspberry leaf', 'Soyabean leaf', 'Soybean leaf','Squash Powdery mildew leaf', 'Strawberry leaf','Tomato Early blight leaf',
'Tomato Septoria leaf spot', 'Tomato leaf bacterial spot', 'Tomato leaf late blight','Tomato leaf mosaic virus',
'Tomato leaf yellow virus','Tomato leaf', 'Tomato mold leaf','Tomato two spotted spider mites leaf','grape leaf black rot', 'grape leaf' ]
Object_classes = ['sick', 'ok', 'sick', 'sick', 'sick', 'ok', 'ok', 'sick','sick', 'sick','Peach leaf','ok','sick', 'sick','ok', 'ok', 'ok','sick', 'ok','sick','sick', 'sick', 'sick','sick','sick','ok', 'sick','sick','sick', 'ok' ]
Object_colors = list(np.random.rand(80,3)*255)
Object_detector = OBJ_DETECTION('weights/best.pt', Object_classes)


me.streamoff()
sleep(3)



me.enable_mission_pads()
me.set_mission_pad_detection_direction(0)
#sleep(3)
length = 90
landPortion = int(length / 3)
direction = "clockwise"

exitFlag = 0



class imageProcessing(threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
    def run(self):
        print("Starting " + self.name)
        while True:
            frame = me.get_frame_read().frame
            frame = cv2.resize(frame, (800, 550))
            frame = cv2.flip(frame, 1)  # vertical
            # window_handle = cv2.namedWindow("Tello Camera", cv2.WINDOW_AUTOSIZE)
            # detection process
            objs = Object_detector.detect(frame)

            # plotting
            for obj in objs:
                # print(obj)
                label = obj['label']
                score = obj['score']
                [(xmin, ymin), (xmax, ymax)] = obj['bbox']
                color = Object_colors[Object_classes.index(label)]
                frame = cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), color, 2)
                frame = cv2.putText(frame, f'{label} ({str(score)})', (xmin, ymin), cv2.FONT_HERSHEY_SIMPLEX, 0.75,
                                    color, 1,
                                    cv2.LINE_AA)

            cv2.imshow("Tello Camera", frame)
            cv2.imwrite("result.jpg", frame)
            cv2.waitKey(1)


class pathPlanning(threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.length = length
        self.direction = direction
        self.landPortion = landPortion
        self.threadID = threadID
        self.name = name
        self.counter = counter

    def run(self):
        print("Starting path planning " + self.name)
        me.go_xyz_speed_yaw_mid(self.length, 0, 60, 10, 0, 1, 2)
        sleep(2)
        # start
        lengthCovered = 0
        while lengthCovered < self.length:
            me.go_xyz_speed(self.landPortion, 0, 0, 10)
            #me.move_forward(int(self.landPortion))
            lengthCovered = lengthCovered + self.landPortion
            if self.direction == "clockwise":
                me.rotate_clockwise(90)
                self.direction = "anticlockwise"
            else:
                me.rotate_counter_clockwise(90)
                self.direction = "clockwise"
            sleep(2)
            me.go_xyz_speed(self.length, 0, 0, 10)
            #me.move_forward(self.length)
            sleep(2)
            if self.direction == "clockwise":
                me.rotate_clockwise(90)
            else:
                me.rotate_counter_clockwise(90)
            sleep(2)
            if self.length - lengthCovered == self.landPortion:

                currentDetectedMissionPadId = me.get_mission_pad_id()
                print("current detection mission pad id", currentDetectedMissionPadId)
                if currentDetectedMissionPadId == 3:
                    me.go_xyz_speed_mid(0, 0, 60, 10, 3)  # go to m3
                    sleep(2)
                    me.rotate_clockwise(90)
                    sleep(2)
                    me.go_xyz_speed_yaw_mid(self.length, 0,60,10, 0, 3, 4)  # go to m4
                elif currentDetectedMissionPadId == 4:
                    me.go_xyz_speed_mid(0, 0, 60,10, 4)
                    sleep(2)
                lengthCovered = self.length
                me.streamoff()
                sleep(2)
                me.land()
        print("Exiting " + self.name)


'''def print_time(threadName, counter, delay):
    while counter:
        if exitFlag:
            threadName.exit()
        time.sleep(delay)
        print("%s: %s" % (threadName, time.ctime(time.time())))
        counter -= 1
'''

me.streamon()
sleep(2)



# Create new threads
thread1 = imageProcessing(1, "image-processing", 1)
# Start new Threads
thread1.start()
sleep(12)
me.takeoff()
sleep(2)
thread2 = pathPlanning(2, "path-planning", 3)

thread2.start()

print("Exiting Main Thread")
