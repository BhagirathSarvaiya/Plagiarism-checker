import os
from PIL import ImageFont
from PIL import Image
from PIL import ImageDraw
import unicodedata
import cv2
import pytesseract

pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'


def text2png(text, fullpath, color="#000", bgcolor="#FFF", fontfullpath=None, fontsize=13, leftpadding=3,
             rightpadding=3, width=200):
    REPLACEMENT_CHARACTER = u'\uFFFD'
    NEWLINE_REPLACEMENT_STRING = ' ' + REPLACEMENT_CHARACTER + ' '

    font = ImageFont.load_default() if fontfullpath is None else ImageFont.truetype(fontfullpath, fontsize)
    text = text.replace('\n', NEWLINE_REPLACEMENT_STRING)

    lines = []
    line = ""

    for word in text.split(" "):
        if word == REPLACEMENT_CHARACTER:  # give a blank line
            lines.append(line[1:])  # slice the white space in the beginning of the line
            line = ""
            lines.append("")  # the blank line
        elif font.getsize(line + ' ' + word)[0] <= (width - rightpadding - leftpadding):
            line += ' ' + word
        else:  # start a new line
            lines.append(line[1:])
            # slice the white space in the begining of the line
            line = ""

            # TODO: handle too long words at this point
            line += ' ' + word  # for now, assume no word alone can exceed the line width

    if len(line) != 0:
        lines.append(line[1:])  # add the last line

    line_height = font.getsize(text)[1]
    img_height = line_height * (len(lines) + 1)

    img = Image.new("RGBA", (width, img_height), bgcolor)
    draw = ImageDraw.Draw(img)

    y = 0
    for line in lines:
        draw.text((leftpadding, y), line, color, font=font)
        y += line_height

    img.save(fullpath)


def read_text_files(file_path):
    with open(file_path, encoding='utf8') as f:
        s = f.read()
        generated_img_path = f'../../imgs/{(file_path.split("."))[0]}.png'
        text2png(s, generated_img_path, fontfullpath="../font.ttf")


def img_2_text(image_path):
    print(image_path)
    img = cv2.imread(image_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    y = pytesseract.image_to_string(img)
    x = unicodedata.normalize('NFKD', y).encode('ascii', 'ignore')
    x = x.decode("utf-8")
    f = open(f'../final_txt_files/{image_path.split(".")[0]}.txt', 'w')
    f.write(x)
    f.close()


def removeIrrelevantChars(s):
    # s.replace(" ", "")
    x = ""
    for i in s:
        if ord(i) > 32 and ord(i) < 127:
            x += i
    x = x.lower()
    # print(x)
    return x


def hashValues(s, d):
    code = {"!": 1, "#": 2, "$": 3, "%": 4, "&": 5, "(": 6, ")": 7, "*": 8, "+": 9, ",": 10,
            "-": 11, ".": 12, "/": 13, ":": 14, ";": 15, "<": 16, "=": 17, ">": 18, "?": 19,
            "@": 20, "[": 21, "^": 22, "_": 23, "`": 24, "{": 25, "|": 26, "}": 27, "~": 28,
            "]": 29, "\"": 30, "\'": 31, "a": 32, "b": 33, "c": 34, "d": 35, "e": 36, "f": 37,
            "g": 38, "h": 39, "i": 40, "j": 41,
            "k": 42, "l": 43, "m": 44, "n": 45, "o": 46, "p": 47, "q": 48, "r": 49, "s": 50,
            "t": 51, "u": 52, "v": 53, "w": 54, "x": 55, "y": 56, "z": 57, "0": 58, "1": 59,
            "2": 60, "3": 61, "4": 62, "5": 63, "6": 64, "7": 65, "8": 66, "9": 67, "\\": 68}
    x = 0

    # created a 5-gram
    for i in range(d):
        x += ((109 ** (d - 1 - i)) * code[s[i]])
        # x += pow(100,d-i,100009)
        x = x % 100009
    # print(x)
    lis = []
    lis.append(x)
    # print(x)
    i = 1
    while (i < len(s) - d + 1):
        x = ((x - (109 ** (d - 1)) * code[s[i - 1]]) * 109 + code[s[i + d - 1]])
        x = x % 100009
        lis.append(x)
        i += 1
    # print(lis)
    return lis


def winnowing(lst, d):
    y = len(lst)
    x = 100009
    # window of 3
    winList = []
    for i in range(y - d + 1):
        if x != min(lst[i:i + d]):
            winList.append([min(lst[i:i + d]), i])
            x = min(lst[i:i + d])
    return winList


def printPer(lis1, lis2):
    match = {}
    i = 0
    while (i < len(lis1)):
        # print(match)
        # print(lis1[i][0])
        match[lis1[i][0]] = match.get(lis1[i][0], 0) + 1
        i += 1
    i = 0
    count = 0
    while (i < len(lis2)):
        if lis2[i][0] in match:
            count += 1
            match[lis2[i][0]] -= 1
            if match[lis2[i][0]] == 0:
                del match[lis2[i][0]]
        i += 1
    # print(len(lis1))
    similarity = (2 * count) / (len(lis1) + len(lis2)) * 100
    # print(similarity)
    return similarity


def printPer_500(lis1, lis2):
    match = {}
    i = 0
    while (i < len(lis1)):
        # print(match)
        # print(lis1[i][0])
        match[lis1[i]] = match.get(lis1[i], 0) + 1
        i += 1
    i = 0
    count = 0
    while (i < len(lis2)):
        if lis2[i] in match:
            count += 1
            match[lis2[i]] -= 1
            if match[lis2[i]] == 0:
                del match[lis2[i]]
        i += 1
    similarity = (2 * count) / (len(lis1) + len(lis2)) * 100
    return similarity
    # print(similarity)


def read_all_files():
    for file in os.listdir():
        if file.endswith('.txt'):
            print('success')
            read_text_files(f'{file}')


# read the files from the given dataset and convert them to images
os.chdir('pan_15_dataset/src')
read_all_files()
os.chdir('../susp')
read_all_files()

os.chdir('../../imgs')
# convert it back to text and store it in another folder with the same names as the initial
for file in os.listdir():
    if file.endswith('.png'):
        img_2_text(f'{file}')

# create an array that stores the names of the files
arr = os.listdir("../final_txt_files")

# create a dictionary to store the list of students with plag % higher than the bench mark
plag_data={}

# take the assignments of 2 students at a time and find the plag % for them
for i in range(len(arr)-1):
    for j in range(i+1,len(arr)):
        a=arr[i]
        b=arr[j]
        aa= open(f'../final_txt_files/{a.split(".")[0]}.txt', encoding="utf8")
        bb= open(f'../final_txt_files/{b.split(".")[0]}.txt', encoding="utf8")
        # aa and bb contain the texts of their assignment now
        aa=aa.read()
        bb=bb.read()
        s = removeIrrelevantChars(aa)
        ss = removeIrrelevantChars(bb)
        x=len(s)
        y=len(s)
        # set the value of sliding window for creating hash table and winnowing based on their lengths
        if min(x,y) <= 2000:
            d=5
        else:
            d=8
        hashList = hashValues(s,d)
        hashList1 = hashValues(ss,d)

        z=min(x,y)
        if z>500:
            if z>2000:
                d=5
            else:
                d=3
            fingerprint1 = winnowing(hashList,d)
            fingerprint2 = winnowing(hashList1,d)
            sim= printPer(fingerprint1,fingerprint2)
        else:
            sim= printPer_500(hashList,hashList1)
        if sim>=30:
            val = str(a)+":"+str(b)
            plag_data[val]=sim
print(plag_data)
