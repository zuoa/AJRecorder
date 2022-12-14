import datetime
from moviepy.editor import VideoFileClip
import traceback
from PIL import Image, ImageFont, ImageDraw
from FlvParser import FlvParser
import jieba.analyse

jieba.analyse.set_stop_words('stopwords.txt')


def get_video_duration(filename):
    u"""
    获取视频时长（s:秒）
    """
    file_time = 0
    clip = None
    try:
        clip = VideoFileClip(filename)
        file_time = clip.duration
    except Exception as e:
        traceback.print_exc()
    finally:
        if clip:
            clip.close()
    return file_time


def get_video_real_duration(filename):
    u"""
    获取视频时长（s:秒）
    """
    parser = FlvParser(filename)
    return int(parser.get_duration())


def get_font_size(font_size, font_path, text):
    u"""
    获取字体大小
    """
    font = ImageFont.truetype(font_path, font_size)
    return font.getsize(text)


def generate_part_title(filename):
    t = filename.split(".")[0]
    start = t.split("_")[0]
    start_time = datetime.datetime.strptime(start, "%Y%m%d%H%M%S")
    return start_time.strftime("%m月%d日 %H时%M分")


def extract_tags(text, top=10):
    return jieba.analyse.extract_tags(text, topK=top)


def image_add_text(img_path, words, x, y, font_size=128):
    im = Image.open(img_path)
    im = im.convert('RGBA')
    font_size = 128
    fill_color = (255, 255, 0, 200)
    shadow_color = (0, 0, 0, 160)

    text_overlay = Image.new('RGBA', im.size, (255, 255, 255, 0))
    image_draw = ImageDraw.Draw(text_overlay)

    font = "fzht.ttf"
    font = ImageFont.truetype(font, font_size)
    for i, word in enumerate(words):
        image_draw.text((x + 500 * int(i / 5), y + (font_size + 16) * (i % 5)),
                        word, font=font, fill=fill_color,
                        stroke_fill=shadow_color, stroke_width=8)

    im = Image.alpha_composite(im, text_overlay)
    output = img_path + ".png"
    im.save(output)
    return output


if __name__ == '__main__':
    y = get_video_real_duration("/Users/yujian/data/AJRecorder/video/source/7828414/7828414_20221115_162622.flv")
    print(y)
    # x = get_video_duration("/Users/yujian/data/AJRecorder/video/source/7828414/7828414_20221115_161655.flv")
    # print(x)
