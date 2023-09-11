from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import os
import svgwrite
import cv2
import pandas as pd
import numpy as np

def trim_white_space(im: Image):
    """ Trim white space of image.
    Args:
        im (PIL.Image): Image to trim.
    Returns:
        PIL.Image: Trimmed image.
    Note:
        This function uses information of white(255) pixels.
        So, if the image has white noise (e.g., resized by LANCZOS filter), this function may not work correctly.
    """
    inverted_image = ImageOps.invert(im)
    # 不要な白色画素を除去
    crop_box = list(inverted_image.getbbox())
    # crop_box[1] = 0
    # crop_box[3] = im.height
    cropped_image = im.crop(crop_box)
    return cropped_image

def add_margin(pil_img, top, right, bottom, left, color):
    width, height = pil_img.size
    new_width = width + right + left
    new_height = height + top + bottom
    result = Image.new(pil_img.mode, (new_width, new_height), color)
    result.paste(pil_img, (left, top))
    return result

def draw(text, font, output_dir, kernel, type="dilate", savename="test", stretch=(1.0,1.0)):
    """
    Draw a single character to an image file.
    Args:
        text (str): The character to draw.
        font (str): The path to the font file.
        output_dir (str): The directory to save the image file.
        kernel (ndarray[int]): The kernel of the filter.
        type (str): The type of the filter. "dilate" or "erode".
    Returns:
        None
    """
    # gray-scale image
    img = Image.new("L", (160, 160), color=255)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(font, 100)
    # draw center
    w, h = draw.textsize(text, font=font)
    draw.text((80, 80), text, font=font, fill=0, anchor='mm')
    # stretch
    resized = (int(img.width * stretch[0]), int(img.height * stretch[1]))
    img = img.resize(resized, resample=Image.NEAREST)
    # re-centering: 1. trim side white space 2. side-padding same width
    img = trim_white_space(img)
    left_padding = int((160 - img.width) / 2)
    right_padding = 160 - img.width - left_padding
    up_padding = int((160 - img.height) / 2)
    down_padding = 160 - img.height - up_padding
    img = add_margin(img, up_padding, right_padding, down_padding, left_padding, 255)
    # save
    img.save(os.path.join(output_dir, text + ".png"))
    img = cv2.imread(os.path.join(output_dir, text + ".png"), 0)
    # img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    inverse_img = cv2.bitwise_not(img)
    if type == "dilate":
        inverse_img = cv2.dilate(inverse_img, kernel, iterations=1)
    elif type == "erode":
        inverse_img = cv2.erode(inverse_img, kernel, iterations=1)
    else:
        raise ValueError("type must be dilate or erode")
    # find contours
    contours, hierarchy = cv2.findContours(inverse_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # draw contours
    img = cv2.drawContours(img, contours, -1, (0, 0, 0), 1)
    # cv2.imwrite(os.path.join(output_dir, text + ".png"), img)
    # get (x,y)
    x_list = []
    y_list = []
    df_group_list = []
    for i in range(len(contours)):
        buf_np = contours[i].flatten()
        for i, elem in enumerate(buf_np):
            if i % 2 == 0:
                x_list.append(elem)
            else:
                y_list.append(elem)
        mylist = list(zip(x_list, y_list))
        df_buf = pd.DataFrame(mylist, columns=["x", "y"])
        df_group_list.append(df_buf)
        x_list = []
        y_list = []
    if True:
        for i, df_buf in enumerate(df_group_list):
            if not df_buf[(df_buf['x'] == 0) & (df_buf['y'] == 0)].empty:
                #print(i, df_buf)
                df_group_list.pop(i)
    # save svg
    dwg = svgwrite.Drawing(os.path.join(output_dir, savename + ".svg"), size=(160, 160))
    for num, df in enumerate(df_group_list, start=1):
        points = df.to_numpy().tolist()
        dwg.add(dwg.polygon(
            points,
            stroke_width=1,
            stroke="black",
            fill="none",
            id=str(num)
        ))
    dwg.save()

if __name__ == "__main__":
    hiraganas = [
        "あ", "い", "う", "え", "お",
        "か", "き", "く", "け", "こ",
        "さ", "し", "す", "せ", "そ",
        "た", "ち", "つ", "て", "と",
        "な", "に", "ぬ", "ね", "の",
        "は", "ひ", "ふ", "へ", "ほ",
        "ま", "み", "む", "め", "も",
        "や", "ゆ", "よ",
        "ら", "り", "る", "れ", "ろ",
        "わ", "を", "ん",
        "が", "ぎ", "ぐ", "げ", "ご",
        "ざ", "じ", "ず", "ぜ", "ぞ",
        "だ", "ぢ", "づ", "で", "ど",
        "ば", "び", "ぶ", "べ", "ぼ",
        "ぱ", "ぴ", "ぷ", "ぺ", "ぽ",
        "ゃ", "ゅ", "ょ",
        "っ",
        "ぁ", "ぃ", "ぅ", "ぇ", "ぉ",
    ]
    font_path = "deepsvg/hiragana/ipaexg00401/ipaexg.ttf"
    output_dir = "deepsvg/hiragana/unprocessed_svgs"
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    kernel_size_list_dilate = [1,2,3,4]
    kernel_size_list_erode = [3,2]
    stretch_rates = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5]
    id = 1
    overall_id = 0
    for hira_id, hira_moji in enumerate(hiraganas):
        for stretch_direct in ["width", "height"]:
            for stretch_width in stretch_rates:
                for stretch_height in stretch_rates:
                    for kernel_size in kernel_size_list_erode:
                        kernel = np.ones((kernel_size, kernel_size), np.uint8)
                        draw(hira_moji, font_path, output_dir, kernel, "erode", str(hira_id) + "_" + hira_moji + "_" + str(id) + "_" + str(overall_id).rjust(6, "0"), stretch=(stretch_width, stretch_height))
                        id += 1
                        overall_id += 1
                    for kernel_size in kernel_size_list_dilate:
                        kernel = np.ones((kernel_size, kernel_size), np.uint8)
                        draw(hira_moji, font_path, output_dir, kernel, "dilate", str(hira_id) + "_" + hira_moji + "_" + str(id) + "_" + str(overall_id).rjust(6, "0"), stretch=(stretch_width, stretch_height))
                        id += 1
                        overall_id += 1
        id = 1

    # delete png
    png_list = os.listdir(output_dir)
    for png in png_list:
        if png.endswith(".png"):
            os.remove(os.path.join(output_dir, png))
