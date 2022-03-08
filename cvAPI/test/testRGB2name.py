from webcolors import CSS3_HEX_TO_NAMES
from webcolors import hex_to_rgb
from scipy.spatial import KDTree

def getRGBValues():
    css3_db = CSS3_HEX_TO_NAMES

    names = []
    rgb_values = []
    for color_hex, color_name in css3_db.items():
        names.append(color_name)
        rgb_values.append(hex_to_rgb(color_hex))

    return rgb_values, names


def getColorNameFromRGB(rgb_tuple, rgb_values, names):

    # a dictionary of all the hex and their respective names in css3

    kdt_db = KDTree(rgb_values)
    _, index = kdt_db.query(rgb_tuple)
    return names[index]

rgbTuple = (0, 0, 255)
rgb_values, names = getRGBValues()
print(getColorNameFromRGB(rgbTuple, rgb_values, names))