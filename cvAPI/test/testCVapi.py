import sys

sys.path.append('/opt/mycroft/skills/easy-shopping-skill/cvAPI')
from util import callAPI, encode_image_from_file

image_file = '/opt/mycroft/skills/easy-shopping-skill/testPhoto/1.jpeg'
image_base64 = encode_image_from_file(image_file)
response = callAPI(image_base64, 'LABEL')
print(response)
