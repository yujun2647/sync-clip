from PIL import Image
from io import BytesIO
from typing import *


def get_output_data(im: Image.Image, image_format="png"):
    output = BytesIO()
    im.save(output, format=image_format)
    data = output.getvalue()
    return data


class Box(object):
    def __init__(self, data, flag=False):
        self.data = data
        self.flag = flag


def reduce_image_size(byte_datas: bytes,
                      limit_size: int = 1024 * 1024,
                      image_format="png") -> Tuple[bytes, bool]:
    if len(byte_datas) <= limit_size:
        return byte_datas, False
    input_data = BytesIO(byte_datas)
    im: Image.Image = Image.open(input_data)
    asa, sa = 0.5, 0.5
    width, height = im.size
    allow_max_diff = -40000
    while True:
        a_width, a_height = int(width * sa), int(height * sa)
        new_im = im.resize((a_width, a_height))
        output_data = get_output_data(new_im, image_format=image_format)
        diff = len(output_data) - limit_size
        print(f"sa: {sa}, diff: {diff}")
        if allow_max_diff < diff < 0:
            print(f"reduce size to {(a_width, a_height)},"
                  f" filesize: {len(output_data)}")
            return output_data, True
        asa = asa / 2
        if diff < allow_max_diff:
            sa = sa + asa
        else:
            sa = sa - asa
