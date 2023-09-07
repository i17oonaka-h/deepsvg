from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import svgwrite
import cv2
import pandas as pd
import numpy as np

def draw(text, font, output_dir, kernel, type="dilate", savename="test", stretch=1.0):
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
    img = Image.new("L", (100, 100), color=255)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(font, 50)
    # draw center
    w, h = draw.textsize(text, font=font)
    draw.text(((100 - w) / 2, (100 - h) / 2), text, font=font, fill=0)
    # stretch
    img = img.resize((int(img.width * stretch), int(img.height)))
    # save
    img.save(os.path.join(output_dir, text + ".png"))
    img = cv2.imread(os.path.join(output_dir, text + ".png"), 0)
    img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
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
    dwg = svgwrite.Drawing(os.path.join(output_dir, savename + ".svg"), size=(100, 100))
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
    font_path = "/Volumes/GoogleDrive-117840701469929857994/マイドライブ/deepsvg/deepsvg/hiragana/ipaexg00401/ipaexg.ttf"
    output_dir = "/Volumes/GoogleDrive-117840701469929857994/マイドライブ/deepsvg/deepsvg/hiragana/svg"
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    kernel_size_list = [1, 2, 3]
    type_list = ["dilate", "erode"]
    wide_stretch_list = [0.8, 0.9, 1.0, 1.1, 1.2]
    id = 1
    for hira in hiraganas:
        for kernel_size in kernel_size_list:
            for type in type_list:
                for wide_stretch in wide_stretch_list:
                    kernel = np.ones((kernel_size, kernel_size), np.uint8)
                    draw(hira, font_path, output_dir, kernel, type, str(id), wide_stretch)
                    id += 1
    # delete png
    png_list = os.listdir(output_dir)
    for png in png_list:
        if png.endswith(".png"):
            os.remove(os.path.join(output_dir, png))
