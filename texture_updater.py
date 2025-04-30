import os, json
import pygame as pg

os.chdir(os.path.realpath(os.path.dirname(__file__)))
SOURCE = "./vanilla/textures/"
TARGET = "./data/images/"


with open(f"{TARGET}terrain.meta", "r") as inp:
    terrain_dat = json.load(inp)

w, h = terrain_dat[0]["uvs"][0][4:6]
tw, th = terrain_dat[0]["uvs"][0][2:4]

try:
    with open("config.csv", "r") as inp:
        rept = [i for i in inp.read().split(",")]
except FileNotFoundError:
    with open("config.csv", "x") as inp:
        rept = []

pg.init()
scale_factor = 4
screen = pg.display.set_mode((w * 2 + 50, h * 2), pg.RESIZABLE)


class render_control(object):
    def __init__(self):
        pg.font.init()
        self.font = pg.font.SysFont("Mojangles", 10)
        self.bg = pg.surface.Surface((1, 1), pg.SRCALPHA).convert_alpha()
        self.bg.fill((0, 0, 0, 120))

    def text(self, content: str, des: pg.Surface, align: tuple = (0, 0), offset: tuple = (0, 0), area: tuple = None, with_bg: bool = False, color="white", antialiasing: bool = False):
        # align: (horizontal, vertical) ---- 0: left/top, 1: middle, 2: right/bottom
        __line_list = content.split("\n")
        __line_count = len(__line_list)
        for __lindex, __lcurrent in enumerate(__line_list):
            __text = self.font.render(__lcurrent, antialiasing, color)
            __text_rect = __text.get_rect(topleft=(0, 0))
            __w, __h = area if isinstance(area, tuple) else (mcord.ww, mcord.wh)
            __al_offset_x = (0, __w / 2 - __text_rect.width / 2, __w - __text_rect.width)
            __al_offset_y = (__text_rect.height * __lindex, __h / 2 - (__line_count * __text_rect.height) / 2 + __text_rect.height * __lindex, __h - __line_count * __text_rect.height + __text_rect.height * __lindex)
            __text_rect.x = __al_offset_x[align[0]] + offset[0]
            __text_rect.y = __al_offset_y[align[1]] + offset[1]
            if with_bg:
                des.blit(pg.transform.scale(self.bg, __text_rect.size), __text_rect)
            des.blit(__text, __text_rect)


pgc = pg.time.Clock()
render = render_control()
pg.display.set_caption("Preview output texture atlas")

debug_surf = pg.Surface((w * scale_factor + 50, h * scale_factor), pg.SRCALPHA)
scene_cp = mouse_shift = (0, 0)
drag_active = False

_exit = _done = _selected = False
while not _exit:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            _exit = True
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                exit()
            if event.key == pg.K_TAB:
                rept.append("0")
            if event.key == pg.K_RETURN:
                rept.append("1")
            if event.key == pg.K_BACKSPACE:
                rept.pop()
            if event.key == pg.K_r:
                with open("config.csv", "r") as inp:
                    rept = [i for i in inp.read().split(",")]
            _done = False
        if event.type == pg.DROPFILE:
            rept.append(event.file.split("\\")[-1].split(".")[0])
            _done = False
        if event.type == pg.MOUSEBUTTONDOWN:
            mouse_shift = (event.pos[0] - scene_cp[0], event.pos[1] - scene_cp[1])
            drag_active = True
        if event.type == pg.MOUSEBUTTONUP:
            drag_active = False
        if event.type == pg.MOUSEMOTION and drag_active:
            scene_cp = (event.pos[0] - mouse_shift[0], event.pos[1] - mouse_shift[1])
    if not _done:
        ci = 0
        out_surf = pg.image.load(f"{TARGET}terrain-atlas.tga")
        debug_surf.fill((0, 0, 0, 0))
        for tile in terrain_dat:
            for tp in tile["uvs"]:
                if ci == len(rept):
                    if _selected == True:
                        debug_surf.blit(pg.transform.scale_by(pg.image.load(f"{SOURCE}blocks/structure_void.png"), scale_factor), (tp[0] * scale_factor, tp[1] * scale_factor))
                        _selected = False
                    render.text(tile["name"], debug_surf, (0, 0), (tp[0] * scale_factor, tp[1] * scale_factor + (tp[0] // 16) % 3 * 12), (tw * scale_factor, th * scale_factor), with_bg=True)
                    if tile == terrain_dat[-1]:
                        break
                    continue
                if ci == len(rept) - 1:
                    _selected = True
                if rept[ci] == "0":
                    debug_surf.fill((255, 0, 0, 150), (tp[0] * scale_factor, tp[1] * scale_factor, tw * scale_factor, th * scale_factor))
                _rc = rept[ci]
                if rept[ci] == "1":
                    _rc = tile["name"]
                if (ci != len(rept)) and (rept[ci] != "0"):
                    out_surf.fill((0, 0, 0, 0), (tp[0], tp[1], tw, th))
                    try:
                        out_surf.blit(pg.image.load(f"{SOURCE}blocks/{_rc}.png"), (tp[0], tp[1]))
                    except FileNotFoundError:
                        try:
                            out_surf.blit(pg.image.load(f"{SOURCE}blocks/{_rc}.tga"), (tp[0], tp[1]))
                        except FileNotFoundError:
                            render.text("ERROR", debug_surf, (1, 1), (tp[0] * scale_factor, tp[1] * scale_factor), (tw * scale_factor, th * scale_factor), color="red")
                ci = min(ci + 1, len(rept))
            else:
                continue
            _done = True
            break
    screen.fill((0, 0, 0))
    screen.blits(((pg.transform.scale_by(out_surf, scale_factor), scene_cp), (debug_surf, scene_cp)))
    render.text("Esc: Cancel changes\nTab: Skip tile\nEnter: Use current name\nBackspace: Remove last name\nR: Reload name\nDrag and drop file here to add to config.csv", screen, (0, 2), area=screen.get_size(), with_bg=True)
    render.text(f"Dimension: {w}x{h}", screen, (2, 2), area=screen.get_size(), with_bg=True)
    pg.display.update()
    pgc.tick(60)

with open("config.csv", "w") as out:
    out.write(",".join(rept))

pg.image.save(out_surf, "test.png", "png")
pg.quit()
