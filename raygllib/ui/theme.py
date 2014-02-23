
class Color(list):
    def __init__(self, *args):
        if len(args) == 0:
            super().__init__([0., 0., 0., 1.])
        elif len(args) <= 2:
            rgb = args[0]
            a = args[1] if len(args) > 1 else 1.
            super().__init__([
                ((rgb >> 16) & 0xff) / 255,
                ((rgb >> 8) & 0xff) / 255,
                (rgb & 0xff) / 255, 
                a])
        elif len(args) == 3:
            super().__init__(list(args) + [1.])
        elif len(args) == 4:
            super().__init__(args)

colorDark = Color(0x333333)
colorLight = Color(0x666666)
colorButton = Color(0x888888)
colorTitle = Color(0x222222)
colorSubTitle = Color(0x666666)
colorActive = Color(0xCF4B7B)
colorFontLight = Color(0xffffff)
colorTextInput = Color(0xdddddd)
colorFontDark = Color(0x444422)
colorFontDarkHint = Color(0x666666)
colorFocus = Color(0x7F3B63)

fontSizeDefault = 14
fontSizeTitle = 16
fontSizeSmall = 12
fontSizeTitle = 16
fontSizeSubTitle = 14

heightTitle = 18
heightSubTitle = 16
