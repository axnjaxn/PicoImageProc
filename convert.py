import numpy as np
import sys,cv2,os

pal=[
    "000000",
    "1d2b53",
    "7e2553",
    "008751",
    "ab5236",
    "5f574f",
    "c2c3c7",
    "fff1e8",
    "ff004d",
    "ffa300",
    "ffec27",
    "00e436",
    "29adff",
    "83769c",
    "ff77a8",
    "ffccaa"
]

alt_pal = [
    "291814",
    "111d35",
    "422136",
    "125359",
    "742f29",
    "49333b",
    "a28879",
    "f3ef7d",
    "be1250",
    "ff6c24",
    "a8e72e",
    "00b543",
    "065ab5",
    "754665",
    "ff6e59",
    "ff9d81"
]

def hex2bgr(s):
    r = int(s[:2], 16)
    g = int(s[2:4], 16)
    b = int(s[4:], 16)
    return np.array([b, g, r], dtype=float)

# TODO: I'm going to use a perceptual distance later on
def squareDist(bgr1,bgr2):
    d = np.asarray(bgr1, float) - np.asarray(bgr2, float)
    return d[0] * d[0] + d[1] * d[1] + d[2] * d[2]

def allColors():
    colors = []
    for i in range(16):
        colors.append(hex2bgr(pal[i]))
    for i in range(16):
        colors.append(hex2bgr(alt_pal[i]))
    return colors

# TODO: This can also be faster, but who cares?
def bestColor(bgr,colors):
    dbest = 1e99
    for i in range(len(colors)):
        d = squareDist(bgr, colors[i])
        if d < dbest:
            dbest = d
            best = i
    return best

def bestPalette(img, palette=None, dither=0.0):
    if palette is None:
        colors = allColors()
        palette = list(range(len(colors)))
    else:
        colors = selectColors(palette)

    idx_map = convertImage(img,palette,dither)
    h = [0] * len(colors)
    for r in range(img.shape[0]):
        for c in range(img.shape[1]):
            h[idx_map[r,c]] += 1

    while len(colors) > 16:
        worst = 0
        for i in range(1, len(colors)):
            if h[i]<h[worst]:
                worst = i
        colors = colors[:worst] + colors[worst+1:]
        palette = palette[:worst] + palette[worst+1:]
        change_ct = h[worst]
        h = h[:worst] + h[worst+1:]
        if change_ct > 0:
            if dither>0:
                idx_map = convertImage(img,palette,dither)
                h = [0] * len(colors)
                for r in range(img.shape[0]):
                    for c in range(img.shape[1]):
                        h[idx_map[r,c]] += 1
            else:
                for r in range(img.shape[0]):
                    for c in range(img.shape[1]):
                        if idx_map[r,c]==worst:
                            bgr = np.asarray(img[r,c,:], float)
                            idx = bestColor(bgr, colors)
                            idx_map[r,c] = idx
                            h[idx] = h[idx] + 1

    return palette

def selectColors(palette):
    all_colors = allColors()
    colors = []
    for idx in palette:
        colors.append(all_colors[idx])
    return colors

def convertImage(img, palette, dither=0.0):
    colors = selectColors(palette)
    idx_map = np.zeros(img.shape[:2], dtype=int)
    debt = np.zeros(img.shape, dtype=float)
    inrange = lambda x: (x >= 0 and x < img.shape[1])
    for r in range(img.shape[0]):
        if r%2==0:
            clist = range(img.shape[1])
            dc = 1
        else:
            clist = range(img.shape[1]-1,-1,-1)
            dc = -1
        for c in clist:
            bgr = np.asarray(img[r,c,:], float) + debt[r,c,:]
            idx = bestColor(bgr,colors)
            idx_map[r,c] = idx
            if dither>0.0:
                error = dither*(bgr-colors[idx])
                if inrange(c+dc):
                    debt[r,c+dc] += (7/16.0)*error
                if r < img.shape[0] - 1:
                    if inrange(c-dc): debt[r+1,c-dc] += (3/16.0)*error
                    debt[r+1,c] += (5/16.0)*error
                    if inrange(c+dc): debt[r+1,c+dc] += (1/16.0)*error

    return idx_map

def getPreview(img, palette, dither=0.0):
    idx_map = convertImage(img, palette, dither)
    colors = selectColors(palette)

    prev = np.zeros(img.shape, dtype=float)
    for r in range(img.shape[0]):
        for c in range(img.shape[1]):
            prev[r,c,:]=colors[idx_map[r,c]]
    return np.asarray(prev,np.uint8)

def getPalettePreview(palette):
    size=48
    prev = np.zeros((size,size*len(palette),3),dtype=float)
    colors = selectColors(palette)
    for i in range(len(colors)):
        prev[:,size*i:size*(i+1),:] = colors[i]
        idx = (128 * (palette[i] // 16)) + (palette[i] % 16)
        if np.sum(colors[i])/3.0 > 128.0: textcol = (0.0,0.0,0.0)
        else: textcol = (255.0,255.0,255.0)
        cv2.putText(prev,str(idx),(size*i+1,size-16),
                    cv2.FONT_HERSHEY_DUPLEX,0.65,textcol)
    prev = np.asarray(prev,dtype=np.uint8)
    return prev

def arrangePalette(palette):
    used = [False] * 16

    to_arrange = []
    for idx in palette:
        if idx < 16:
            used[idx] = True
        else:
            to_arrange.append(idx)

    arranged = list(range(16))
    for i in range(16):
        if len(to_arrange)<1: break
        if not used[i]:
            arranged[i]=to_arrange[0]
            to_arrange = to_arrange[1:]

    return arranged

usage = '''
python %s [options] imagefile.ext output.p8
--use-palette palette-filename: only use the palette listed in the file
                                (format is text, one color index per line)
--default-palette: use the normal palette and disable secret colors
--ban-color index: do not allow a color index to appear in recommendations
--dither percentage: enable Floyd-Steinberg dithering (0%-100%)
--preview: preview results (3x scale, press any key to terminate)
--slower-recommend: take dithering settings into account when recommending (slower)
'''

if len(sys.argv) < 3:
    print(usage % (sys.argv[0]))
    sys.exit(0)

imagefn = None
outfn = None

palette = list(range(32))
preview = False
dither = 0.0
tryhard = False
i=1
while i < len(sys.argv):
    arg = sys.argv[i]
    if arg == "--use-palette":
        i = i + 1
        palette = []
        with open(sys.argv[i],'r') as fp:
            for line in fp.readlines():
                idx = int(line.strip())
                idx = (idx % 16) + 16 * (idx//128)
                palette.append(idx)
    elif arg == "--ban-color":
        i = i + 1
        idx = int(sys.argv[i])
        idx = (idx % 16) + 16 * (idx//128)
        palette.remove(idx)
    elif arg == "--default-palette":
        palette = list(range(16))
    elif arg == "--dither":
        i = i + 1
        dither = min(max(float(sys.argv[i])/100.0,0.0),1.0)
    elif arg == "--preview":
        preview = True
    elif arg == "--slower-recommend":
        tryhard = True
    elif imagefn == None:
        imagefn = arg
    elif outfn == None:
        outfn = arg
    else:
        print("Error: too many arguments")
        sys.exit(1)
    i = i + 1

if imagefn is None:
    print("Error: no image filename specified.")
    sys.exit(1)

if outfn and os.path.isfile(outfn):
    print("Warning: output cartridge already exists!")
    print("This script will overwrite the contents of the output cartridge.")
    yn = input("Are you sure you want to continue? ").lower().strip()
    if yn == "y" or yn == "yes":
        print("Overwriting.")
    else:
        print("Canceling.")
        sys.exit(1)

img = cv2.imread(imagefn)

if max(img.shape[0],img.shape[1])>128:
    img = cv2.resize(img, None,
                     fx=128.0/max(img.shape[0],img.shape[1]),
                     fy=128.0/max(img.shape[0],img.shape[1]),
                     interpolation=cv2.INTER_AREA)

if len(palette) > 16:
    print("Generating recommended palette...")
    recommend_dither = dither
    if not tryhard: recommend_dither = 0
    palette = arrangePalette(bestPalette(img, palette, recommend_dither))
    print("Done.")

if preview:
    orig = cv2.resize(img,None,
                      fx=3,fy=3,interpolation=cv2.INTER_NEAREST)
    prev = cv2.resize(getPreview(img,palette,dither),None,
                      fx=3,fy=3,interpolation=cv2.INTER_NEAREST)
    cv2.imshow("Original", orig)
    cv2.imshow("Palette", getPalettePreview(palette))
    cv2.imshow("Converted", prev)
    print("Press any key in the window to continue...")
    cv2.waitKey(0)

if outfn is None:
    print("Warning: No output file specified; no output written.")
    sys.exit(0)

converted = convertImage(img,palette,dither)

with open(outfn,'w') as fp:
    fp.write("pico-8 cartridge // http://www.pico-8.com\n")
    fp.write("version 27\n")
    fp.write("__lua__\n")
    fp.write("pal()\n")
    for idx in palette:
        if idx>15:
            fp.write("poke(0x5f2e,1)\n")
            break
    s = ""
    for i in range(len(palette)):
        idx = (128 * (palette[i] // 16)) + (palette[i] % 16)
        if i != idx: s = s + "[%d]=%d," % (i,idx)
    if len(s)>0:
        s = s[:-1]
        fp.write("pal({%s},1)\n" % (s))

    fp.write("palt(0,false)\nspr(0,0,0,16,16)\nwhile true do end\n")

    fp.write("__gfx__\n")
    for r in range(img.shape[0]):
        for c in range(img.shape[1]):
            fp.write("%1x" % (converted[r,c]))
        for c in range(img.shape[1],128):
            fp.write("0")
        fp.write("\n")
