import cv2 as cv
import time
 
# start video cap on webcam
cap = cv.VideoCapture(0)
if not cap.isOpened():
    print("cannot open cam")
    exit()

# Properties
frame_width = int(cap.get(3))
frame_height = int(cap.get(4))
fps = cap.get(cv.CAP_PROP_FPS)
# start background video
bg_vid = cv.VideoCapture('bgVID.mp4')
# initialize video writer
fourcc = cv.VideoWriter_fourcc(*'mp4v')
out = cv.VideoWriter("output.mp4", fourcc, fps, (frame_width, frame_height))
out_orig = cv.VideoWriter("original.mp4", fourcc, fps, (frame_width, frame_height))

# Create a named window and set it to fullscreen
cv.namedWindow("FullScreen", cv.WND_PROP_FULLSCREEN)
cv.setWindowProperty("FullScreen", cv.WND_PROP_FULLSCREEN, cv.WINDOW_FULLSCREEN)
# read the frame of the current video feed
ret1, frame1 = cap.read()
if not ret1:
    print("Can't receive frame from first frame (stream end?). Exiting ...")
    exit()

frame1 = cv.cvtColor(frame1, cv.COLOR_BGR2GRAY)
inverted = cv.bitwise_not(frame1)


mask_range = 10

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    # save original video
    out_orig.write(frame)
    # grayscale and flip
    frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)  
    frame = cv.flip(frame, 1)
    # read current frame of background video
    ret2, img = bg_vid.read()
    # Restart video when it ends
    if not ret2:
        bg_vid.set(cv.CAP_PROP_POS_FRAMES, 0)
        continue
    if not ret:
        print("Can't receive frame from webcam (stream end?). Exiting ...")
        break
    # match background size to the webcam
    img = cv.resize(img, (frame.shape[1], frame.shape[0]))
    img_inv = cv.bitwise_not(img)

    # blend the past inverted and current normal frames to get motion-based image
    blended = cv.addWeighted(frame, 0.5, inverted, 0.5, 0)
    # make masks
    mask = cv.inRange(blended, 255/2-mask_range, 255/2+mask_range)
    mask_inv = cv.bitwise_not(mask)
    # Bitwise-AND: mask and original image
    res = cv.bitwise_and(img, img, mask=mask_inv)
    res_inv = cv.bitwise_and(img_inv, img_inv, mask=mask_inv)
    # Display the resulting frames

    cv.imshow("FullScreen", res_inv)
    out.write(res_inv)

    # save the current frame inverted to use next round
    inverted = cv.bitwise_not(frame)

    # quit if user presses "q"
    if cv.waitKey(1) == ord('q'):
        print("manual quit")
        break
    

# When everything done, release the capture
cap.release()
out.release()
out_orig.release()
cv.destroyAllWindows()