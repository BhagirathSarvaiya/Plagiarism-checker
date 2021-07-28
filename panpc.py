import hashlib
import zlib
import os
from collections import defaultdict
from xml.dom import minidom
from nltk.corpus import stopwords
from nltk.stem.snowball import EnglishStemmer
from nltk.stem.porter import *

stemmer = EnglishStemmer()
nltk_stop_words = set(stopwords.words("english"))


class token:
    def __init__(self, val, start, end, id):
        self.val = val
        self.offset_end = end
        self.offset_start = start
        self.id = id


class gram:
    def __init__(self, val: str, start, end):
        self.hashVal = zlib.crc32(bytes(val, 'utf8'))
        self.start = start
        self.end = end


class plag:

    def filter_word(self, word):
        word = stemmer.stem(word.lower())
        if word in nltk_stop_words:
            return ''
        return word

    def preprocess(self, text):

        offset_data = []
        id = 0
        n = len(text)
        curr = ""
        j = 0
        s = ""
        for i in range(n):
            s = text[i]
            if not re.search(r'[\s\.]', s):
                if re.search(r"[\w\-]", s):
                    curr += s
            else:
                if j != i and len(curr) != 0:
                    # final_word = self.filter_word(curr)
                    # if len(final_word) != 0:
                    offset_data.append(token(curr.lower(), j, i, id))
                    id += 1
                curr = ""
                j = i + 1
        return offset_data

    def offset_to_gram(self, off_data, n):
        data = []
        m = len(off_data)
        for i in range(m - 3):
            s = off_data[i].val + ' ' + off_data[i + 1].val + ' ' + off_data[i + 2].val
            # print(s, zlib.crc32(bytes(s, 'utf8')))
            data.append(gram(s, i, i + 3), )

        return data

    def generateHashMap(self, grams):
        checksumMap = defaultdict(lambda: [])
        for i in grams:
            checksumMap[i.hashVal].append(i)
        return checksumMap


class document:
    def __init__(self, name, text):
        x = plag()
        self.name = name
        self.tokens = x.preprocess(text)
        self.grams = x.offset_to_gram(self.tokens, 3)
        self.checksumMap = x.generateHashMap(self.grams)
        self.min_tokens = int(len(self.tokens) * 0.1)


class matchrange:
    def __init__(self, susp_start, susp_end, src_start, src_end):
        self.susp_start = susp_start
        self.susp_end = susp_end
        self.src_start = src_start
        self.src_end = src_end
        self.tokensclaimed = src_end - src_start


def tokensort(matchlist):
    return matchlist.sort(key=lambda x: -x.tokensclaimed)


def getMatches(grams, src_doc):
    offset_map = defaultdict(lambda: [])
    matches = []

    for _gram in grams:
        if _gram.hashVal not in src_doc.checksumMap.keys():
            continue

        for z in src_doc.checksumMap[_gram.hashVal]:
            offset = _gram.start - z.start

            if offset in offset_map and offset_map[offset][-1].susp_end + 1 == _gram.end:
                offset_map[offset][-1].susp_end = _gram.end
                offset_map[offset][-1].src_end = z.end
            else:
                offset_map[offset].append(matchrange(_gram.start, _gram.end, z.start, z.end))

    for offset in offset_map.keys():
        for value in offset_map[offset]:
            value.tokensclaimed = value.susp_end - value.susp_start
            matches.append(value)
    tokensort(matches)
    return matches


# def detect_runs(susp_len, confidence, matches, src_min_length):
#     sub_len = src_min_length
#
#     target_tokens = int(src_min_length * confidence)
#     # print(target_tokens)
#     hits = []
#     for i in range(susp_len):
#         hits.append(False)
#
#     for element in matches:
#         for i in range(element.susp_start, element.susp_end):
#             hits[i] = True
#
#     total_matches = 0
#     for i in range(src_min_length):
#         if hits[i]:
#             total_matches += 1
#
#     # print(total_matches)
#     out = []
#     if total_matches >= target_tokens:
#         out.append(0)
#
#     for i in range(1, susp_len):
#         if hits[i - 1]:
#             total_matches -= 1
#         end = i + sub_len - 1
#
#         if end < susp_len and hits[end]:
#             total_matches += 1
#
#         if total_matches >= target_tokens:
#             out.append(i)
#
#     if len(out) == 0:
#         return []
#
#     final_out = [matchrange(out[0], out[0] + 3, 0, 0)]
#
#     for i in range(1, len(out)):
#         if out[i] != out[i - 1] + 1:
#             final_out.append(matchrange(out[i], out[i] + 3, 0, 0))
#         else:
#             final_out[-1].susp_end = out[i] + 3
#
#     return final_out


def fuse_matches(matches, runs, confidence, susp_size, src_min_size):
    claimed = []
    filter = []
    for i in range(susp_size):
        filter.append(False)

    error_margin = round(src_min_size * (1 - confidence))
    for match in runs:
        for i in range(match.susp_start, match.susp_end):
            filter[i] = True

    for match in matches:
        # offset = match.susp_start - match.src_start

        # if offset < 0:
        #     if -offset < error_margin:
        #         offset = 0
        # else:
        #     continue

        # if not filter[offset]:
        #     continue
        #
        # print('pass filter', match.susp_start)

        unclaimed = True

        moff = match.susp_start - match.src_start

        for claim in claimed:
            coff = claim.susp_start - claim.src_start

            sample_error = abs(moff - coff)
            match_within_error_margin_to_claim = (abs(match.susp_start - claim.susp_end) < error_margin or abs(
                match.susp_end - claim.susp_start) < error_margin)

            within_error = sample_error < error_margin and match_within_error_margin_to_claim

            if within_error and match.tokensclaimed > sample_error:
                # print('sample error', sample_error, 'claim', claim.susp_start, 'match', match.susp_start,
                #       match.tokensclaimed)
                if match.susp_start >= claim.susp_start and match.susp_end <= match.src_end:
                    claim.tokensclaimed += match.tokensclaimed
                    unclaimed = False

                else:
                    if match.susp_start < claim.susp_start and match.src_start < claim.src_start:
                        claim.susp_start = match.susp_start
                        claim.src_start = match.src_start
                        claim.tokensclaimed += match.tokensclaimed
                        # print('updated claim', claim.susp_start, claim.susp_end, claim.src_start, claim.src_end)
                        unclaimed = False

                    elif match.susp_end > claim.susp_start and match.src_end > claim.src_end:
                        claim.susp_end = match.susp_end
                        claim.src_end = match.src_end
                        claim.tokensclaimed += match.tokensclaimed
                        # print('updated claim', claim.susp_start, claim.susp_end, claim.src_start, claim.src_end)
                        unclaimed = False

            if not unclaimed:
                break

        if unclaimed and match.tokensclaimed * 10 > matches[0].tokensclaimed:
            claimed.append(match)
    final_filter = []

    for claim in claimed:
        if claim.tokensclaimed >= (src_min_size * confidence):
            final_filter.append(claim)

    return final_filter


src_data = {}
path = 'final_txt_files'
os.chdir(path)

for i in os.listdir():
    x = i.split(".")[0]
    with open(i, encoding='utf8') as f:
        s = f.read()
    src_data[x] = document(x, s)

susp_data = {}
os.chdir("../susp")

for i in os.listdir():
    x = i.split(".")[0]
    with open(i, encoding='utf8') as f:
        s = f.read()
    susp_data[x] = document(x, s)

os.chdir("..")
path = "pairs"

pairs = []
with open(path, encoding='utf8') as f:
    s = f.read()

s = s.splitlines()
for i in s:
    pairs.append(i.split())

# print(pairs)
found = 0
# print(os.getcwd())
os.chdir("xml_files")
print('start matching')
for p in pairs:

    try:
        susp = susp_data[p[0].split('.')[0]]
        src = src_data[p[1].split('.')[0]]
    except:
        continue
    matched = getMatches(susp.grams, src)
    # runs = detect_runs(len(susp.tokens), 0.6, matched, src.min_tokens)

    fuses = fuse_matches(matched, [], 0.8, len(susp.tokens), src.min_tokens)
    if len(fuses) > 0:
        found += 1

    for match in fuses:
        x=susp.tokens[match.susp_start].offset_start
        y=susp.tokens[match.susp_end].offset_start
        a=src.tokens[match.src_start].offset_start
        b=src.tokens[match.src_end].offset_start
        root = minidom.Document()

        xml = root.createElement('document')
        xml.setAttribute('reference', str(p[0]))
        root.appendChild(xml)

        productChild = root.createElement('feature')
        productChild.setAttribute('name', 'plagiarism')
        productChild.setAttribute('obfuscation', 'none')
        productChild.setAttribute('source_length', str(b-a))
        productChild.setAttribute('source_offset', str(a))
        productChild.setAttribute('source_reference', str(p[1]))
        productChild.setAttribute('this_length', str(y-x))
        productChild.setAttribute('this_offset', str(x))
        productChild.setAttribute('type', 'artificial')

        xml.appendChild(productChild)

        xml_str = root.toprettyxml(indent="\n")

        save_path_file =p[0]+"-"+p[1]+".xml"


        with open(save_path_file, "w") as f:
            f.write(xml_str)


        print(p[0], p[1], susp.tokens[match.susp_start].offset_start, susp.tokens[match.susp_end].offset_start,
              src.tokens[match.src_start].offset_start, src.tokens[match.src_end].offset_start, match.tokensclaimed)
        # print(match.susp_start, match.susp_end, match.src_start, match.src_end, match.tokensclaimed)
print('found', found)
