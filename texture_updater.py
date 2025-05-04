import os, sys, json, math, PIL

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = ""
os.chdir(os.path.realpath(os.path.dirname(__file__)))

import PIL.Image
import pygame as pg


class render_control(object):
    # class taken from my "flappy clone" project
    def __init__(self):
        pg.font.init()
        self.font = [pg.font.SysFont("monospace", 12), pg.font.SysFont("monospace", 20), pg.font.SysFont("monospace", 30)]
        self.bg = pg.surface.Surface((1, 1), pg.SRCALPHA)

    def text(self, content: str, des: pg.Surface, align: tuple = (0, 0), offset: tuple = (0, 0), area: tuple = None, with_bg: int = 175, color="white", antialiasing: bool = False, size: int = 1):
        # align: (horizontal, vertical) ---- 0: left/top, 1: middle, 2: right/bottom
        __line_list = content.split("\n")
        __line_count = len(__line_list)
        for __lindex, __lcurrent in enumerate(__line_list):
            __text = self.font[size - 1].render(__lcurrent, antialiasing, color)
            __text_rect = __text.get_rect(topleft=(0, 0))
            __w, __h = area if isinstance(area, tuple) else (mcord.ww, mcord.wh)
            __al_offset_x = (0, __w / 2 - __text_rect.width / 2, __w - __text_rect.width)
            __al_offset_y = (__text_rect.height * __lindex, __h / 2 - (__line_count * __text_rect.height) / 2 + __text_rect.height * __lindex, __h - __line_count * __text_rect.height + __text_rect.height * __lindex)
            __text_rect.x = __al_offset_x[align[0]] + offset[0]
            __text_rect.y = __al_offset_y[align[1]] + offset[1]
            if with_bg != 0:
                self.bg.fill((0, 0, 0, with_bg))
                des.blit(pg.transform.scale(self.bg, __text_rect.size), __text_rect)
            des.blit(__text, __text_rect)

    def popup(self, content: str, duration: int, lasttime: int):
        if pg.time.get_ticks() - lasttime < duration:
            self.text(content, screen, (1, 1), area=screen.get_size(), with_bg=255, size=3)

    def trigger_popup(self, content: str, duration: int = 3000):
        global p_content, p_duration, p_ltime
        p_content = content
        p_duration = duration
        p_ltime = pg.time.get_ticks()


render = render_control()


def rpath(inp_path: str, is_img: bool = False, allow_return_dir: bool = False):
    if inp_path == "":
        if allow_return_dir:
            return (inp_path, False)
        return inp_path
    out = ""
    is_dir = False
    try:
        out = os.path.relpath(os.path.realpath(inp_path))
        if out[0:2] == "..":
            raise ValueError
    except ValueError:
        out = os.path.realpath(inp_path)
    if os.path.isfile(out):
        if is_img:
            try:
                pg.image.load(out)
            except:
                out = ""
    else:
        is_dir = out != ""
    if allow_return_dir:
        out = (out, is_dir)
    return out


def save_conf():
    _n = f"{os.path.splitext(os.path.split(meta_path)[1])[0]}.conf"
    _dat = [meta_path, tga_path, tga_path_original, source_dir, ",".join(map(str, (sel_pos, follow_selector))), ",".join(map(str, scene_cp + [scale])), ",".join(tex_repl)]
    with open(_n, "w", encoding="utf-8") as out:
        out.write("\n".join(_dat))
    return _n


def export_tex():
    global tga_path_nobackup, tga_path_original
    _tgap = os.path.split(tga_path)
    _n = os.path.splitext(_tgap[1])
    _f = f"{_n[0]}{_n[1]}"
    _surf = org_surf.copy()
    _surf.blit(upd_mask_surf, (0, 0), special_flags=pg.BLEND_RGBA_MULT)
    _surf.blit(upd_surf, (0, 0))
    _new_path = os.path.join(_tgap[0], _n[0] + "_original" + _n[1])
    if not os.path.exists(_new_path) and not tga_path_nobackup:
        os.rename(tga_path, _new_path)
        tga_path_original = _new_path
        tga_path_nobackup = True
    PIL.Image.frombytes("RGBA", (w, h), pg.image.tobytes(_surf, "RGBA")).save(tga_path)
    save_conf()
    return _f


sel_pos = 0
scene_cp = [0, 0]
scale = 2
follow_selector = 0
source_dir = "."
_conf = sys.argv[-1] if len(sys.argv) > 1 else ""
meta_path = ""
tga_path_nobackup = False
tga_path_original = ""

if not os.path.exists(rpath(_conf)):
    _conf = input("Path to config file (.conf, leave blank to create new one - drag file here for quick input): ")

try:
    with open(_conf, "r", encoding="utf-8") as inp:
        meta_path = rpath(inp.readline().strip())
        if not os.path.exists(meta_path):
            raise FileNotFoundError
        tga_path = rpath(inp.readline().strip(), True)
        tga_path_original = rpath(inp.readline().strip(), True)
        tga_path_nobackup = True
        source_dir = rpath(inp.readline().strip())
        sel_pos, follow_selector = map(int, inp.readline().strip().split(","))
        scene_cp[0], scene_cp[1], scale = map(float, inp.readline().strip().split(","))
        tex_repl = inp.readline().split(",")
except:
    print("Skipped .conf file, or file not found, or file contains error(s).")
    while not os.path.exists(meta_path):
        meta_path = rpath(input("Path to .meta file - drag file here for quick input: "))
    tga_path = rpath(input("Path to target .tga file (leave blank to create output.tga - drag file here for quick input): "), True)
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
_z = 1
p_content = ""
p_duration = 2500
p_ltime = 0


dbg_surf = pg.Surface((w, h), pg.SRCALPHA)
upd_surf = dbg_surf.copy()
upd_mask_surf = dbg_surf.copy()
upd_mask_surf.fill("white", (0, 0, w, h))
try:
    org_surf = pg.image.load(tga_path_original)
    tga_path_nobackup = True
except FileNotFoundError:
    try:
        org_surf = pg.image.load(tga_path)
    except FileNotFoundError:
        tga_path = "output.png"
        tga_path_nobackup = True
        org_surf = dbg_surf.copy()


def dbg_fill(state: int, spos: int = -1):
    # state: 0 - no texture, 1 - normal, -1 - texture error
    spos = sel_pos if spos == -1 else spos
    color = (0, 0, 0) if state == 1 else (0, 0, 0, 180)
    dbg_surf.fill(color, tex_pos[spos][0:2] + [tw, th])
    if state == -1:
        render.text("?", dbg_surf, (1, 1), (tex_pos[spos][0:2]), area=(tw, th), with_bg=0, color="red")


def upd_fill(path: str = "", spos: int = -1):
    spos = sel_pos if spos == -1 else spos
    _cr = tex_pos[spos][0:2] + [tw, th]
    upd_surf.fill((0, 0, 0, 0), _cr)
    upd_mask_surf.fill("white", _cr)
    if os.path.exists(rpath(path, True)):
        _img = PIL.Image.open(path).convert("RGBA")
        upd_surf.blit(pg.transform.scale(pg.image.frombytes(_img.tobytes(), (_img.width, _img.height), "RGBA"), [tw, th]), tex_pos[spos][0:2])
        upd_mask_surf.fill((0, 0, 0, 0), _cr)
        return 1
    return 0 if path == "" else -1


for id in range(tex_count):
    dbg_fill(upd_fill(tex_repl[id], id), id)

while not _exit:
    mx, my = pg.mouse.get_pos()
    for ev in pg.event.get():
        match ev.type:
            case pg.QUIT:
                save_conf()
                _exit = True
            case pg.KEYDOWN:
                if ev.key == pg.K_ESCAPE:
                    exit()
                if (ev.key == pg.K_s) and (pg.key.get_mods() & pg.KMOD_CTRL):
                    render.trigger_popup(f'Changes saved to "{save_conf()}"')
                    continue
                if (ev.key == pg.K_e) and (pg.key.get_mods() & pg.KMOD_CTRL):
                    render.trigger_popup(f'Changes exported to "{export_tex()}"')
                    continue
                if ev.key == pg.K_RETURN:
                    _pos = range(tex_count) if (pg.key.get_mods() & pg.KMOD_CTRL) else range(sel_pos, sel_pos + 1)
                    for i in _pos:
                        _pth = os.path.join(source_dir, tex_name[tex_pos[i][-1]])
                        _pth = _pth + (".tga" if os.path.exists(_pth + ".tga") else ".png")
                        tex_repl[i] = _pth
                        dbg_fill(upd_fill(_pth, i), i)
                    if i != sel_pos:
                        render.trigger_popup(f"Successfully applied current name to {tex_count} tiles")
                if ev.key in (pg.K_LSHIFT, pg.K_RSHIFT):
                    follow_selector = 1 - follow_selector
                if ev.key in (pg.K_DELETE, pg.K_BACKSPACE, pg.K_TAB):
                    _pos = range(tex_count) if (ev.key == pg.K_DELETE) and (pg.key.get_mods() & pg.KMOD_CTRL) else range(sel_pos, sel_pos + 1)
                    for i in _pos:
                        tex_repl[i] = ""
                        dbg_fill(upd_fill(spos=i), spos=i)
                    if i != sel_pos:
                        render.trigger_popup(f"Successfully deleted name of {tex_count} tiles")
                if ev.key in (pg.K_MINUS, pg.K_EQUALS):
                    _z = 1.25 if ev.key == pg.K_EQUALS else 0.8
                if ev.key in (pg.K_RIGHT, pg.K_d, pg.K_TAB, pg.K_RETURN):
                    sel_pos += 1
                if ev.key in (pg.K_LEFT, pg.K_a, pg.K_BACKSPACE):
                    sel_pos -= 1
                    sel_pos = 0 if (ev.key == pg.K_BACKSPACE and sel_pos < 1) else sel_pos
                sel_pos = sel_pos + (ev.key in (pg.K_DOWN, pg.K_s)) * tc - (ev.key in (pg.K_UP, pg.K_w)) * tc
            case pg.DROPFILE:
                _chk = rpath(ev.file, allow_return_dir=True)
                if _chk[1]:
                    source_dir = _chk[0]
                    render.trigger_popup(f'Current source directory changed to\n"{source_dir}"')
                else:
                    tex_repl[sel_pos] = _chk[0]
                    dbg_fill(upd_fill(tex_repl[sel_pos]))
                    sel_pos += 1 if sel_pos < tex_count else 0
            case pg.MOUSEWHEEL:
                _z = 1.25 if ev.y > 0 else 0.8
            case pg.MOUSEBUTTONDOWN:
                _ms = (mx - scene_cp[0], my - scene_cp[1])
                drag_active = True
            case pg.MOUSEBUTTONUP:
                drag_active = False
            case pg.MOUSEMOTION if drag_active:
                scene_cp = [mx - _ms[0], my - _ms[1]]
                follow_selector = 0
    scene_cp = [round(mx + (scene_cp[0] - mx) * _z, 3), round(my + (scene_cp[1] - my) * _z, 3)]
    scale = round(scale * _z, 3)
    _z = 1
    sel_pos %= tex_count
    screen.fill((0, 0, 0))
    tex_sel_pos = tex_pos[sel_pos]
    test_surf = pg.Surface((math.ceil(screen.get_width() / scale), math.ceil(screen.get_height() / scale)))
    if follow_selector:
        scene_cp = [screen.get_width() / 2 - tw * scale / 2 - tex_sel_pos[0] * scale, screen.get_height() / 2 - th * scale / 2 - tex_sel_pos[1] * scale]
    sx, sy = math.ceil(scene_cp[0] / scale) * scale, math.ceil(scene_cp[1] / scale) * scale
    test_surf.blit(org_surf, (math.ceil(scene_cp[0] / scale), math.ceil(scene_cp[1] / scale)))
    test_surf.blit(dbg_surf, (math.ceil(scene_cp[0] / scale), math.ceil(scene_cp[1] / scale)))
    test_surf.blit(upd_surf, (math.ceil(scene_cp[0] / scale), math.ceil(scene_cp[1] / scale)))
    screen.blit(pg.transform.scale_by(test_surf, scale), (0, 0))

    pg.draw.rect(screen, "white", (sx, sy, w * scale, h * scale), 1)
    pg.draw.rect(screen, "red", (sx + math.ceil(tex_sel_pos[0] * scale), sy + math.ceil(tex_sel_pos[1] * scale), math.ceil(tw * scale), math.ceil(th * scale)), 2)
    tname = f"{tex_name[tex_sel_pos[-1]]}{" -> " + tex_repl[sel_pos] if tex_repl[sel_pos] not in ["0", ""] else ""}"
    render.text(tname, screen, offset=(sx + tex_sel_pos[0] * scale, sy + (tex_sel_pos[1] + th) * scale), area=(0, 0), size=2)
    pg.draw.rect(screen, "black", (sx + tex_sel_pos[0] * scale, sy + (tex_sel_pos[1] + th) * scale + 23, tw * max(3, scale), th * max(3, scale)), 999)
    screen.blit(pg.transform.scale_by(org_surf.subsurface((tex_sel_pos[0:2] + [tw, th])), max(3, scale)), (sx + tex_sel_pos[0] * scale, sy + (tex_sel_pos[1] + th) * scale + 23))
    pg.draw.rect(screen, "white", (sx + tex_sel_pos[0] * scale, sy + (tex_sel_pos[1] + th) * scale + 23, tw * max(3, scale), th * max(3, scale)), 1)

    render.text("Close program: Save changes and exit\nEsc: Cancel changes and exit\nCtrl + S: Save changes\nCtrl + E: Export changes to image\n\nDel: Remove current name\n(Ctrl + Del: Apply to all)\nTab: Remove current name and move forward\nBackspace: Remove current name and move backward\nEnter: Use current name from source directory\n(Ctrl + Enter: Apply to all)\n\nMouse wheel, +, -: Zoom in/out\nMouse drag: Move around\nArrow key, WASD: Select tile\nShift: Toggle follow selector mode\n\nDrag and drop file here for quick replace\nDrag and drop folder here to change source directory", screen, (0, 2), area=screen.get_size(), size=1)
    render.text(f"{"Follow selector mode" if follow_selector else ""}\n\nView position: x = {round(scene_cp[0])}, y = {round(scene_cp[1])}\nZoom level: {scale}x\n\nDimension: {w}x{h}\nTile size: {tw}x{th}\n\nSource directory: {source_dir}", screen, (2, 2), area=screen.get_size(), size=1)
    render.popup(p_content, p_duration, p_ltime)
    pg.display.update()
    pgc.tick(60)

pg.quit()
