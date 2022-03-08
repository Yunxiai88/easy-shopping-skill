from mycroft import MycroftSkill, intent_file_handler, intent_handler
from adapt.intent import IntentBuilder

# import removes_context
from mycroft.skills.context import removes_context

from mycroft.util import LOG
import time
import cv2
import os
import sys
from multiprocessing import Process, Queue

import csv
import json
from .cvAPI import getDetail, getObjLabel


LOGSTR = '********************====================########## '

MODE = 'PROD'

IMAGE_PATH='/home/iss-user/mycroft-core/skills/easy-shopping-skill/photo/'
TEST_IMAGE_PATH='/home/iss-user/mycroft-core/skills/easy-shopping-skill/testPhoto/'

class EasyShopping(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)
        self.log.info(LOGSTR + ' initial EasyShopping SKill')

        self.category_str = ''
        self.color_str = ''
        self.brand_str = ''
        self.kw_str = ''
        self.img_multi = ''
        self.img_hand = ''
        
    
    def initialize(self):
        self.reload_skill = False

    @intent_handler('is.there.any.goods.intent')
    def handle_is_there_any_goods(self, message):
        if self.img_multi == '':
            self.handle_no_context_front(message)
        else:
            try:        
                self.log.info(LOGSTR + 'actual img path')
                self.log.info(self.img_multi)
                if MODE == 'TEST':
                    self.log.info(LOGSTR + 'testing mode, use another image')
                    self.img_multi = TEST_IMAGE_PATH + '1.jpeg'
                
                objectlist = getObjLabel.getObjectsThenLabel(self.img_multi)
                label_list = []
                loc_list = []
                detected = 0


                category = message.data.get('category')
                
                for obj in objectlist['objectList']:
                    label_list.append(obj['name'])
                    loc_list.append(obj['loc'])

                for i in range(len(label_list)):
                    label_str = generate_str(label_list[i])
                    label_str = label_str.lower()

                    if category is not None:
                        if category in label_str:
                            self.speak_dialog('yes.goods', 
                                        {
                                            'category': category,
                                            'location': loc_list[i]
                                        })
                            detected = 1
                            break
                    else:
                        continue
        
                if detected == 0:
                    self.speak_dialog('no.goods', {'category': category})
        
            except Exception as e:
                    self.log.error((LOGSTR + "Error: {0}").format(e))
                    self.speak_dialog("exception", {"action": "calling computer vision API"})
    
    @intent_handler('view.goods.intent')
    def handle_view_goods(self, message):
        self.speak_dialog('take.photo')
        self.img_multi = ''
        self.img_hand = ''

        #TODO
        # step 1.2: create another process to do the photo taking
        img_queue = Queue()
        take_photo_process = Process(target=take_photo, args=(img_queue,))
        take_photo_process.daemon = True
        take_photo_process.start()
        take_photo_process.join()
        self.img_multi = img_queue.get()

        self.speak('I find some goods here, you can ask me whatever goods you want.', expect_response=True)

    @intent_handler(IntentBuilder('ViewItemInHand').require('ViewItemInHandKeyWord'))
    def handle_view_item_in_hand(self, message):
        self.speak_dialog('take.photo')

        self.img_multi = ''
        self.img_hand = ''

        # take photo
        img_queue = Queue()
        take_photo_process = Process(target=take_photo, args=(img_queue,))
        take_photo_process.daemon = True
        take_photo_process.start()
        take_photo_process.join()
        self.img_hand = img_queue.get()

        try:
            self.log.info(LOGSTR + 'actual img path')
            self.log.info(self.img_hand)

            if MODE == 'TEST':
                self.log.info(LOGSTR + 'testing mode, use another image')
                self.img_hand = TEST_IMAGE_PATH + "test2.jpg"

            detail = getDetail(self.img_hand)
            self.detail = detail

            self.category_str = generate_str(detail['objectLabel'])

            if self.category_str != '':
                self.set_context('getDetailContext')
                self.speak_dialog('item.category', {'category': self.category_str}, expect_response=True)

                self.brand_str = generate_str(detail['objectLogo'])
            
                color_list = []
                for color in detail['objectColor']:
                    color_list.append(color['colorName'])
                self.color_str = generate_str(color_list)

                self.kw_str = ' '.join(detail['objectText'])

                print('brand ---->' + self.brand_str)
                print('color ---->' + self.color_str)
                print('keyword ---->' + self.kw_str)
            else:
                print("clear context....")
                self.clear_all()
                self.remove_context('getDetailContext')
                self.speak('I cannot understand what is in your hand. Maybe turn around it and let me see it again', expect_response=True)

        except Exception as e:
            self.log.error((LOGSTR + "Error: {0}").format(e))
            self.speak_dialog("exception", {"action": "calling computer vision API"})
    
    @intent_handler(IntentBuilder('AskItemBrand').require('Brand').require('getDetailContext').build())
    def handle_ask_item_brand(self, message):
        self.handle_ask_item_detail('brand', self.brand_str)
    
    @intent_handler(IntentBuilder('AskItemCategory').require('Category').require('getDetailContext').build())
    def handle_ask_item_category(self, message):
        self.handle_ask_item_detail('category', self.category_str)
    
    @intent_handler(IntentBuilder('AskItemColor').require('Color').require('getDetailContext').build())
    def handle_ask_item_color(self, message):
        self.handle_ask_item_detail('color', self.color_str)

    @intent_handler(IntentBuilder('AskItemKw').require('Kw').require('getDetailContext').build())
    def handle_ask_item_keywords(self, message):
        self.handle_ask_item_detail('keyword', self.kw_str)

    @intent_handler(IntentBuilder('AskItemInfo').require('Info').require('getDetailContext').build())
    def handle_ask_item_complete_info(self, message):
        if self.color_str == '':
            self.handle_ask_item_detail('category', self.category_str)
        else:
            self.speak_dialog('item.complete', {'category': self.category_str})
            self.handle_ask_item_detail('brand', self.brand_str)
            self.handle_ask_item_detail('keyword', self.kw_str)

    @intent_handler(IntentBuilder('FinishOneItem').require('Finish').require('getDetailContext').build())
    @removes_context('getDetailContext')
    def handle_finish_current_item(self, message):
        self.speak('Got you request. Let\'s continue shopping!')
        if self.img_hand != '':
            self.speak('I will put the item into cart. Let\'s continue shopping!')
            self.clear_all()
        else:
            self.speak('Sorry, I don\'t understand')
    
    @intent_handler(IntentBuilder('NoContext').one_of('Category', 'Color', 'Brand', 'Kw', 'Info'))
    def handle_no_context(self, message):
        self.speak('Please let me have a look at what\'s in your hand first.')
    
    # util functions
    def handle_no_context_front(self, message):
        self.speak('Please let me have a look at what\'s in front of you first.')

        take_photo = self.ask_yesno('do.you.want.to.take.a.photo')
        if take_photo == 'yes':
            self.handle_view_goods(message)
        elif take_photo == 'no':
            self.speak('OK. I won\'t take photo')
        else:
            self.speak('I cannot understand what you are saying')
    
    def clear_all(self):
        self.color_str = ''
        self.logo_str = ''
        self.kw_str = ''
        self.img_hand = ''
        self.img_multi = ''

    def handle_ask_item_detail(self, detail, detail_str):
        if detail_str == '':
            self.speak_dialog('cannot.get', {'detail': detail}, expect_response=True)
        else:
            dialog_str = 'item.' + detail
            print(dialog_str)
            self.speak_dialog(dialog_str, {detail: detail_str}, expect_response=True)

def generate_str(possible_list):
    res = ''
    if len(possible_list) == 3:
        res = possible_list[0] + ' ' + \
            possible_list[1] + ' and ' + possible_list[2]
    elif len(possible_list) == 2:
        res = possible_list[0] + ' and ' + possible_list[1]
    elif len(possible_list) == 1:
        res = possible_list[0]

    return res

def take_photo(img_queue):
    LOG.info(LOGSTR + 'take photo process start')

    cap = cv2.VideoCapture(0)
    img_name = 'cap_img_' + str(time.time()) + '.jpg'

    img_path = IMAGE_PATH + img_name

    cout = 0
    while True:
        ret, frame = cap.read()
        cv2.waitKey(1)
        cv2.imshow('capture', frame)
        cout += 1 
        if cout == 50:
            img_queue.put(img_path)
            cv2.imwrite(img_path, frame)
            break

    cap.release()
    cv2.destroyAllWindows()
    LOG.info(LOGSTR + 'take photo process end')
    os._exit(0)

def create_skill():
    return EasyShopping()

