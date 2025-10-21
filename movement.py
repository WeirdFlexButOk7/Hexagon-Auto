import pyautogui
import time
import os
from contour import contour_detection_visualization_mss

pyautogui.FAILSAFE = False

def move_left_small():
    pyautogui.press('left')

def move_right_small():
    pyautogui.press('right')

def move_left(amount, once = 0.0244, extra = 0.16005):
    l = [0.02421, 0.1648, 0.3045, 0.45, 0.61]
    pyautogui.keyDown('left')
    # time.sleep(once + (amount-1) * extra)
    time.sleep(l[amount-1])
    pyautogui.keyUp('left')

def move_right(amount, once = 0.0244, extra = 0.16005):
    l = [0.02421, 0.1648, 0.3045, 0.45, 0.61]
    pyautogui.keyDown('right')
    time.sleep(l[amount-1])
    pyautogui.keyUp('right')

def start_game():
    time.sleep(1)
    os.system('bash -c "rm -rf contour-test > /dev/null 2>&1" && mkdir contour-test')
    os.system('osascript -e \'tell application "System Events" to keystroke "k" using {command down}\'')
    os.system('osascript -e \'tell application "System Events" to key code 123 using control down\'')
    time.sleep(1)
    # os.system("osascript -e 'tell application \"System Events\" to click (get the first button of (get the first window of (get frontmost application)))'")
    os.system("cliclick c:500,1000")
    time.sleep(0.5)
    pyautogui.press('space')
    pyautogui.press('space')
    pyautogui.press('space')
    time.sleep(0.8)

def end_game():
    time.sleep(1)
    os.system('osascript -e \'tell application "System Events" to key code 124 using control down\'')

def main():
    time.sleep(1)
    stop_loop = False
    cnt = 0
    tol = 10
    move_tol = 395
    step_tol = 20
    f=open('contour-logs.txt','w')
    start_game()
    
    five = False
    four = False
    pre_four = False
    five_sm = False
    values = None

    while not stop_loop:
        cnt += 1
        distances, values, player_dist, sm_info = contour_detection_visualization_mss(f=f,ii=cnt,pre=values)
        f.flush()
        if(distances == -2):
            f.write("\n")
            break
        if(distances == -1):
            f.write("\n")
            continue

        orig_distances = [int(distance) for (distance, angle) in distances]

        if(max(orig_distances) <= 350):
            f.write(" nothing low\n")
            continue

        distances = sorted([(int(distance), angle) for (distance, angle) in distances], reverse=True)
        dist_merge = dict()
        maxd, mind = 0, 800
        prev = -1

        for distance, angle in distances[::-1]:
            if(prev == -1):
                dist_merge[distance] = [angle]
                prev = distance
                maxd = max(maxd, distance)
                mind = min(mind, distance)
            elif(prev + 2 * tol >= distance):
                dist_merge[prev].append(angle)
            else:
                dist_merge[distance] = [angle]
                prev = distance
                maxd = max(maxd, distance)
                mind = min(mind, distance)

        # print(dist_merge)

        dist_merge[maxd].sort(key=lambda x:min(x, 6-x))
        position = dist_merge[maxd][0]

        if(len(dist_merge[maxd]) == 1 and maxd <= 650):
            five = True
        
        # if(len(dist_merge[maxd]) == 1 and len(dist_merge) >= 3):
        if(len(dist_merge[maxd]) == 1 and len(dist_merge) >= 3 and len(dist_merge[mind]) == 1):
            four = True

        # print(cnt, five, four)

        if position == 0:
            left, right = player_dist
            if(abs(left-right) <= step_tol or five_sm):
                f.write(" nothing0\n")
                pre_non = True
            elif(not pre_four):
                if(left > right):
                    move_right_small()
                    f.write(" right sm\n")
                else:
                    move_left_small()
                    f.write(" left sm\n")
                pre_non = False
            else:
                f.write(" nothing0\n")
                pre_non = True
            five = four = False
            pre_four = False
        elif position <= 2:
            pre_non = False
            if(five):
                position = 5
                five = four = False
                pre_four = False
            elif(four):
                move_left(6-position)
                f.write(f" left {6-position}\n")
                five = four = False
                if(pre_four):
                    pre_four = False
                else:
                    pre_four = True
                continue

            if(position in [2,3]):
                if(orig_distances[1] <= move_tol and position == 2):
                    f.write(" nothing\n")
                    continue
                if(min(orig_distances[1], orig_distances[2]) <= move_tol and position == 3):
                    f.write(" nothing\n")
                    continue
                if(orig_distances[1] > move_tol and abs(orig_distances[1]-orig_distances[2]) >= 200 and position == 3):
                    position = 1
                pre_four = False

            move_right(position)
            f.write(f" right {position}\n")
        else:
            pre_non = False
            if(five):
                position = 1
                five = four = False
                pre_four = False
            elif(four):
                move_right(position)
                f.write(f" right {position}\n")
                five = four = False
                if(pre_four):
                    pre_four = False
                else:
                    pre_four = True
                continue

            if(6-position in [2,3]):
                if(orig_distances[5] <= move_tol and 6-position == 2):
                    f.write(" nothing\n")
                    continue
                if(min(orig_distances[5], orig_distances[4]) <= move_tol and 6-position == 3):
                    f.write(" nothing\n")
                    continue
                if(orig_distances[5] > move_tol and abs(orig_distances[5]-orig_distances[4]) >= 200 and 6-position == 3):
                    position = 5
                pre_four = False

            move_left(6-position)
            f.write(f" left {6-position}\n")

    end_game()

    f.close()
    print("done")

if __name__ == '__main__':
    main()
