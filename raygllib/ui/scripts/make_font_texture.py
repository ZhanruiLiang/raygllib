import pygame as pg
import os
import json
import string as String

def make_font_texture(fontname, fontsize, bold, gridsize, m, string, savepath):
    if not string:
        string = String.printable
        # string = [chr(i) for i in range(256)]
    pg.font.init()
    pg.display.init()
    gw, gh = gridsize
    screen = pg.display.set_mode((gw * m, gh * ((len(string) + m - 1) // m)), 0, 32)
    surface = screen.copy().convert_alpha()

    font = pg.font.SysFont(fontname, fontsize, bold=bold)

    x = gw // 2
    y = gh // 2
    surface.fill((0, 0, 0, 0))
    for i, c in enumerate(string):
        tw, th = font.size(c)
        try:
            subSurface = font.render(c, 1, (255, 255, 255, 255))
            surface.blit(subSurface, (x - tw // 2, y - th // 2))
        except ValueError:
            pass
        x += gw
        if (i + 1) % m == 0:
            y += gh
            x = gw // 2
    pg.image.save(surface, savepath)
    config = {
        'fontname': fontname,
        'fontsize': fontsize,
        'gridwidth': gw,
        'gridheight': gh,
        'rowsize': m,
        'string': string,
        'source': os.path.basename(savepath),
    }
    with open(savepath + '.json', 'w') as configfile:
        json.dump(config, configfile)

if __name__ == '__main__':
    import sys
    fontname, fontsize, bold, gridw, gridh, m, string, savepath = sys.argv[1:]
    make_font_texture(fontname, int(fontsize), bool(bold), (int(gridw), int(gridh)), int(m), string, savepath) 
