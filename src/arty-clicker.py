import sys
import time

import numpy as np
import pyautogui
import win32com.client
import win32con
import win32gui
import win32ui
import cv2 as cv
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QInputDialog,
    QCheckBox,
)
from PIL.Image import Image


class MainWindow(QMainWindow):
    def __init__(self):
        """Setting up starting GUI"""
        QMainWindow.__init__(self)
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.X11BypassWindowManagerHint
        )
        self.setGeometry(
            QtWidgets.QStyle.alignedRect(
                QtCore.Qt.LeftToRight,
                QtCore.Qt.AlignCenter,
                QtCore.QSize(200, 200),
                QtWidgets.qApp.desktop().availableGeometry(),
            )
        )
        self.setWindowTitle('Artillery Clicker')

        self.label = QLabel(self)
        self.label.setText("Factorio artillery rapid fire")
        self.label.resize(150, 15)
        self.label.move(35, 20)

        self.fireBtn = QPushButton("Fire", self)
        self.fireBtn.resize(100, 32)
        self.fireBtn.move(50, 50)
        self.fireBtn.clicked.connect(self.fireHandler)

        self.speedBtn = QPushButton("Set Speed", self)
        self.speedBtn.resize(100, 32)
        self.speedBtn.move(50, 100)
        self.speedBtn.clicked.connect(self.setSpeed)
        
        self.biterFilter = QCheckBox('Fire only in turret coverage?', self)
        self.biterFilter.resize(150, 32)
        self.biterFilter.move(32, 125)
        self.biterFilter.toggle()
        
        # Info panel
        
        self.speedLabel = QLabel(self)
        self.speedLabel.setText("Speed: 15.0 CPS")
        self.speedLabel.resize(150, 15)
        self.speedLabel.move(50, 150)

    def setSpeed(self):
        speedInput = QInputDialog.getDouble(
            self,
            "Artillery clicker speed",
            "How many clicks per second?",
            value=4,
            min=0.1,
            max=120,
            decimals=1,
        )
        if speedInput[1]:
            self.speedLabel.setText(f"Speed: {speedInput[0]} CPS" )
            pyautogui.PAUSE = 1 / speedInput[0]
            
        print(speedInput)

    def changeTitle(self, state):

        print(self.biterFilter.checkState())
        if state == QtCore.Qt.Checked:
            self.biterFilterState = True
        else:
            self.setWindowTitle(' ')



    def fireHandler(self) -> None:
        win32gui.EnumWindows(winEnumHandler, self)
        print("BANG")


def screenshot(windowID: int = None) -> Image:
    if not windowID:
        print("No window given!")
        exit(1)
    shell = win32com.client.Dispatch("WScript.Shell")
    shell.SendKeys("")
    win32gui.SetForegroundWindow(windowID)
    win32gui.BringWindowToTop(windowID)
    x, y, x1, y1 = win32gui.GetClientRect(windowID)
    x, y = win32gui.ClientToScreen(windowID, (x, y))
    x1, y1 = win32gui.ClientToScreen(windowID, (x1 - x, y1 - y))
    image: Image = pyautogui.screenshot(region=(x, y, x1, y1))
    return image


def winEnumHandler(windowID: int, ctx) -> None:
    if not win32gui.IsWindowVisible(windowID):
        # Window is not visible
        return
    if "factorio 1" not in win32gui.GetWindowText(windowID).lower():
        # Factorio window not found
        return
    
    pyautogui.PAUSE = 1 / float(str(ctx.speedLabel.text()).split(" ")[1])

    print(hex(windowID), win32gui.GetWindowText(windowID))

    image = np.array(screenshot(windowID))
    
    # RGB Ranges for biter base 'Red'
    if ctx.biterFilter.checkState(): # turret coverage biter base color values
        lowerColorRange = np.array([158, 19, 19])
        upperColorRange = np.array([255, 25, 28])
    else: # Non turret coverage biter base color values
        lowerColorRange = np.array([153, 15, 15])
        upperColorRange = np.array([255, 24, 25])

    mask = cv.inRange(image, lowerColorRange, upperColorRange)
    kernel = np.ones((3, 3), np.uint8)
    mask_erode = cv.erode(mask, kernel, iterations=2)
    masked = cv.bitwise_and(image, image, mask=mask_erode)
    contours, _ = cv.findContours(
        image=mask_erode, mode=cv.RETR_TREE, method=cv.CHAIN_APPROX_NONE
    )

    image_copy = masked.copy()
    coordsToShoot = []
    for c in contours:
        if cv.contourArea(c) > 0:
            M = cv.moments(c)
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            coordsToShoot.append((cX, cY))
            # draw the contour and center of the shape on the image
            cv.drawContours(
                image=image_copy,
                contours=[c],
                contourIdx=-1,
                color=(0, 255, 0),
                thickness=2,
                lineType=cv.LINE_AA,
            )
            cv.circle(image_copy, (cX, cY), 7, (255, 255, 255), -1)
            cv.putText(
                image_copy,
                "center",
                (cX - 20, cY - 20),
                cv.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                2,
            )
    print(coordsToShoot)

    x, y, x1, y1 = win32gui.GetClientRect(windowID)
    x, y = win32gui.ClientToScreen(windowID, (x, y))
    x1, y1 = win32gui.ClientToScreen(windowID, (x1 - x, y1 - y))

    cv.destroyAllWindows()
    # cv.imshow("Computer Vision", image)
    #cv.imshow("None approximation", image_copy)

    # cv.imshow("mask",mask)
    #cv.imshow("mask_erode", mask_erode)
    #cv.imshow("masked", masked)

    def click(button) -> None:
        """Preforms a click action"""
        pyautogui.mouseDown(button=button)
        pyautogui.mouseUp(button=button)

    time.sleep(2)
    # pyautogui.PAUSE = .5
    pyautogui.FAILSAFE = True
    for c in coordsToShoot:
        pyautogui.moveTo(x=(c[0] + x), y=(y + c[1]))
        click("left")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MainWindow()
    myWindow.show()
    sys.exit(app.exec_())
