
class Color(list):
    def __init__(self, r, g, b, a=1.):
        super().__init__([r, g, b, a])

colorDark = Color(.5, .5, .5, 1.)
colorLight = Color(.8, .8, .8, 1.)
colorActive = Color(.5, .8, .5, 1.)
colorFontLight = Color(.9, .9, .9, 1.)
colorTextInput = Color(.9, .9, .9, 1.)
colorFontDark = Color(.1, .1, .1, 1.)
defaultFontSize = 14
titleFontSize = 16
