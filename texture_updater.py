import os, sys, ctypes
import json, math
import PIL, PIL.Image
import pygame as pg

# Initialization stage

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = ""
os.chdir(os.path.realpath(os.path.dirname(__file__)))
if sys.platform == "win32":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
elif sys.platform.find("inux") != -1:
    os.environ["SDL_VIDEODRIVER"] = "x11"


def real_path(input_path: str, is_image: bool = False, return_directory: bool = False):
    if input_path == "":
        if return_directory:
            return (input_path, False)
        return input_path
    out = ""
    is_dir = False
    try:
        out = os.path.relpath(os.path.realpath(input_path))
        if out[0:2] == "..":
            raise ValueError
    except ValueError:
        out = os.path.realpath(input_path)
    if os.path.isfile(out):
        if is_image:
            try:
                pg.image.load(out)
            except:
                out = ""
    else:
        is_dir = out != ""
    if return_directory:
        out = (out, is_dir)
    return out


select_position = 0
view_position = [0, 0]
view_scaling = 2
follow_selector = 0
source_dir = "."
conf_path = sys.argv[-1] if len(sys.argv) > 1 else ""
meta_path = ""
texture_path_nobackup = False
texture_path_original = ""

if not os.path.exists(real_path(conf_path)):
    conf_path = input("Path to config file (.conf, leave blank to create new one - drag file here for quick input): ").replace("'", "")
try:
    with open(conf_path, "r", encoding="utf-8") as inp:
        meta_path = real_path(inp.readline().strip())
        if not os.path.exists(meta_path):
            raise FileNotFoundError
        tga_path = real_path(inp.readline().strip(), True)
        texture_path_original = real_path(inp.readline().strip(), True)
        texture_path_nobackup = True
        source_dir = real_path(inp.readline().strip())
        select_position, follow_selector = map(int, inp.readline().strip().split(","))
        view_position[0], view_position[1], view_scaling = map(float, inp.readline().strip().split(","))
        tex_repl = inp.readline().split(",")
except:
    print("Skipped .conf file, or file not found, or file contains error(s).")
    while not os.path.exists(meta_path):
        meta_path = real_path(input("Path to .meta file - drag file here for quick input: ").replace("'", ""))
    tga_path = real_path(input("Path to target .tga file (leave blank to create output.tga - drag file here for quick input): ").replace("'", ""), True)
    tex_repl = []

# Visual editor stage


class render_control(object):
    # class taken from my "flappy clone" project
    def __init__(self):
        pg.font.init()
        self.font = [pg.font.SysFont("monospace", 13), pg.font.SysFont("monospace", 16), pg.font.SysFont("monospace", 30)]
        self.bg = pg.surface.Surface((1, 1), pg.SRCALPHA)

    def text(self, content: str, des: pg.Surface, align: tuple = (0, 0), offset: tuple = (0, 0), area: tuple = None, with_bg: int = 175, color="white", antialiasing: bool = False, size: int = 1):
        # align: (horizontal, vertical) ---- 0: left/top, 1: middle, 2: right/bottom
        __line_list = content.split("\n")
        __line_count = len(__line_list)
        __line_height = self.font[size - 1].get_height() * __line_count
        for __line_index, __line_content in enumerate(__line_list):
            __rendered_text = self.font[size - 1].render(__line_content, antialiasing, color)
            __rendered_text_rect = __rendered_text.get_rect(topleft=(0, 0))
            __area_width, __area_height = area
            __offset_x = (0, __area_width / 2 - __rendered_text_rect.width / 2, __area_width - __rendered_text_rect.width)
            __offset_y = (__rendered_text_rect.height * __line_index, __area_height / 2 - (__line_count * __rendered_text_rect.height) / 2 + __rendered_text_rect.height * __line_index, __area_height - __line_count * __rendered_text_rect.height + __rendered_text_rect.height * __line_index)
            __rendered_text_rect.x = __offset_x[align[0]] + offset[0]
            __rendered_text_rect.y = __offset_y[align[1]] + offset[1]
            if with_bg != 0:
                self.bg.fill((0, 0, 0, with_bg))
                des.blit(pg.transform.scale(self.bg, __rendered_text_rect.size), __rendered_text_rect)
            des.blit(__rendered_text, __rendered_text_rect)
        return __line_height

    def popup(self, content: str, duration: int, lasttime: int):
        if pg.time.get_ticks() - lasttime < duration:
            self.text(content, screen, (1, 1), area=screen.get_size(), with_bg=255, size=3)

    def trigger_popup(self, content: str, duration: int = 3000):
        global popup_content, popup_duration, popup_last_time
        popup_content = content
        popup_duration = duration
        popup_last_time = pg.time.get_ticks()


render = render_control()


def dbg_fill(state: int, spos: int = -1):
    # state: 0 - no texture, 1 - normal, -1 - texture error
    spos = select_position if spos == -1 else spos
    color = (0, 0, 0) if state == 1 else (0, 0, 0, 180)
    dbg_surf.fill(color, tex_pos[spos][0:2] + [tw, th])
    if state == -1:
        render.text("?", dbg_surf, (1, 1), (tex_pos[spos][0:2]), area=(tw, th), with_bg=0, color="red")


def upd_fill(path: str = "", spos: int = -1):
    spos = select_position if spos == -1 else spos
    _cr = tex_pos[spos][0:2] + [tw, th]
    upd_surf.fill((0, 0, 0, 0), _cr)
    upd_mask_surf.fill("white", _cr)
    if os.path.exists(real_path(path, True)):
        _img = PIL.Image.open(path).convert("RGBA")
        upd_surf.blit(pg.image.frombytes(_img.tobytes(), (_img.width, _img.height), "RGBA"), tex_pos[spos][0:2], (0, 0, tw, th))
        upd_mask_surf.fill((0, 0, 0, 0), _cr)
        return 1
    return 0 if path == "" else -1


def save_conf():
    _n = f"{os.path.splitext(os.path.split(meta_path)[1])[0]}.conf"
    _dat = [meta_path, tga_path, texture_path_original, source_dir, ",".join(map(str, (select_position, follow_selector))), ",".join(map(str, view_position + [view_scaling])), ",".join(tex_repl)]
    with open(_n, "w", encoding="utf-8") as out:
        out.write("\n".join(_dat))
    return _n


def export_tex(cre_mipmap: bool = False):
    global texture_path_nobackup, texture_path_original
    _tgap = os.path.split(tga_path)
    _n = os.path.splitext(_tgap[1])
    _f = f"{_n[0]}{_n[1]}"
    _surf = org_surf.copy()
    _surf.blit(upd_mask_surf, (0, 0), special_flags=pg.BLEND_RGBA_MULT)
    _surf.blit(upd_surf, (0, 0))
    _new_path = os.path.join(_tgap[0], _n[0] + "_original" + _n[1])
    if not os.path.exists(_new_path) and not texture_path_nobackup:
        os.rename(tga_path, _new_path)
        texture_path_original = _new_path
        texture_path_nobackup = True
    _img = PIL.Image.frombytes("RGBA", (w, h), pg.image.tobytes(_surf, "RGBA"))
    _img.save(tga_path)
    if cre_mipmap:
        for i in range(1, int(math.log2(tw)) + 1):
            _mtpl = int(math.exp2(i))
            _img.resize((w // _mtpl, h // _mtpl), PIL.Image.Resampling.LANCZOS).save(os.path.join(_tgap[0], _n[0] + f"_mip{i-1}" + _n[1]))
    save_conf()
    return _f


pg.init()
pg.display.set_icon(pg.surface.Surface((0, 0)))
pg.display.set_caption("Texture atlas editor")
screen = pg.display.set_mode((1280, 600), pg.RESIZABLE)
pg_clock = pg.time.Clock()

with open(meta_path, "r") as inp:
    tex_pos = []
    tex_name = []
    for index, tile in enumerate(json.load(inp)):
        tex_pos.extend([i + [index] for i in tile["uvs"]])
        tex_name.append(tile["name"])
    tex_count = len(tex_pos)
    tex_sav_count = len(tex_repl)
    if tex_sav_count < tex_count:
        tex_repl.extend([""] * (tex_count - tex_sav_count))
    elif tex_sav_count > tex_count:
        for i in range(tex_sav_count - tex_count):
            tex_repl.pop()

GUIDE1 = "Close program: Save changes and exit\nEsc: Cancel changes and exit\nCtrl + S: Save changes\nCtrl + E: Export spritesheet\nCtrl + Shift + E: Export spritesheet with mipmaps\n"
GUIDE2 = "Del: Remove current name\n(Ctrl + Del: Apply to all)\nTab: Remove current name and move forward\nBackspace: Remove current name and move backward\nEnter: Use current name from source directory\n(Ctrl + Enter: Apply to all)\n"
GUIDE3 = "Mouse wheel, +, -: Zoom in/out\nMouse drag: Move around\nArrow key, WASD: Select tile\nShift: Toggle follow selector mode\n"
GUIDE4 = "Drag and drop file here for quick replace\nDrag and drop folder here to change source directory\n"

w, h = tex_pos[0][4:6]
tw, th = tex_pos[0][2:4]
tc = w // tw
drag_active = False
_exit = False
zoom_factor = 1
popup_content = ""
popup_duration = 2500
popup_last_time = 0
show_guide = False

dbg_surf = pg.Surface((w, h), pg.SRCALPHA)
upd_surf = dbg_surf.copy()
upd_mask_surf = dbg_surf.copy()
upd_mask_surf.fill("white", (0, 0, w, h))
try:
    org_surf = pg.image.load(texture_path_original)
    texture_path_nobackup = True
except FileNotFoundError:
    try:
        org_surf = pg.image.load(tga_path)
    except FileNotFoundError:
        tga_path = "output.png"
        texture_path_nobackup = True
        org_surf = dbg_surf.copy()
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
                if ev.key == pg.K_F1:
                    show_guide = not show_guide
                if (ev.key == pg.K_s) and (pg.key.get_mods() & pg.KMOD_CTRL):
                    render.trigger_popup(f'Changes saved to "{save_conf()}"')
                    continue
                if (ev.key == pg.K_e) and (pg.key.get_mods() & pg.KMOD_CTRL):
                    if pg.key.get_mods() & pg.KMOD_SHIFT:
                        render.trigger_popup(f'Exported spritesheet to "{export_tex(True)}" (with mipmap)')
                    else:
                        render.trigger_popup(f'Exported spritesheet to "{export_tex()}"')
                    continue
                if ev.key == pg.K_RETURN:
                    _pos = range(tex_count) if (pg.key.get_mods() & pg.KMOD_CTRL) else range(select_position, select_position + 1)
                    for i in _pos:
                        _pth = os.path.join(source_dir, tex_name[tex_pos[i][-1]])
                        _pth = _pth + (".tga" if os.path.exists(_pth + ".tga") else ".png")
                        tex_repl[i] = _pth
                        dbg_fill(upd_fill(_pth, i), i)
                    if i != select_position:
                        render.trigger_popup(f"Successfully applied current name to {tex_count} tiles")
                if ev.key in (pg.K_LSHIFT, pg.K_RSHIFT):
                    follow_selector = 1 - follow_selector
                if ev.key in (pg.K_DELETE, pg.K_BACKSPACE, pg.K_TAB):
                    _pos = range(tex_count) if (ev.key == pg.K_DELETE) and (pg.key.get_mods() & pg.KMOD_CTRL) else range(select_position, select_position + 1)
                    for i in _pos:
                        tex_repl[i] = ""
                        dbg_fill(upd_fill(spos=i), spos=i)
                    if i != select_position:
                        render.trigger_popup(f"Successfully deleted name of {tex_count} tiles")
                if ev.key in (pg.K_MINUS, pg.K_EQUALS):
                    zoom_factor = 1.25 if ev.key == pg.K_EQUALS else 0.8
                if ev.key in (pg.K_RIGHT, pg.K_d, pg.K_TAB, pg.K_RETURN):
                    select_position += 1
                if ev.key in (pg.K_LEFT, pg.K_a, pg.K_BACKSPACE):
                    select_position -= 1
                    select_position = 0 if (ev.key == pg.K_BACKSPACE and select_position < 1) else select_position
                select_position = select_position + (ev.key in (pg.K_DOWN, pg.K_s)) * tc - (ev.key in (pg.K_UP, pg.K_w)) * tc
            case pg.DROPFILE:
                _chk = real_path(ev.file, return_directory=True)
                if _chk[1]:
                    source_dir = _chk[0]
                    render.trigger_popup(f'Current source directory changed to\n"{source_dir}"')
                else:
                    tex_repl[select_position] = _chk[0]
                    dbg_fill(upd_fill(tex_repl[select_position]))
                    select_position += 1 if select_position < tex_count else 0
            case pg.MOUSEWHEEL:
                zoom_factor = 1.25 if ev.y > 0 else 0.8
            case pg.MOUSEBUTTONDOWN:
                _ms = (mx - view_position[0], my - view_position[1])
                drag_active = True
            case pg.MOUSEBUTTONUP:
                drag_active = False
            case pg.MOUSEMOTION if drag_active:
                view_position = [mx - _ms[0], my - _ms[1]]
                follow_selector = 0
    view_position = [round(mx + (view_position[0] - mx) * zoom_factor, 3), round(my + (view_position[1] - my) * zoom_factor, 3)]
    view_scaling = round(view_scaling * zoom_factor, 3)
    zoom_factor = 1
    select_position %= tex_count
    screen.fill((0, 0, 0))
    tex_sel_pos = tex_pos[select_position]
    editor_surf = pg.Surface((math.ceil(screen.get_width() / view_scaling), math.ceil(screen.get_height() / view_scaling)))
    if follow_selector:
        view_position = [screen.get_width() / 2 - tw * view_scaling / 2 - tex_sel_pos[0] * view_scaling, screen.get_height() / 2 - th * view_scaling / 2 - tex_sel_pos[1] * view_scaling]
    sx, sy = math.ceil(view_position[0] / view_scaling) * view_scaling, math.ceil(view_position[1] / view_scaling) * view_scaling
    editor_surf.blit(org_surf, (math.ceil(view_position[0] / view_scaling), math.ceil(view_position[1] / view_scaling)))
    editor_surf.blit(dbg_surf, (math.ceil(view_position[0] / view_scaling), math.ceil(view_position[1] / view_scaling)))
    editor_surf.blit(upd_surf, (math.ceil(view_position[0] / view_scaling), math.ceil(view_position[1] / view_scaling)))
    screen.blit(pg.transform.scale_by(editor_surf, view_scaling), (0, 0))
    pg.draw.rect(screen, "white", (sx, sy, w * view_scaling, h * view_scaling), 1)
    pg.draw.rect(screen, "red", (sx + math.ceil(tex_sel_pos[0] * view_scaling), sy + math.ceil(tex_sel_pos[1] * view_scaling), math.ceil(tw * view_scaling), math.ceil(th * view_scaling)), 2)
    tname = f"{tex_name[tex_sel_pos[-1]]}{" -> " + tex_repl[select_position] if tex_repl[select_position] not in ["0", ""] else ""}"
    _txt_h = render.text(tname, screen, offset=(sx + tex_sel_pos[0] * view_scaling, sy + (tex_sel_pos[1] + th) * view_scaling), area=(0, 0), size=2)
    pg.draw.rect(screen, "black", (sx + tex_sel_pos[0] * view_scaling, sy + (tex_sel_pos[1] + th) * view_scaling + _txt_h, tw * max(3, view_scaling), th * max(3, view_scaling)), 999)
    screen.blit(pg.transform.scale_by(org_surf.subsurface((tex_sel_pos[0:2] + [tw, th])), max(3, view_scaling)), (sx + tex_sel_pos[0] * view_scaling, sy + (tex_sel_pos[1] + th) * view_scaling + _txt_h))
    pg.draw.rect(screen, "white", (sx + tex_sel_pos[0] * view_scaling, sy + (tex_sel_pos[1] + th) * view_scaling + _txt_h, tw * max(3, view_scaling), th * max(3, view_scaling)), 1)
    render.text("Press F1 to show/hide addtional info", screen, (0, 2), area=screen.get_size(), size=1)
    if show_guide:
        tmp = render.text(GUIDE4, screen, (0, 2), area=screen.get_size(), size=1)
        tmp += render.text(GUIDE3, screen, (0, 2), offset=(0, -tmp), area=screen.get_size(), size=1)
        tmp += render.text(GUIDE2, screen, (0, 2), offset=(0, -tmp), area=screen.get_size(), size=1)
        tmp += render.text(GUIDE1, screen, (0, 2), offset=(0, -tmp), area=screen.get_size(), size=1)
        render.text(f"{"Follow selector mode" if follow_selector else ""}\n\nView position: x = {round(view_position[0])}, y = {round(view_position[1])}\nZoom level: {view_scaling}x\n\nDimension: {w}x{h}\nTile size: {tw}x{th}\n\nSource directory: {source_dir}", screen, (2, 2), area=screen.get_size(), size=1)
    render.popup(popup_content, popup_duration, popup_last_time)
    pg.display.update()
    pg_clock.tick(60)
pg.quit()
