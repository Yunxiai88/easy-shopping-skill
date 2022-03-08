import time
import cv2


def take_photo():
    print('take photo process start')
    cap = cv2.VideoCapture(0)
    img_name = 'cap_img_' + str(time.time()) + '.jpg'
    print(img_name)

    # Change this variable to the path you want to store the image
    img_path = '/opt/mycroft/skills/easy-shopping-skill/testPhoto/' + img_name

    #<-- Take photo in specific time duration -->
    cout = 0
    while True:
        ret, frame = cap.read()
        cv2.waitKey(1)
        cv2.imshow('capture', frame)
        cout += 1 
        if cout == 50:
            cv2.imwrite(img_path, frame)
            break

    cap.release()
    cv2.destroyAllWindows()
    print('take photo process end')


take_photo()

