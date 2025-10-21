import cv2
import numpy as np
import matplotlib.pyplot as plt
import mss
import time
import math
import sys

# h = 1800; w = 2880

def game_ended(area,x,y):
    print(area, x, y)
    return math.floor(area) == 1044 and (x in [1604, 1117, 1229, 119, 1727, 1642]) and y == 656

def contour_detection_visualization_local(img_path=None, ii = 1, threshold_value=50, crop_bottom=75, color = (0, 255, 0), tolerance=50, t_len = 800, add_angle = 0):
    img = cv2.imread(img_path)
    img = img[:1800 - crop_bottom, :, :]
    md_height, md_width = 1800//2, 2880//2
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    plt.figure(figsize=(15, 10))
    plt.subplot(231), plt.imshow(img_rgb), plt.title('Original Image')
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    plt.subplot(232), plt.imshow(gray, cmap='gray'), plt.title('Grayscale Image')
    _, thresh = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY)
    plt.subplot(233), plt.imshow(thresh, cmap='gray'), plt.title(f'Binary Threshold ({threshold_value})')
    edges = cv2.Canny(gray, 50, 150)
    plt.subplot(234), plt.imshow(edges, cmap='gray'), plt.title('Edge Detection')
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # contours, hierarchy = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    all_contours = img_rgb.copy()
    cv2.drawContours(all_contours, contours, -1, color, 2)
    plt.subplot(235), plt.imshow(all_contours), plt.title(f'All Contours ({len(contours)})')
    filtered_img = img_rgb.copy()
    shapes = []

    CX, CY = None, None
    
    for contour in contours:
        area = cv2.contourArea(contour)
        # print(f"cnt area: {area}", end=' ')
        epsilon = 0.03 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        M = cv2.moments(contour)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            # print(f"cent: x={cX}, y={cY}")
            if 1100 <= cX <= 1770 and 575 <= cY <= 1190 and area >= 850 and area <= 2700:
                # print(f"cont area: {area} cent: x={cX}, y={cY}")
                CX = cX
                CY = cY
                shapes.append(contour)
                cv2.putText(filtered_img, f"{len(approx)} sides", (cX - 20, cY - 20), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                cv2.drawContours(filtered_img, [approx], -1, color, 3)
                cv2.circle(filtered_img, (cX, cY), 7, (0, 0, 0), -1)
                break

    plt.subplot(236), plt.imshow(filtered_img), plt.title('Classified Shapes')
    plt.tight_layout()
    plt.show()

    plt.figure(figsize=(15, 8))
    
    other_img = img_rgb.copy()
    cv2.drawContours(other_img, shapes, -1, color, 2)

    plt.subplot(111), plt.imshow(other_img), plt.title(f'Shapes ({len(shapes)})')
    plt.tight_layout()
    plt.show()

    plt.figure(figsize=(15, 8))

    other_img = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

    if CX is not None and CY is not None:
        direction = np.array([CX - md_width, CY - md_height])
        length = np.linalg.norm(direction)
        unit_vec = direction / length
        base_angle = np.arctan2(unit_vec[1], unit_vec[0]) + add_angle

        tdx, tdy = np.cos(base_angle), np.sin(base_angle)
        tx, ty = md_width + tdx * length, md_height + tdy * length
        while np.array_equal(other_img[int(ty), int(tx)], [255, 255, 255]):
            length += 1
            tx += tdx 
            ty += tdy
        
        length += 25

        for i in range(6):
            angle = base_angle + np.deg2rad(60 * i)
            dx = np.cos(angle)
            dy = np.sin(angle)

            x, y, tlength = md_width + dx * length, md_height + dy * length, length

            while 0 <= int(x) < other_img.shape[1] and 0 <= int(y) < other_img.shape[0] and tlength < t_len:
                pixel = other_img[int(y), int(x)]
                if np.array_equal(pixel, [255, 255, 255]):
                    break
                x += dx
                y += dy
                tlength += 1
            
            # print(tlength)
            end_point = (int(x), int(y))
            cv2.line(other_img, (md_width, md_height), end_point, color, 2)
    
    plt.subplot(111), plt.imshow(other_img), plt.title(f'Shapes ({len(shapes)})')
    plt.tight_layout()
    plt.show()
    return contours, shapes

def contour_detection_visualization_mss(f=None, img_path=None, ii=1, threshold_value=50, crop_bottom=75, color=(0, 255, 0),tolerance=50, t_len = 800, add_angle=0, self_adjust = 40, pre = None):
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        screenshot = np.array(sct.grab(monitor))
    screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
    height, width, _ = screenshot.shape
    md_height, md_width = height//2, width//2
    img = screenshot[:height - crop_bottom, :, :]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cnts = 0

    CX, CY, Area = None, None, None

    players = []
    
    for contour in contours:
        area = cv2.contourArea(contour)
        M = cv2.moments(contour)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            if 1100 <= cX <= 1770 and 575 <= cY <= 1190 and area >= 900 and area <= 2700:
                cnts += 1
                players.append((cX, cY, area))
    
    man_dist,idx = float('inf'), 0

    if(pre is not None):
        pcx,pcy,pArea = pre
        for i in range(len(players)):
            tcx, tcy, tArea = players[i]
            now_man_dist = abs(tcx - pcx) + abs(tcy - pcy) + abs(tArea - pArea)
            if(man_dist > now_man_dist):
                man_dist = now_man_dist
                idx = i

    if(len(players)):
        CX,CY,Area = players[idx]
        if f is not None: f.write(f"{ii} Contour Area: {area} Centroid: x={cX}, y={cY}  ")
    else:
        players = None
    
    other_img = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

    if(CX is None or CY is None):
        return -1, players, None, None
    print("game end chk",(Area,CX,CY))
    if(game_ended(Area,CX,CY)):
        return -2, players, None, None
    
    distances = []
    direction = np.array([CX - md_width, CY - md_height])
    length = np.linalg.norm(direction)
    unit_vec = direction / length
    base_angle = np.arctan2(unit_vec[1], unit_vec[0]) + add_angle

    tdx, tdy = np.cos(base_angle), np.sin(base_angle)
    tx, ty = md_width + tdx * length, md_height + tdy * length
    while np.array_equal(other_img[int(ty), int(tx)], [255, 255, 255]):
        length += 1
        tx += tdx 
        ty += tdy

    length += 28

    sm_info = []

    for i in range(6):
        angle = base_angle + np.deg2rad(60 * i)
        dx = np.cos(angle)
        dy = np.sin(angle)

        x, y, tlength = md_width + dx * length, md_height + dy * length, length

        while 0 <= int(x) < other_img.shape[1] and 0 <= int(y) < other_img.shape[0] and tlength < t_len:
            pixel = other_img[int(y), int(x)]
            if np.array_equal(pixel, [255, 255, 255]):
                break
            x += dx
            y += dy
            tlength += 1

        if f is not None: f.write(f"{round(tlength,2)} ")
        distances.append((tlength, i))
        cv2.line(other_img, (md_width, md_height), (int(x), int(y)), color, 2)

        if(i == 1 or i == 5):
            sm_info.append((x,y,dx,dy,tlength))

    fives = True

    for i in range(1,6):
        if(not (distances[1][0] - 1 <= distances[i][0] <= distances[1][0] + 1)):
            fives = False
    
    if(fives):
        for x,y,dx,dy,tlength in sm_info:
            px, py = x, y
            while 0 <= int(x) < other_img.shape[1] and 0 <= int(y) < other_img.shape[0] and tlength < t_len:
                pixel = other_img[int(y), int(x)]
                if np.array_equal(pixel, [0, 0, 0]):
                    break
                x += dx
                y += dy
                tlength += 1

            cv2.line(other_img, (int(px), int(py)), (int(x), int(y)), color, 3)
    else:
        sm_info = None

    values = (Area, CX, CY)
    cv2.imwrite(f'contour-test/{str(ii).zfill(3)}-{cnts}-2.png', cv2.cvtColor(other_img, cv2.COLOR_RGB2BGR))
    cv2.imwrite(f'contour-test/{str(ii).zfill(3)}-{cnts}-1.png', img)

    other_img2 = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
    diff_angle = np.deg2rad(self_adjust)
    player_dist = []
    direction = np.array([md_width - CX, md_height - CY])
    length = np.linalg.norm(direction)
    unit_vec = direction / length
    base_angle = np.arctan2(unit_vec[1], unit_vec[0])

    for add_angle in [-diff_angle, diff_angle]:
        angle = base_angle + add_angle
        dx, dy = np.cos(angle), np.sin(angle)
        length = 0
        x, y = CX + dx * length, CY + dy * length

        while not np.array_equal(other_img2[int(y), int(x)], [0, 0, 0]):
            length += 1
            x += dx
            y += dy

        more = 12
        length += more; x += dx * more; y += dy * more

        while not np.array_equal(other_img2[int(y), int(x)], [255, 255, 255]):
            length += 1
            x += dx
            y += dy

        player_dist.append(length)
        cv2.line(other_img2, (CX, CY), (int(x), int(y)), color, 2)

    cv2.imwrite(f'contour-test/{str(ii).zfill(3)}-{cnts}-3.png', cv2.cvtColor(other_img2, cv2.COLOR_RGB2BGR))

    if f is not None: f.write(f"|{player_dist[0]} {player_dist[1]}")

    return distances, values, player_dist, sm_info

if __name__ == '__main__':
    time.sleep(2)
    cnt = 0
    # f = open('contour-logs.txt', 'w')
    contour_detection_visualization_local(img_path=f'{sys.argv[1]}', ii=cnt)

    # while True:
        # cnt += 1;contour_detection_visualization_mss(f=f, ii=cnt)
        # contour_detection_visualization_local(img_path='contour-test/182-1-1.png', ii=cnt); break

# 199 Contour Area: 144809.0 Centroid: x=355, y=288  620.05 283.05 800.05 283.05 618.05 283.05 |93 77 nothing
# 200 Contour Area: 367314.5 Centroid: x=389, y=937  548.57 281.57 800.57 281.57 551.57 281.57 |88 72 nothing
# 201 Contour Area: 455713.0 Centroid: x=412, y=925  501.62 494.62 800.62 493.62 495.62 502.62 |93 72 right 2
# 202 Contour Area: 62868.0 Centroid: x=1436, y=897  446.27 511.27 572.27 292.27 292.27 292.27 |104 85 right 5
