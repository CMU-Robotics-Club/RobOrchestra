import numpy as np
import cv2
import mido

def getFrame():
    ok, frame = cap.read()
    
    if not ok:
        print('Error: Cannot read webcam!')
        sys.exit()
    
    frame = cv2.flip(frame, 1)
    return frame

def initializeTracker(frame):
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
    return p1[1]
    

def main():
    frame = getFrame()
    tracker = initializeTracker(frame)
    #mido seems to need a port name in order to send messages,
    #so we put mio here but we're not sure about it
    port = mido.open_output('mio')
    msg = mido.Message('note_on', note=36)
    #keep track of the last position and last direction you had
    #if your last direction was up and your current direction is
    #down, then you've made a beat
    n = 0
    prevDir = "up"
    prevPosition = 0
    curDir = "up"
    
    while(True):
        frame = getFrame()
        curPosition = track(tracker, frame)
        #print(curPosition)
    
        if n != 0:
            if curPosition - prevPosition > 15:
                curDir = "down"
            elif curPosition - prevPosition < -15:
                curDir = "up"
            if prevDir == "up" and curDir == "down":
                print("drum_beat")
                port.send(msg)
        prevPosition = curPosition
        prevDir = curDir
            
        cv2.imshow('frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        n += 1

    cap.release()
    cv2.destroyAllWindows()


cap = cv2.VideoCapture(0)
main()
