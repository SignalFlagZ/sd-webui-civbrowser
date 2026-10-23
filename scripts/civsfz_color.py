import colorsys
import math
from scripts.civsfz_shared import opts

def hex_color_hsl_to_rgb(h, s, l):
    # param order h,s,l not h,l,s
    if h > 1.0:
        h = h % 360 / 360
    if l > 1.0:
        l = max(min(l / 100, 1.0), 0)
    if s > 1.0:
        s = max(min(s / 100, 1.0), 0)
    (r, g, b) = colorsys.hls_to_rgb(h, l, s)
    return f"#{round(r*255):02x}{round(g*255):02x}{round(b*255):02x}"


def hex_color_hsl_to_rgba(h, s, l, opacity=None):
    # param order h,s,l not h,l,s
    ret = hex_color_hsl_to_rgb(h, s, l)
    if opacity is not None:
        if opacity > 1.0:
            opacity = max(min(opacity / 100, 1.0), 0)
        alpha = f"{round(opacity*255):02x}"
    else:
        alpha = ""
    return f"{ret}{alpha}"


def hls_from_hex(hexrgb):
    (r, g, b) = (int(hexrgb[1:3], 16), int(hexrgb[3:5], 16), int(hexrgb[5:7], 16))
    (r, g, b) = (x / 255 for x in (r, g, b))
    return colorsys.rgb_to_hls(r, g, b)


# Initial values
familyColor: dict = {
    "family1": {
        "value": [
            "Illustrious",
            "Pony",
            "SDXL 1.0",
            "SDXL 0.9",
            "SDXL 1.0 LCM",
            "SDXL Lightning",
            "SDXL Hyper",
            "SDXL Turbo",
        ],
        "color": hex_color_hsl_to_rgb(350, 80, 50),
    },
    "family2": {
        "value": [
            "MOSS Image",
            "Anima",
            "Krea 2",
            "Krea 2 Turbo",
            "Qwen 2.1",
            "ZImageTurbo",
            "ZImageBase",
        ],
        "color": hex_color_hsl_to_rgb(260, 80, 50),
    },
    "family3": {
        "value": [
            "Wan Video 2.7",
            "Wan Video 2.5 I2V",
            "Wan Video 2.5 T2V",
            "Wan Video 2.2 T2V-A14B",
            "Wan Video 2.2 I2V-A14B",
            "Wan Video 2.2 TI2V-5B",
            "Wan Video 14B i2v 720p",
            "Wan Video 14B i2v 480p",
            "Wan Video 14B t2v",
            "Wan Video 1.3B t2v",
            "Wan Video",
        ],
        "color": hex_color_hsl_to_rgb(120, 80, 30),
    },
    "family4": {
        "value": [
            "MiniMax H3",
            "LTXV 2.5",
            "LTXV 2.3",
            "LTXV2",
            "LTXV",
        ],
        "color": hex_color_hsl_to_rgb(170, 80, 40),
    },
    "family5": {
        "value": [
            "Chroma",
            "Flux.3 Klein",
            "Flux.3 Klein-base",
            "Flux.3",
            "Flux 3 Video",
            "Flux.2 Klein 4B-base",
            "Flux.2 Klein 4B",
            "Flux.2 Klein 9B-base",
            "Flux.2 Klein 9B",
            "Flux.2 D",
            "Flux.1 Kontext",
            "Flux.1 Krea",
            "Flux.1 D",
            "Flux.1 S",
        ],
        "color": hex_color_hsl_to_rgb(320, 80, 50),
    },
    "family6": {
        "value": [],
        "color": hex_color_hsl_to_rgb(290, 80, 50),
    },
    "non_family": {
        "value": [],
        "color": hex_color_hsl_to_rgb(250, 14, 30),
    },
}

def autoColorRotate(hexColor: str, num: int, i: int, hue=30, opacity=None):
    h0, l0, s0 = hls_from_hex(hexColor)
    r = 0.25  # radius of helix
    p = 2.5  # pitch of helix
    angle_step = 45.0  # angle step in degrees
    # angle in degrees
    angle_deg = i * angle_step
    angle_rad = math.radians(angle_deg)
    # point on the circle with radius r from the center in H-S plane
    h = h0 + (i * p / 360.0)
    s = s0 * (r * math.cos(angle_rad) + 1.0 - r)
    l = l0 * (r * math.sin(angle_rad) + 1.0)

    return hex_color_hsl_to_rgba(h, s, l, opacity)

def dictBasemodelColors(listBaseModel: list) -> dict:
    ret = {}
    for name in listBaseModel:
        for k, v in familyColor.items():
            family = getattr(opts, "civsfz_" + k, [])
            num = len(family)
            for baseModel in family:
                if name == baseModel:
                    i = family.index(name)
                    hexColor = getattr(opts, "civsfz_color_" + k)
                    ret[name] = autoColorRotate(hexColor, num, i)
                    # print(f"{name}:{k}-{num}:{i}:{hexColor}:{ret[name]}")
        if name not in ret:
            ret[name] = opts.civsfz_color_non_family
    # print(f"{ret}")
    return ret
