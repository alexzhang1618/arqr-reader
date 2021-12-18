import cv2
from pyzbar import pyzbar
import numpy as np
import time
import webbrowser
import validators
import hashlib
import os.path
from os import path
from .LinkPreviewGenerator import generateLinkPreview

# Tuples storing green and blue BGR values.
green = (77, 202, 4)
blue = (255, 141, 47)

# Dictionary including parameters for sparse
# optical flow using the Lucas-Kanade algorithm.
# @param winSize The integration window size. Larger windows allow for smoother integration and are less sensitive to noise.
# @param maxLevel The maximum number of pyramids used in the algorithm.
# @param criteria The numbers 100 and 0.3 refer to the maximum number of iterations and epsilon. Smaller values finish faster but are less accurate.
optFlowParams = dict(winSize = (85,85), 
                     maxLevel = 4,
                     criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 100, 0.03))

# Given a list of four points, returns a tuple containing
# the integer coordinate of the center of the points.
# @param points A 2d array containing the coordinates for each of the four points.
# @return A tuple indicating the coordinate for the center of the points.
def findCenter(points):
    x = int(sum([k[0] for k in points])) // 4
    y = int(sum([k[1] for k in points])) // 4
    return (x, y)

# Finds the optimal position for text to be placed in the box.
# @param points A 2d array containing the coordinates for each of the four points.
# @return A tuple indicating the coordinate where the text should be placed.
def findTextPoint(points):
    x = min(points, key = lambda k: k[0])[0]
    y = min(points, key = lambda k: k[1])[1]
    return (x, y - 10)

# Draws a display box with text around the given points in the image.
# @param img The frame the display box will be depicted on.
# @param points A 2d array containing the coordinates for each of the four points.
# @param text The text to be displayed on the top of the display box. If empty, no text will be displayed.
def displayBox(img, points, text = ""):
    n = len(points)
    
    for i in range(n):
        cv2.line(img, tuple(points[i]), tuple(points[(i+1) % n]), green, 2)
        
    if text != "":
        cv2.putText(img, text, findTextPoint(points), cv2.FONT_HERSHEY_SIMPLEX, 0.5, green, 2)
        
    # Putting a dot in the middle
    cv2.circle(img, findCenter(points), 2, green, -1)

# Finds the angle between two vectors in radians.
# @param vector1 A NumPy vector storing the value of an edge of the display box.
# @param vector2 A NumPy vector storing the value of an adjacent edge in the display box.
# @return The angle between the edges in radians.
def angleBetween(vector1, vector2):
    unitVector1 = vector1 / np.linalg.norm(vector1)
    unitVector2 = vector2 / np.linalg.norm(vector2)
    dotProduct = np.dot(unitVector1, unitVector2)
    return np.arccos(dotProduct)

# Finds if the points given form the shape of a rectangle or parallelogram.
# Checks that the sum of the interior angles of the shape formed are close to
# 2pi radians and that opposite angles are of equal measure.
# @param points A 2d array containing the coordinates for each of the four points.
# @return A boolean indicating if the points form a rectangle/parallelogram or not.
def isRectangle(points):
    if points == None or len(points) != 4:
        return False
    
    edges = []
    
    n = len(points)
    for i in range(n):
        a = np.array(points[i])
        b = np.array(points[(i+1) % n])
        edges.append(b-a)
        
    angles = []
    for i in range(len(edges)):
        angles.append(angleBetween(edges[i], edges[(i+1) % n]))
    
    IATolerance = 0.1
    # Sum of interior angles are close to 2pi radians
    interiorAngles = abs(sum(angles) - 2 * np.pi) < IATolerance
    
    OATolerance = 0.3
    # Opposite angles are close to equal
    oppositeAngles = abs(angles[0] - angles[2]) < OATolerance and abs(angles[1] - angles[3]) < OATolerance
    
    return interiorAngles and oppositeAngles

# Creates a sha1 hash string for the given string.
# @param s The string to be encoded.
# @return A sha1 hash string corresponding to string s.
def sha1(s):
    return hashlib.sha1(s.encode()).hexdigest()

# Given the data for a code, generates a path for the image
# preview for the data to be stored.
# @param s The string data retrieved from a code.
# @return A string denoting the path where the image preview for the code will be stored.
def createPath(s):
    ret = os.path.join(os.getcwd(), "images", sha1(s) + ".png")
    return str(ret)

# Given the data from a code, returns True if an image preview
# for the code has already been created.
# @param s The string data retrieved from a code.
# @return A boolean indicating if an image preview has already been created for the data.
def imagePreviewExists(s):
    return path.exists(createPath(s))

# Generates a link preview in images/___.png if not previously created.
# @param data The string data retrieved from a code.
# @return A string denoting the path where the image preview for the code is stored.
def makePreview(data):
    previewPath = createPath(data)
    if not imagePreviewExists(data):
        generateLinkPreview(data, sha1(data) + ".png")
    return createPath(data)
    
# Calculates if the given coordinate lies within the box formed by the points given.
# @param x The integer for the x-coordinate.
# @param y The integer for the y-coordinate.
# @param pts A 2d array containing the coordinates for each of the four points.
# @return A boolean indicating if the coordinates lie within the pts given.
def coordinatesInRange(x, y, pts):
    xVals = [p[0] for p in pts]
    yVals = [p[1] for p in pts]
    xInRange = x >= min(xVals) and x <= max(xVals)
    yInRange = y >= min(yVals) and y <= max(yVals)
    return xInRange and yInRange

# Makes a new frame including an augmented reality preview for a given code.
# @param frame The frame to be used to create the new augmented reality frame.
# @param pts A 2d array containing the coordinates for each of the four points of the given code.
# @param path The path to find the created image preview for the code that is located by pts.
# @param imgWidth Width of the image frame
# @param imgHeight Height of the image frame
# @return A new frame with the image preview placed below the given code.
def makeARPreviewFrame(frame, pts, path, imgWidth, imgHeight):
    source = cv2.imread(path)
    srcH, srcW = source.shape[:2]
    pts = sorted(pts, key=lambda x: x[0])
    # Organizing the points given by corner: top left, bottom left, top right, bottom right.
    ptTL = min(pts[:2], key=lambda x: x[1])
    ptBL = max(pts[:2], key=lambda x: x[1])
    ptTR = min(pts[2:], key=lambda x: x[1])
    ptBR = max(pts[2:], key=lambda x: x[1])
    
    centerPt = (np.array(ptBR) + np.array(ptBL)) / 2
    lrDisplacement = (np.array(ptBR) - np.array(ptBL)) * 2
    tbDisplacement = (np.array(ptTL) - np.array(ptBL)) * 1
    
    # Calculating the points on the frame where the preview image will be placed.
    ptTL = (centerPt - lrDisplacement - tbDisplacement * 0.1).astype(int)
    ptTR = (centerPt + lrDisplacement - tbDisplacement * 0.1).astype(int)
    ptBL = (ptTL - tbDisplacement).astype(int)
    ptBR = (ptTR - tbDisplacement).astype(int)
    
    # destinationMatrix: A matrix indicating the points on the frame where the preview image will be displayed.
    destinationMatrix = [ptTL, ptTR, ptBR, ptBL]
    destinationMatrix = np.array(destinationMatrix)
    
    # sourceMatrix: A matrix indicating the points for the preview image.
    sourceMatrix = np.array([[0, 0], [srcW, 0], [srcW, srcH], [0, srcH]])
    
    h, status = cv2.findHomography(sourceMatrix, destinationMatrix)
    warp = cv2.warpPerspective(source, h, (imgWidth, imgHeight))
    
    mask = np.zeros((imgHeight, imgWidth), dtype="uint8")
    cv2.fillConvexPoly(mask, destinationMatrix.astype("int32"), (255, 255, 255), cv2.LINE_AA)
    
    scaledMask = mask.copy() / 255.0
    scaledMask = np.dstack([scaledMask] * 3)
    
    warpMultiplied = cv2.multiply(warp.astype("float"), scaledMask)
    imgMultiplied = cv2.multiply(frame.astype("float"), 1.0 - scaledMask)
    
    returnFrame = cv2.add(warpMultiplied, imgMultiplied)
    returnFrame = returnFrame.astype("uint8")
    return returnFrame

# Formats data into a valid url
# @param data A string containing data from a QR code
# @return Valid URL containing the data
def format_data(data):
    if not data or not validators.url(data):
        return "https://www.google.com/search?q={}".format(data)
    return data

class ImageProcessor():
    def __init__(self):
        # Boolean value storing if a code has been detected recently.
        self.qrExists = False
        # Time object denoting the last time a code has been detected.
        self.lastSeen = None
        # List storing previously found points for codes, used in the optical flow algorithm.
        self.prevPoints = []
        # Object storing the last frame when a code was detected.
        self.prevImage = None
        # List storing the formatted text values of previously detected codes for display purposes.
        self.prevText, self.prevData = [], []
        # Set storing data values that augmented reality previews will be generated for.
        self.showPreview = set()
        
    # Processes a single frame and returns the new frame with 
    # a display if a QR code is detected
    # @param frame The image frame to be processed
    # @param AR A boolean storing if an AR preview should be added
    # @return The processed frame, a boolean storing if a code 
    # is found, and the data from the code
    def processImage(self, frame, AR=False):
        codes = pyzbar.decode(frame)
        if len(codes) == 0 and self.qrExists:
            # A code has been detected previously but is not found currently on this frame.
            # Optical flow will be used with the previously found points to draw detection boxes.
            for j in range(len(self.prevPoints)):
                point = self.prevPoints[j]
                # Argument types are changed to fit the optical flow algorithm parameters.
                p1 = [[[np.float32(i[0]), np.float32(i[1])]] for i in point]
                p = np.array(p1)
                f = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                pI = cv2.cvtColor(self.prevImage, cv2.COLOR_BGR2GRAY)
                
                newPoints, status, error = cv2.calcOpticalFlowPyrLK(pI, f, p, None, **optFlowParams)
                
                # Change the types of the points to fit the arguments of displayBox()
                newPoints = [[int(i[0][0]), int(i[0][1])] for i in newPoints]
                
                # Computing the distance between center of old points and center of new points.
                newCenter = np.array(findCenter(newPoints))
                oldCenter = np.array(findCenter(self.prevPoints[j]))
                dist = np.linalg.norm(newCenter - oldCenter)
                
                noSuddenMovement = dist < 150
                    
                # Only display the box if there's no sudden change in placement and the shape is correct.
                if isRectangle(newPoints) and noSuddenMovement:
                    if AR and self.prevData[j] in self.showPreview:
                        imgWidth, imgHeight = frame.shape[1], frame.shape[2]
                        frame = makeARPreviewFrame(frame, self.prevPoints[j], makePreview(self.prevData[j]), imgWidth, imgHeight)
                        displayBox(frame, newPoints)
                        return frame, True, self.prevData[j]
                    else:
                        displayBox(frame, newPoints, self.prevText[j])
                        return frame, True, self.prevData[j]
                    
                # Optical flow times out after one full second of no code detection.
                # QR code may no longer be in frame, time out and reset everything.
                elif time.time() - self.lastSeen > 1:
                    self.qrExists = False
                    self.lastSeen = None
                    self.prevPoints.clear()
                    self.prevText.clear()
                    self.prevData.clear()
                    self.prevImage = None
        
        # Codes have been detected, all "prev" variables can be updated.
        elif len(codes) > 0:
            self.qrExists = True
            self.lastSeen = time.time()
            self.prevPoints.clear()
            self.prevText.clear()
            self.prevData.clear()
            self.prevImage = frame
        
            for code in codes:
                points = code.polygon
                self.prevPoints.append(points)
                data = code.data.decode("utf-8")
                codeType = code.type
            
                # Preparing text to be displayed. (Text shows type of code and the data associated with it)
                text = "{0}: {1}".format(codeType, data)
                self.prevText.append(text)
                self.prevData.append(data)
                # If the data needs to be showed in the AR preview, update the frame to include the preview.
                # Performance is slower when AR previews need to be shown.
                if AR and data in self.showPreview:
                    imgWidth, imgHeight = frame.shape[1], frame.shape[2]
                    frame = makeARPreviewFrame(frame, points, makePreview(data), imgWidth, imgHeight)
                    displayBox(frame, points)
                else:
                    displayBox(frame, points, text)
            return frame, True, self.prevData[0]
        return frame, False, None

# Main loop for the ARQR application
def main():
    # VideoCapture object that opens the default camera.
    vidCap = cv2.VideoCapture(0)
    # Boolean value storing if a code has been detected recently.
    qrExists = False
    # Time object denoting the last time a code has been detected.
    lastSeen = None
    # List storing previously found points for codes, used in the optical flow algorithm.
    prevPoints = []
    # Object storing the last frame when a code was detected.
    prevImage = None
    # List storing the formatted text values of previously detected codes for display purposes.
    prevText = []
    # List storing the data values of previously detected codes.
    prevData = []
    # Set storing data values that augmented reality previews will be generated for.
    showPreview = set()
    # Integer value storing the pixel width of the frame.
    imgWidth = -1
    # Integer value storing the pixel height of the frame.
    imgHeight = -1

    # Reads mouse input to detect if a QR code box has been clicked on the display.
    # A left click opens a web browser window navigating to the QR code data.
    # A right click toggles the QR code preview for all codes including the selected code's data.
    # @param event An object indicating the mouse input that occured on the display.
    # @param x The integer for the x-coordinate where the mouse input occured.
    # @param y The integer for the y-coordinate where the mouse input occurred.
    # @param flags An object storing the MouseEventFlags for the mouse input.
    # @param param An optional parameter. Usually left as None.
    def clickQR(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            n = len(prevPoints)
            for i in range(n):
                if coordinatesInRange(x, y, prevPoints[i]):
                    webbrowser.open_new_tab(format_data(prevData[i]))
                    return
        elif event == cv2.EVENT_RBUTTONDOWN:
            n = len(prevPoints)
            for i in range(n):
                if coordinatesInRange(x, y, prevPoints[i]):
                    if prevData[i] in showPreview:
                        showPreview.remove(prevData[i])
                        return
                    else:
                        makePreview(prevData[i])
                        showPreview.add(prevData[i])
                        return

    if not vidCap.isOpened():
        print("Error: Unable to open camera")
        
    else:
        imgWidth = int(vidCap.get(3))
        imgHeight = int(vidCap.get(4))
        while True:
            isRead, frame = vidCap.read()
            
            if isRead:
                codes = pyzbar.decode(frame)
                
                if len(codes) == 0 and qrExists:
                    # A code has been detected previously but is not found currently on this frame.
                    # Optical flow will be used with the previously found points to draw detection boxes.
                    for j in range(len(prevPoints)):
                        point = prevPoints[j]
                        # Argument types are changed to fit the optical flow algorithm parameters.
                        p1 = [[[np.float32(i[0]), np.float32(i[1])]] for i in point]
                        p = np.array(p1)
                        f = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        pI = cv2.cvtColor(prevImage, cv2.COLOR_BGR2GRAY)
                        
                        newPoints, status, error = cv2.calcOpticalFlowPyrLK(pI, f, p, None, **optFlowParams)
                        
                        # Change the types of the points to fit the arguments of displayBox()
                        newPoints = [[int(i[0][0]), int(i[0][1])] for i in newPoints]
                        
                        # Computing the distance between center of old points and center of new points.
                        newCenter = np.array(findCenter(newPoints))
                        oldCenter = np.array(findCenter(prevPoints[j]))
                        dist = np.linalg.norm(newCenter - oldCenter)
                        
                        noSuddenMovement = dist < 150
                            
                        # Only display the box if there's no sudden change in placement and the shape is correct.
                        if isRectangle(newPoints) and noSuddenMovement:
                            if prevData[j] in showPreview:
                                frame = makeARPreviewFrame(frame, prevPoints[j], makePreview(prevData[j]), imgWidth, imgHeight)
                                displayBox(frame, newPoints)
                            else:
                                displayBox(frame, newPoints, prevText[j])
                            # Green dot in the top left of the screen flashes when optical flow is used.
                            cv2.circle(frame, (10, 10), 5, green, -1)
                            
                        # Optical flow times out after one full second of no code detection.
                        # QR code may no longer be in frame, time out and reset everything.
                        elif time.time() - lastSeen > 1:
                            qrExists = False
                            lastSeen = None
                            prevPoints.clear()
                            prevText.clear()
                            prevData.clear()
                            prevImage = None
                
                # Codes have been detected, all "prev" variables can be updated.
                elif len(codes) > 0:
                    qrExists = True
                    lastSeen = time.time()
                    prevPoints.clear()
                    prevText.clear()
                    prevData.clear()
                    prevImage = frame
                
                    for code in codes:
                        points = code.polygon
                        prevPoints.append(points)
                        data = code.data.decode("utf-8")
                        codeType = code.type
                    
                        # Preparing text to be displayed. (Text shows type of code and the data associated with it)
                        text = "{0}: {1}".format(codeType, data)
                        prevText.append(text)
                        prevData.append(data)
                        # If the data needs to be showed in the AR preview, update the frame to include the preview.
                        # Performance is slower when AR previews need to be shown.
                        if data in showPreview:
                            frame = makeARPreviewFrame(frame, points, makePreview(data), imgWidth, imgHeight)
                            displayBox(frame, points)
                        else:
                            displayBox(frame, points, text)
                    
                    # Blue dot in the top left of the screen flashes when a code is detected.
                    cv2.circle(frame, (10, 10), 5, blue, -1)
                
                cv2.imshow("Display", frame)
                cv2.setMouseCallback("Display", clickQR)
                key = cv2.waitKey(1)
            
                # Loop times out when the 'q' key on the keyboard is pressed.
                if key == ord('q'):
                    break
            else:
                break
        
    vidCap.release()
    cv2.destroyAllWindows()
    print("Done")

if __name__ == '__main__':
    main()