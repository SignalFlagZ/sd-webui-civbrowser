import colorsys
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
            "SD 1.5",
            "SD 1.5 LCM",
            "SD 1.5 Hyper",
            "SD 1.4",
            "SD 2.1",
            "SD 2.1 768",
            "SD 2.0",
            "SD 2.0 768",
            "SD 2.1 Unclip",
        ],
        "color": hex_color_hsl_to_rgb(100, 100, 40),
    },
    "family2": {
        "value": [
            "Illustrious",
            "Pony",
            "NoobAI",
            "SDXL 1.0",
            "SDXL 0.9",
            "SDXL 1.0 LCM",
            "SDXL Distilled",
            "SDXL Turbo",
            "SDXL Lightning",
            "SDXL Hyper",
        ],
        "color": hex_color_hsl_to_rgb(15, 100, 45),
    },
    "family3": {
        "value": [
            "Flux.1 D",
            "Flux.1 S",
            "Flux.1 Kontext",
            "SD 3.5",
            "SD 3.5 Large",
            "SD 3.5 Medium",
            "SD 3.5 Large Turbo",
            "SD 3",
        ],
        "color": hex_color_hsl_to_rgb(130, 90, 30),
    },
    "family4": {
        "value": [
            "Wan Video",
            "Wan Video 14B t2v",
            "Wan Video 1.3B t2v",
            "Wan Video 14B i2v 480p",
            "Wan Video 14B i2v 720p",
            "Wan Video 2.2 TI2V-5B",
            "Wan Video 2.2 I2V-A14B",
            "Wan Video 2.2 T2V-A14B"
        ],
        "color": hex_color_hsl_to_rgb(300, 90, 45),
    },
    "family5": {
        "value": [
            "Hunyuan Video",
            "Hunyuan 1",
            "Mochi",
            "SVD",
            "SVD XT",
            "LTXV",
            "CogVideoX",
            "HiDream",
            "OpenAI",
        ],
        "color": hex_color_hsl_to_rgb(330, 90, 45),
    },
    "family6": {
        "value": [],
        "color": hex_color_hsl_to_rgb(75, 70, 45),
    },
    "non_family": {
        "value": [""],
        "color": hex_color_hsl_to_rgb(250, 14, 30),
    },
}

def autoColorRotate(hexColor: str, num: int, i: int, hue=30, opacity=None):
    (h, l, s) = hls_from_hex(hexColor)
    h = h + (hue/(num/3)*(i//4))/360
    l = l * ((1 - (i % 4) / 5) * 0.6 + 0.4)
    s = s * 0.5/num*(num-i)+0.5
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


class BaseModelColors:
    colors = [
        {
            "name": "BASE",
            "label": "Background color for model names",
            "key": "civsfz_background_color_figcaption",
            "property": "--civsfz-background-color-figcaption",
            "color": hex_color_hsl_to_rgb(225, 15, 30),
        },
        {
            "name": "SD 1",
            "label": "Background color for SD1 models",
            "key": "civsfz_background_color_sd1",
            "property": "--civsfz-background-color-sd1",
            "color": hex_color_hsl_to_rgb(90, 70, 30),
        },
        {
            "name": "SD 2",
            "label": "Background color for SD2 models",
            "key": "civsfz_background_color_sd2",
            "property": "--civsfz-background-color-sd2",
            "color": hex_color_hsl_to_rgb(90, 60, 40),
        },
        {
            "name": "SD 3",
            "label": "Background color for SD3 models",
            "key": "civsfz_background_color_sd3",
            "property": "--civsfz-background-color-sd3",
            "color": hex_color_hsl_to_rgb(135, 70, 30),
        },
        {
            "name": "SD 3.",
            "label": "Background color for SD3.5 models",
            "key": "civsfz_background_color_sd35",
            "property": "--civsfz-background-color-sd35",
            "color": hex_color_hsl_to_rgb(150, 80, 40),
        },
        {
            "name": "SDXL",
            "label": "Background color for SDXL models",
            "key": "civsfz_background_color_sdxl",
            "property": "--civsfz-background-color-sdxl",
            "color": hex_color_hsl_to_rgb(15, 70, 40),
        },
        {
            "name": "Pony",
            "label": "Background color for Pony models",
            "key": "civsfz_background_color_pony",
            "property": "--civsfz-background-color-pony",
            "color": hex_color_hsl_to_rgb(15, 90, 40),
        },
        {
            "name": "Illustrious",
            "label": "Background color for Illustrious models",
            "key": "civsfz_background_color_illustrious",
            "property": "--civsfz-background-color-illustrious",
            "color": hex_color_hsl_to_rgb(15, 95, 50),
        },
        {
            "name": "Flux.1",
            "label": "Background color for Flux.1 models",
            "key": "civsfz_background_color_flux1",
            "property": "--civsfz-background-color-flux1",
            "color": hex_color_hsl_to_rgb(330, 80, 40),
        },
    ]

    def __init__(self) -> None:
        pass

    # for macros.jinja
    def name_property_dict(self):
        ret = {}
        for d in self.colors:
            ret[d["name"]] = d["property"]
        # reverse order for sd3.5
        return dict(reversed(list(ret.items())))


# print(f"{BaseModelColors().name_property_dict()}")
