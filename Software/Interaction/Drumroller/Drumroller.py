import numpy as np
import cv2

def getFrame():
    ok, frame = cap.read()
    
    if not ok:
        print('Error: Cannot read webcam!')
        sys.exit()
    
    frame = cv2.flip(frame, 1)
    return frame

def initializeTracker():
    # tracker = cv2.TrackerBoosting_create()
    # tracker = cv2.TrackerMIL_create()
    # tracker = cv2.TrackerKCF_create()
    # tracker = cv2.TrackerTLD_create()
    # tracker = cv2.TrackerMedianFlow_create()
    tracker = cv2.TrackerCSRT_create()
    # tracker = cv2.TrackerMOSSE_create()
    
    bbox = cv2.selectROI(frame, False)
    ok = tracker.init(frame, bbox)
    
    if not ok:
        print('Error: Unable to initialize tracker!')
        sys.exit()
        
    return tracker
    
def track(tracker, frame):
    ok, bbox = tracker.update(frame)    
    p1 = (int(bbox[0]), int(bbox[1]))
    p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
    cv2.rectangle(frame, p1, p2, (255,0,0), 2, 1)
    

def main():
    tracker = initializeTracker()

    while(True):
        frame = getFrame()
        track(tracker, frame)
        cv2.imshow('frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


cap = cv2.VideoCapture(0)
main()
