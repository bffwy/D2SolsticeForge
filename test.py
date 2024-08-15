import cv2
import numpy as np
import os
import sys
from PIL import ImageGrab


def show(fp):

    # 读取图像
    # image = cv2.imread(fp)
    screenshot = ImageGrab.grab(bbox=[10, 10, 1306, 769])
    image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 高斯滤波
    gray_blurred = cv2.GaussianBlur(gray, (9, 9), 0)

    # 使用Hough Circle Transform检测圆形
    circles = cv2.HoughCircles(
        gray_blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=30, param1=50, param2=15, minRadius=13, maxRadius=14
    )

    if circles is not None:
        circles = np.uint16(np.around(circles))

        for i in circles[0, :]:
            # 绘制圆形边界
            print("radius", i[2])
            cv2.circle(image, (i[0], i[1]), i[2], (0, 255, 0), 2)
            # 绘制圆心
            cv2.circle(image, (i[0], i[1]), 2, (0, 0, 255), 3)

    # 显示结果
    cv2.imshow("Detected Circles", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


show(None)
# parent_dir_name = os.path.dirname(os.path.realpath(__file__))
# print(parent_dir_name)
# fp = os.path.join(parent_dir_name, "debug")

# for root, dirs, files in os.walk(fp):
#     for file in files:
#         fp = os.path.join(root, file)
#         show(fp)
