import numpy as np
import cv2
import mido

key_press_circle = {center:(0,0), radius:3}
key_regions = {((), ()): 60, ((), ()): 62, ((), ()): 64, ((), ()): 65, ((), ()): 67, ((), ()): 69, ((), ()): 71, ((), ()): 72}

def findKey():
    (Cx, Cy) = key_press_circle[center]
    R = key_press_circle[radius]
    for k in key_regions:
        (x1,y1) = k[0]
        (x2,y2) = k[1]
        # assume x1 < x2 and y1 < y2
        if (Cy > y1 and Cy < y2 and Cx > x1 and Cx < x2):
            return k
        if (abs(Cx - x1) <= R and (Cy > y1 and Cy < y2 or edge_case(Cx, Cy, x1, y1, x2, y2, R))):
            return k
    return None

def edge_case(Cx, Cy, x1, y1, x2, y2, R):
    return (((Cy - y1)**2 + (Cx - x1)**2) <= R*R) or (((Cy - y2)**2 + (Cx - x1)**2) <= R*R) or (((Cy - y1)**2 + (Cx - x2)**2) <= R*R) or (((Cy - y2)**2 + (Cx - x2)**2) <= R*R)


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
    key_press_circle[center] = ((p1[0] + p2[0])/2, (p1[1] + p2[1])/2)
    cv2.circle(frame, key_press_circle[center], key_press_circle[radius], (0,255,0), -1)
    

def main():
    frame = getFrame()
    tracker = initializeTracker(frame)
    port = mido.open_output('mio')
    msg = mido.Message('note_on', note=60)
    prev_key = None

    while(True):
        print("msg note", msg.note)
        frame = getFrame()
        track(tracker, frame)
        cv2.imshow('frame', frame)

        check_press = findKey()
        if (check_press != None and check_press != prev_key):
            msg = mido.Message('note_on', note=key_regions[check_press])
            port.send(msg)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


cap = cv2.VideoCapture(0)
main()
