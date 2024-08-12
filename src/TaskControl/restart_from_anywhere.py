import cv2
import numpy as np

# 读取图像
image = cv2.imread("D:/Work/git_work_space/d2-auto-work/screenshot.jpg")
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# 高斯滤波
gray_blurred = cv2.GaussianBlur(gray, (9, 9), 0)

# 使用Hough Circle Transform检测圆形
circles = cv2.HoughCircles(
    gray_blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=20, param1=50, param2=30, minRadius=16, maxRadius=20
)

if circles is not None:
    circles = np.uint16(np.around(circles))

    for i in circles[0, :]:
        # 绘制圆形边界
        print(f"find line: {i[0]}, {i[1]}, {i[2]}")
        cv2.circle(image, (i[0], i[1]), i[2], (0, 255, 0), 2)
        # 绘制圆心
        cv2.circle(image, (i[0], i[1]), 2, (0, 0, 255), 3)

# 显示结果
cv2.imshow("Detected Circles", image)
cv2.waitKey(0)
cv2.destroyAllWindows()
