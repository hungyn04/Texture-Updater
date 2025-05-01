import os, json, math

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = ""
os.chdir(os.path.realpath(os.path.dirname(__file__)))

import pygame as pg


class render_control(object):
    # class taken from my "flappy clone" project
    def __init__(self):
        pg.font.init()
        self.bg = pg.surface.Surface((1, 1), pg.SRCALPHA)
        self.bg.fill((0, 0, 0, 150))

    def text(self, content: str, des: pg.Surface, align: tuple = (0, 0), offset: tuple = (0, 0), area: tuple = None, with_bg: bool = False, color="white", antialiasing: bool = False, size: float = 20):
        # align: (horizontal, vertical) ---- 0: left/top, 1: middle, 2: right/bottom
        self.font = pg.font.SysFont("Mojangles", size)
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


render = render_control()

_conf = "config.conf"
meta_path = ""
sel_pos = 0
scene_cp = [0, 0]
scale = 2


def rpath(p: str):
    try:
        path = os.path.relpath(os.path.realpath(p))
        if path[0:2] == "..":
            raise ValueError
    except ValueError:
        path = os.path.realpath(p)
    return path


if os.path.exists(rpath(_conf)):
    print("Detected config.conf")
else:
    _conf = input("Path to config file (.conf, leave blank to create new one - drag file here for quick input): ")
    if len(_conf.split(".")) == 1:
        _conf = _conf.strip(".") + ".conf"
try:
    with open(_conf, "r", encoding="utf-8") as inp:
        meta_path = rpath(inp.readline().strip())
        if not os.path.exists(meta_path):
            raise FileNotFoundError
        tga_path = rpath(inp.readline().strip())
        sel_pos = int(inp.readline().strip())
        scene_cp[0], scene_cp[1], scale = list(map(float, inp.readline().strip().split(",")))
        tex_repl = inp.readline().split(",")
except FileNotFoundError:
    print("Skipped .conf file, or file not found, or file contains error(s).")
    while not os.path.exists(meta_path):
        meta_path = rpath(input("Path to .meta file - drag file here for quick input: "))
    tga_path = rpath(input("Path to target .tga file (leave blank to create output.tga - drag file here for quick input): "))
    tex_repl = []

pg.init()
pg.display.set_caption("Edit texture atlas")
screen = pg.display.set_mode((1280, 600), pg.RESIZABLE)
pgc = pg.time.Clock()

with open(meta_path, "r") as inp:
    tex_pos = []
    tex_name = []
    for index, tile in enumerate(json.load(inp)):
        tex_pos.extend([i + [index] for i in tile["uvs"]])
        tex_name.append(tile["name"])
    tex_count = len(tex_pos)
    if len(tex_repl) != tex_count:
        tex_repl = [""] * tex_count

w, h = tex_pos[0][4:6]
tw, th = tex_pos[0][2:4]
tc = w // tw
drag_active = False
_exit = False

upd_surf = pg.Surface((w, h), pg.SRCALPHA)
try:
    org_surf = pg.image.load(tga_path)
except FileNotFoundError:
    org_surf = pg.Surface((w, h), pg.SRCALPHA)

while not _exit:
    mx, my = pg.mouse.get_pos()
    for ev in pg.event.get():
        match ev.type:
            case pg.QUIT:
                _exit = True
            case pg.KEYDOWN:
                if ev.key == pg.K_ESCAPE:
                    exit()
                if ev.key == pg.K_RETURN:
                    tex_repl[sel_pos] = "0"
                if ev.key in (pg.K_DELETE, pg.K_BACKSPACE, pg.K_TAB):
                    tex_repl[sel_pos] = ""
                if ev.key in (pg.K_RIGHT, pg.K_TAB, pg.K_RETURN):
                    sel_pos += 1
                if ev.key in (pg.K_LEFT, pg.K_BACKSPACE):
                    sel_pos -= 1
                    sel_pos = 0 if (ev.key == pg.K_BACKSPACE and sel_pos < 1) else sel_pos
                sel_pos = sel_pos + (ev.key == pg.K_DOWN) * tc - (ev.key == pg.K_UP) * tc
            case pg.DROPFILE:
                tex_repl[sel_pos] = os.path.split(ev.file)[-1]
                sel_pos += 1 if sel_pos < tex_count else 0
            case pg.MOUSEWHEEL:
                _z = 1.25 if ev.y > 0 else 0.8
                scene_cp = [round(mx + (scene_cp[0] - mx) * _z, 3), round(my + (scene_cp[1] - my) * _z, 3)]
                scale = round(scale * _z, 3)
            case pg.MOUSEBUTTONDOWN:
                _ms = (mx - scene_cp[0], my - scene_cp[1])
                drag_active = True
            case pg.MOUSEBUTTONUP:
                drag_active = False
            case pg.MOUSEMOTION if drag_active:
                scene_cp = [mx - _ms[0], my - _ms[1]]
    sel_pos %= tex_count
    """if not _done:
        ci = 0
        out_surf = pg.image.load(f"{TARGET}terrain-atlas.tga")
        for tile in tex_dat:
            for tp in tile["uvs"]:
                if ci == len(tex_repl):
                    if _selected == True:
                        debug_surf.blit(pg.transform.scale_by(pg.image.load(f"{SOURCE}blocks/structure_void.png"), scale), (tp[0] * scale, tp[1] * scale))
                        _selected = False
                    render.text(tile["name"], debug_surf, (0, 0), (tp[0] * scale, tp[1] * scale + (tp[0] // 16) % 3 * 12), (tw * scale, th * scale), with_bg=True)
                    if tile == tex_dat[-1]:
                        break
                    continue
                if ci == len(tex_repl) - 1:
                    _selected = True
                if tex_repl[ci] == "0":
                    debug_surf.fill((255, 0, 0, 150), (tp[0] * scale, tp[1] * scale, tw * scale, th * scale))
                _rc = tex_repl[ci]
                if tex_repl[ci] == "0":
                    _rc = tile["name"]
                if (ci != len(tex_repl)) and (tex_repl[ci] != "0"):
                    out_surf.fill((0, 0, 0, 0), (tp[0], tp[1], tw, th))
                    try:
                        out_surf.blit(pg.image.load(f"{SOURCE}blocks/{_rc}.png"), (tp[0], tp[1]))
                    except FileNotFoundError:
                        try:
                            out_surf.blit(pg.image.load(f"{SOURCE}blocks/{_rc}.tga"), (tp[0], tp[1]))
                        except FileNotFoundError:
                            render.text("ERROR", debug_surf, (1, 1), (tp[0] * scale, tp[1] * scale), (tw * scale, th * scale), color="red")
                ci = min(ci + 1, len(tex_repl))
            else:
                continue
            _done = True
            break"""
    screen.fill((0, 0, 0))
    tex_sel_pos = tex_pos[sel_pos]
    test_surf = pg.Surface((math.ceil(screen.get_width() / scale), math.ceil(screen.get_height() / scale)))
    sx, sy = math.ceil(scene_cp[0] / scale) * scale, math.ceil(scene_cp[1] / scale) * scale

    test_surf.blit(org_surf, (math.ceil(scene_cp[0] / scale), math.ceil(scene_cp[1] / scale)))
    screen.blit(pg.transform.scale_by(test_surf, scale), (0, 0))
    pg.draw.rect(screen, "white", (sx, sy, w * scale, h * scale), 1)
    pg.draw.rect(screen, "red", (sx + math.ceil(tex_sel_pos[0] * scale), sy + math.ceil(tex_sel_pos[1] * scale), math.ceil(tw * scale), math.ceil(th * scale)), 2)
    tname = f"{tex_name[tex_sel_pos[-1]]}{" -> " + tex_repl[sel_pos] if tex_repl[sel_pos] not in ["0", ""] else ""}"
    render.text(tname, screen, offset=(sx + tex_sel_pos[0] * scale, sy + (tex_sel_pos[1] + th) * scale), area=(0, 0), with_bg=True)

    render.text("Close program: Save changes and exit\nEsc: Cancel changes and exit\n\nTab: Skip name\nEnter: Use current name\nBackspace: Remove last name\nR: Reload original name from file\n\nMouse wheel: Zoom in/out\nMouse drag: Move around\nArrow key: Select tile\n\nDrag and drop file here to add its name to config.conf", screen, (0, 2), area=screen.get_size(), with_bg=True, size=10)
    render.text(f"View position: x = {round(scene_cp[0])}, y = {round(scene_cp[1])}\nZoom level: {scale}x\n\nDimension: {w}x{h}\nTile size: {tw}x{th}", screen, (2, 2), area=screen.get_size(), with_bg=True, size=10)
    pg.display.update()
    pgc.tick(60)

with open(f"{os.path.splitext(os.path.split(meta_path)[1])[0]}.conf", "w", encoding="utf-8") as out:
    out.write("\n".join([meta_path, tga_path, str(sel_pos), ",".join(map(str, scene_cp + [scale])), ",".join(tex_repl)]))

pg.image.save(org_surf, "test.png", "png")
pg.quit()
