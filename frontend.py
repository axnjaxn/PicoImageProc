import wx, os, tempfile, uuid
from threading import Thread

class PaletteControl(wx.Panel):
    def __init__(self, parent, color, title, enabled=True):
        wx.Panel.__init__(self, parent)
        outerBox = wx.BoxSizer(wx.VERTICAL)
        colorBox = wx.Panel(self, size=(32,32))
        colorBox.SetBackgroundColour(color)
        outerBox.Add(colorBox)
        innerBox = wx.BoxSizer(wx.HORIZONTAL)
        innerBox.Add(wx.StaticText(self, 0, title))
        self.checkbox = wx.CheckBox(self)
        self.checkbox.SetValue(enabled)
        innerBox.Add(self.checkbox)
        outerBox.Add(innerBox)
        self.SetSizer(outerBox)
        self.Layout()

    def SetValue(self, enabled):
        self.checkbox.SetValue(enabled)

    def GetValue(self):
        return self.checkbox.GetValue()

class PalettePanel(wx.Panel):
    def __init__(self, parent):
        pal=[
            "#000000","#1d2b53","#7e2553","#008751",
            "#ab5236","#5f574f","#c2c3c7","#fff1e8",
            "#ff004d","#ffa300","#ffec27","#00e436",
            "#29adff","#83769c","#ff77a8","#ffccaa"
        ]

        alt_pal = [
            "#291814","#111d35","#422136","#125359",
            "#742f29","#49333b","#a28879","#f3ef7d",
            "#be1250","#ff6c24","#a8e72e","#00b543",
            "#065ab5","#754665","#ff6e59","#ff9d81"
        ]

        wx.Panel.__init__(self, parent)
        self.parent = parent
        outerBox = wx.BoxSizer(wx.HORIZONTAL)

        # Left portion: grid of palette controls
        self.controls = []
        grid = wx.GridSizer(2, 16, 2, 2)
        colors = [pal, alt_pal]
        for r in range(2):
            for c in range(16):
                self.controls.append(PaletteControl(self, colors[r][c], '%x' % (0x80*r+c)))
                self.controls[-1].Bind(wx.EVT_CHECKBOX, lambda event: self.parent.refreshPreview())
                grid.Add(self.controls[-1])
        outerBox.Add(grid, 1, wx.EXPAND | wx.ALL, 1)

        # Right portion: all/default/none buttons
        innerBox = wx.BoxSizer(wx.VERTICAL)
        innerBox.Add(wx.Panel(self), 1, wx.EXPAND | wx.ALL, 1)
        allBtn = wx.Button(self, 0, "All")
        allBtn.Bind(wx.EVT_BUTTON, lambda event: self.setAll())
        innerBox.Add(allBtn)
        defaultBtn = wx.Button(self, 0, "Default")
        defaultBtn.Bind(wx.EVT_BUTTON, lambda event: self.setDefault())
        innerBox.Add(defaultBtn)
        noneBtn = wx.Button(self, 0, "None")
        noneBtn.Bind(wx.EVT_BUTTON, lambda event: self.setNone())
        innerBox.Add(noneBtn)
        innerBox.Add(wx.Panel(self), 1, wx.EXPAND | wx.ALL, 1)
        outerBox.Add(innerBox)

        self.SetSizer(outerBox)
        self.Layout()

    def setAll(self):
        for ctrl in self.controls: ctrl.SetValue(True)
        self.parent.refreshPreview()

    def setDefault(self):
        for i in range(16):
            self.controls[i].SetValue(True)
            self.controls[i+16].SetValue(False)
        self.parent.refreshPreview()

    def setNone(self):
        for ctrl in self.controls: ctrl.SetValue(False)

    def getPalette(self):
        palette = []
        for i in range(32):
            if self.controls[i].GetValue():
                palette.append(i%16+(i//16)*128)
        return palette

class MainFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title = "PicoImageProc", style = wx.DEFAULT_FRAME_STYLE)
        self.SetMinSize((800, 600))
        self.SetSize((800, 600))

        outerBox = wx.BoxSizer(wx.VERTICAL)

        # Top portion: parameter controls
        innerBox = wx.BoxSizer(wx.HORIZONTAL)
        self.palette_panel = PalettePanel(self)
        innerBox.Add(self.palette_panel, 0, wx.EXPAND | wx.ALL, 1)
        outerBox.Add(innerBox, 0, wx.EXPAND | wx.ALL, 1)

        innerBox = wx.BoxSizer(wx.HORIZONTAL)
        innerBox.Add(wx.StaticText(self, 0, "Dithering"))
        self.dither_box = wx.ComboBox(self, choices=["None", "Ordered", "Floyd-Steinberg"])
        self.dither_box.Bind(wx.EVT_COMBOBOX, lambda event: self.refreshPreview())
        innerBox.Add(self.dither_box)
        self.dither_slider = wx.Slider(self, minValue = 0, maxValue=100, value=70)
        self.dither_slider.Bind(wx.EVT_SLIDER, lambda event: self.refreshPreview())
        innerBox.Add(self.dither_slider)
        outerBox.Add(innerBox, 0, wx.EXPAND | wx.ALL, 1)

        innerBox = wx.BoxSizer(wx.HORIZONTAL)
        innerBox.Add(wx.StaticText(self, 0, "Brightness"))
        self.brightness_slider = wx.Slider(self, minValue = -100, maxValue=100, value=0)
        self.brightness_slider.Bind(wx.EVT_SLIDER, lambda event: self.refreshPreview())
        innerBox.Add(self.brightness_slider, 1, wx.EXPAND | wx.ALL, 1)
        innerBox.Add(wx.StaticText(self, 0, "Contrast"))
        self.contrast_slider = wx.Slider(self, minValue = 1, maxValue=200, value=100)
        self.contrast_slider.Bind(wx.EVT_SLIDER, lambda event: self.refreshPreview())
        innerBox.Add(self.contrast_slider, 1, wx.EXPAND | wx.ALL, 1)
        resetBCBtn = wx.Button(self, 0, "Reset")
        resetBCBtn.Bind(wx.EVT_BUTTON, lambda event: self.resetBrightnessContrast())
        innerBox.Add(resetBCBtn)
        outerBox.Add(innerBox, 0, wx.EXPAND | wx.ALL, 1)

        # Middle portion: image previews
        innerBox = wx.BoxSizer(wx.HORIZONTAL)
        innerBox.Add(wx.Panel(self), 1, wx.EXPAND | wx.ALL, 1)
        image = wx.Image("noimage.png")
        self.image_bmp = wx.StaticBitmap(self,0,wx.Bitmap(image))
        self.image_bmp.SetSize((384,384))
        self.image_bmp.SetScaleMode(wx.StaticBitmap.Scale_AspectFit)
        innerBox.Add(self.image_bmp)
        innerBox.Add(wx.Panel(self, size=(20,1)), 0, wx.EXPAND | wx.ALL, 1)
        self.prev_bmp = wx.StaticBitmap(self,0,wx.Bitmap(image))
        self.prev_bmp.SetSize((384,384))
        self.prev_bmp.SetScaleMode(wx.StaticBitmap.Scale_AspectFit)
        innerBox.Add(self.prev_bmp)
        innerBox.Add(wx.Panel(self), 1, wx.EXPAND | wx.ALL, 1)
        outerBox.Add(innerBox, 1, wx.EXPAND | wx.ALL, 1)

         # Bottom portion: load/save buttons
        innerBox = wx.BoxSizer(wx.HORIZONTAL)
        innerBox.Add(wx.Panel(self), 1, wx.EXPAND | wx.ALL, 1)
        btn = wx.Button(self, 0, "Load Image")
        btn.Bind(wx.EVT_BUTTON, lambda event: self.loadImage())
        innerBox.Add(btn, 0, wx.EXPAND | wx.ALL, 1)
        btn = wx.Button(self, 0, "Save Image")
        btn.Bind(wx.EVT_BUTTON, lambda event: self.saveImage())
        innerBox.Add(btn, 0, wx.EXPAND | wx.ALL, 1)
        btn = wx.Button(self, 0, "Save Cart")
        btn.Bind(wx.EVT_BUTTON, lambda event: self.saveCart())
        innerBox.Add(btn, 0, wx.EXPAND | wx.ALL, 1)
        innerBox.Add(wx.Panel(self), 1, wx.EXPAND | wx.ALL, 1)
        outerBox.Add(innerBox, 0, wx.EXPAND | wx.ALL, 1)

        self.SetSizer(outerBox)
        self.Layout()

        self.tempdir = tempfile.TemporaryDirectory()
        self.imagefn = None
        self.prevfn = None
        self.refreshing = False
        self.waiting = False

    def resetBrightnessContrast(self):
        self.brightness_slider.SetValue(0)
        self.contrast_slider.SetValue(100)
        self.refreshPreview()

    def loadImage(self):
        with wx.FileDialog(self, "Load image",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL: return
            self.imagefn = fileDialog.GetPath()

        self.refreshPreview()

    def saveCart(self):
        cmd = self.buildCommand()
        if cmd is None: return

        with wx.FileDialog(self, "Save cart", wildcard="P8 Cart (*.8)|*.p8",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL: return

            fn = fileDialog.GetPath()
            os.system(cmd + " " + fn)

    def saveImage(self):
        cmd = self.buildCommand()
        if cmd is None: return

        with wx.FileDialog(self, "Save image", wildcard="PNG Image (*.png)|*.png",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL: return

            fn = fileDialog.GetPath()
            os.system(cmd + " --export " + fn)

    def refreshPreview(self):
        if self.imagefn is None: return

        if self.refreshing:
            self.waiting = True
            return

        self.refreshing = True

        try:
            image = wx.Image(self.imagefn)
            self.image_bmp.SetBitmap(wx.Bitmap(image))
        except IOError:
            wx.LogError("Cannot open file '%s'." % newfile)
            return

        image = wx.Image(self.imagefn)
        size = image.GetSize()
        scale = min(384/size[0],384/size[1])
        if scale < 1: resize = wx.IMAGE_QUALITY_BICUBIC
        else: resize = wx.IMAGE_QUALITY_NEAREST
        image = image.Scale(int(scale * size[0]), int(scale * size[1]), resize)
        self.image_bmp.SetBitmap(wx.Bitmap(image))
        self.prev_bmp.SetBitmap(wx.Bitmap(wx.Image("processing.png")))
        self.Layout()
        ProcThread(self)

    def postRefresh(self, prevfn):
        self.prevfn = prevfn
        image = wx.Image(self.prevfn)
        size = image.GetSize()
        scale = min(384/size[0],384/size[1])
        image = image.Scale(int(scale * size[0]), int(scale * size[1]), wx.IMAGE_QUALITY_NEAREST)
        self.prev_bmp.SetBitmap(wx.Bitmap(image))
        self.Layout()

        self.refreshing = False
        if self.waiting:
            self.waiting = False
            self.refreshPreview()

    def buildCommand(self):
        if self.imagefn is None: return None

        pal = self.palette_panel.getPalette()
        if len(pal) == 0: return None

        palfn = self.tempdir.name + "/" + str(uuid.uuid1()) + ".pal"
        with open(palfn, "w") as fp:
            for p in pal:
                fp.write("%d\n" % (p))

        if self.dither_box.GetValue() == "Ordered":
            dither = "--ordered-dither"
        elif self.dither_box.GetValue() == "Floyd-Steinberg":
            dither = "--dither"
        else:
            dither = ""

        if len(dither) > 0:
            dither = " " + dither + " " + "%f" % (self.dither_slider.GetValue())

        return "python3 convert.py --suppress-messages " + self.imagefn \
            + dither \
            + " --brighten " + "%f" % (self.brightness_slider.GetValue()) \
            + " --contrast " + "%f" % (self.contrast_slider.GetValue()) \
            + " --use-palette " + palfn

class ProcThread(Thread):
    def __init__(self, parent):
        self.parent = parent
        Thread.__init__(self)
        self.start()

    def run(self):
        cmd = self.parent.buildCommand()
        if cmd is not None:
            prevfn = self.parent.tempdir.name + "/" + str(uuid.uuid1()) + ".png"
            os.system(cmd + " --export " + prevfn)
        else:
            prevfn = "noimage.png"
        wx.CallAfter(self.parent.postRefresh, (prevfn))

app = wx.App()
frame = MainFrame(None)
frame.Center()
frame.Show()
app.MainLoop()
