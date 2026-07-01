from PIL import Image
from pathlib import Path

import argparse
import io
import json
import math
import numpy as np
import re
import xml.etree.ElementTree as ET
import zipfile

class RetrogradeImage:
    _name = None
    _version = None

    _input_name = None
    _input_data = None

    _output_name = None
    _output_data = None

    _theme_name = None
    _theme_data = None

    _config_data = None

    _variant_name = None
    _image_name = None
    _group_name = None
    _layer_name = None
    _frame_index = 0
    _frame_width = 0
    _frame_height = 0
    _image_width = 0
    _image_height = 0

    _references = {}

    _ora_size = {}
    _ora_layers = {}
    _layer_map = {}

    _spinner = [
        "⠋ ", "⠙ ", "⠹ ", "⠸ ", "⠼ ", "⠴ ", "⠦ ", "⠧ ", "⠇ ", "⠏ ",
    ]
    _spinner_index = 0

    _errors = []

    def run(self, config):
        self._reset()

        data = self._load_config(config)

        self._name = data.get("name", "unnamed")
        self._version = data.get("version", "v1.0.0")

        if data.get("inputs") is None:
            self._errors.append("No inputs in config (" + config + ").")
            return

        if data.get("outputs") is None:
            self._errors.append("No outputs in config (" + config + ").")
            return

        for output_name, output_data in data.get("outputs", {}).items():
            if data.get("themes") is None:
                themes = ["Default"]
            else:
                themes = output_data.get("themes", data.get("themes").keys())

            for theme_name in themes:
                for input_name, input_data in data.get("inputs", {}).items():
                    if (not output_data.get("inputs") is None and
                        not input_name in output_data.get("inputs")
                    ):
                        continue

                    if (input_data.get("paths") is None or
                        len(input_data.get("paths")) == 0
                    ):
                        continue

                    self._input_name = input_name
                    self._input_data = input_data
                    self._output_name = output_name
                    self._output_data = output_data

                    for path in input_data.get("paths"):
                        if not Path(path).exists():
                            self._errors.append("Input path not found. (" + path + ")")
                            continue

                        self._load_layer_map(path)

                    if self._input_data.get("groups") is None:
                        groups = {}
                        groups[self._input_name] = {}

                        variants = []
                        for variant_name in self._layer_map.keys():
                            variants.append(variant_name)

                        groups[self._input_name].variants = variants
                        self._input_data["groups"] = groups

                    if data.get("themes") is None or theme_name == "Default":
                        self._theme_name = theme_name
                        self._theme_data = None
                    elif not data["themes"].get(theme_name) is None:
                        self._theme_name = theme_name
                        self._theme_data = data["themes"].get(theme_name)
                    else:
                        self._errors.append("Theme not found. (" + theme_name + ")")
                        continue

                    for config_data in output_data.get("configs", []):
                        if (not config_data.get("inputs") is None and
                            not input_name in config_data.get("inputs")
                        ):
                            continue

                        self._config_data = config_data

                        self._output_config()

        print("\rDone!                                 ")

        if len(self._errors):
            print("The following issues came up:")
            for error in self._errors:
                print(error)

    def _reset(self):
        self._input_name = None
        self._input_data = None

        self._output_name = None
        self._output_data = None

        self._theme_name = None
        self._theme_data = None

        self._config_data = None

        self._variant_name = None
        self._image_name = None
        self._group_name = None
        self._layer_name = None
        self._frame_index = 0
        self._frame_width = 0
        self._frame_height = 0
        self._image_width = 0
        self._image_height = 0

        self._ora_size = {}
        self._ora_layers = {}
        self._layer_map = {}

        self._spinner_index = 0

        self._errors = []

    def _output_config(self):
        self._output_spinner()

        mode = self._config_data.get("mode", "images")

        if mode == "images":
            self._output_images()
        elif mode == "frames":
            self._output_frames()
        elif mode == "sheet":
            self._output_sheet()
        elif mode == "sheet_frames":
            self._output_sheet_frames()
        else:
            self._errors.append("Invalid mode. (" + mode + ")")

    def _output_images(self):
        output_path = self._output_data["path"] + self._config_data.get("path", "") + ".png"

        for group_name, group_data in self._input_data.get("groups", {}).items():
            self._group_name = group_name

            self._references = group_data.get("references", {})

            for variant_name in group_data.get("variants", []):
                variant_name = self._get_reference("*", variant_name)

                if variant_name in self._input_data.get("skip", []):
                    continue

                self._variant_name = variant_name

                if variant_name in self._layer_map.keys():
                    self._image_name = Path(self._layer_map[variant_name]).stem
                else:
                    self._image_name = Path(self._input_data.get("paths")[0]).stem

                self._frame_index = self._config_data.get("start_index", 0)

                (self._frame_width, self._frame_height) = self._get_size_with_padding(
                    self._get_size_from_variant(variant_name),
                    self._get_padding()
                )

                img = self._get_image_from_variant(group_name, variant_name)

                if img == None:
                    continue

                self._image_width = img.width
                self._image_height = img.height

                file = self._clean_path(output_path)

                Path(file).parent.mkdir(parents=True, exist_ok=True)

                img.save(file)

    def _output_frames(self):
        template = self._input_data["templates"][self._config_data["template"]]

        output_path = self._output_data["path"] + self._config_data.get("path", "") + ".png"

        for group_name, group_data in self._input_data.get("groups", {}).items():
            self._group_name = group_name

            self._references = group_data.get("references", {})

            for variant_name in group_data.get("variants", []):
                variant_name = self._get_reference("*", variant_name)

                if variant_name in self._input_data.get("skip", []):
                    continue

                self._variant_name = variant_name

                if variant_name in self._layer_map.keys():
                    self._image_name = Path(self._layer_map[variant_name]).stem
                else:
                    self._image_name = Path(self._input_data.get("paths")[0]).stem

                self._frame_index = self._config_data.get("start_index", 0)

                real_frame_index = 0

                (self._frame_width, self._frame_height) = self._get_size_with_padding(
                    self._get_size_from_variant(variant_name),
                    self._get_padding()
                )

                for frame_index in range(len(template["frames"])):
                    img = self._get_image_from_variant(
                        group_name,
                        variant_name,
                        real_frame_index
                    )

                    if img == None:
                        continue

                    self._image_width = img.width
                    self._image_height = img.height

                    file = self._clean_path(output_path)

                    Path(file).parent.mkdir(parents=True, exist_ok=True)

                    img.save(file)

                    self._frame_index += 1
                    real_frame_index += 1

    def _output_sheet(self):
        output_path = self._output_data["path"] + self._config_data.get("path", "") + ".png"

        width = self._config_data.get("sheet_width", 0)
        height = self._config_data.get("sheet_height", 0)
        cols = self._config_data.get("sheet_cols", 0)
        rows = self._config_data.get("sheet_rows", 0)

        if width <= 0 and height <= 0 and rows <= 0 and cols <= 0:
            if "[[group]]" in output_path:
                self._output_sheet_split_directional(output_path)
            else:
                self._output_sheet_grouped_directional(output_path)
        else:
            if "[[group]]" in output_path:
                self._output_sheet_split_tiled(output_path)
            else:
                self._output_sheet_grouped_tiled(output_path)

    def _output_sheet_frames(self):
        output_path = self._output_data["path"] + self._config_data.get("path", "") + ".png"
        template = self._input_data["templates"][self._config_data["template"]]

        width = self._config_data.get("sheet_width", 0)
        height = self._config_data.get("sheet_height", 0)
        cols = self._config_data.get("sheet_cols", 0)
        rows = self._config_data.get("sheet_rows", 0)

        self._frame_index = self._config_data.get("start_index", 0)
        real_frame_index = 0

        for frame_index in range(len(template["frames"])):
            if width <= 0 and height <= 0 and rows <= 0 and cols <= 0:
                if "[[group]]" in output_path:
                    self._output_sheet_split_directional(output_path, real_frame_index)
                else:
                    self._output_sheet_grouped_directional(output_path, real_frame_index)
            else:
                if "[[group]]" in output_path:
                    self._output_sheet_split_tiled(output_path, real_frame_index)
                else:
                    self._output_sheet_grouped_tiled(output_path, real_frame_index)

            self._frame_index += 1
            real_frame_index += 1

    def _output_sheet_split_directional(self, output_path, frame_index=-1):
        sheet_direction = self._config_data.get("sheet_direction", "horizontal")

        self._variant_name = self._input_name

        for group_name, group_data in self._input_data.get("groups", {}).items():
            self._group_name = group_name

            self._references = group_data.get("references", {})

            img = None

            for variant_name in group_data.get("variants", []):
                variant_name = self._get_reference("*", variant_name)

                if variant_name in self._input_data.get("skip", []):
                    continue

                variant_img = self._get_image_from_variant(
                    group_name,
                    variant_name,
                    frame_index
                )

                if variant_img == None:
                    continue

                if img is None:
                    if variant_name in self._layer_map.keys():
                        self._image_name = Path(self._layer_map[variant_name]).stem
                    else:
                        self._image_name = Path(self._input_data.get("paths")[0]).stem

                    (self._frame_width, self._frame_height) = self._get_size_with_padding(
                        self._get_size_from_variant(variant_name),
                        self._get_padding()
                    )
                    img = variant_img
                    continue

                new_size = None
                new_position = None

                if sheet_direction == "horizontal":
                    new_size = (
                        img.width + variant_img.width,
                        max(img.height, variant_img.height)
                    )
                    new_position = (img.width, 0)
                else:
                    new_size = (
                        max(img.width, variant_img.width),
                        img.height + variant_img.height
                    )
                    new_position = (0, img.height)

                if new_size is None or new_position is None:
                    continue

                new_img = Image.new("RGBA", new_size, (0, 0, 0, 0))

                new_img.paste(img, (0, 0))

                new_img.paste(variant_img, new_position)

                img = new_img

            if img is None:
                return

            self._image_width = img.width
            self._image_height = img.height

            file = self._clean_path(output_path)

            Path(file).parent.mkdir(parents=True, exist_ok=True)

            img.save(file)

    def _output_sheet_grouped_directional(self, output_path, frame_index=-1):
        sheet_direction = self._config_data.get("sheet_direction", "horizontal")
        group_padding = self._config_data.get("group_padding", False)

        img = None

        self._variant_name = self._input_name

        first_group = True

        for group_name, group_data in self._input_data.get("groups", {}).items():
            self._group_name = group_name

            self._references = group_data.get("references", {})

            first_variant = True

            for variant_name in group_data.get("variants", []):
                variant_name = self._get_reference("*", variant_name)

                if variant_name in self._input_data.get("skip", []):
                    continue

                variant_img = self._get_image_from_variant(
                    group_name,
                    variant_name,
                    frame_index
                )

                if variant_img == None:
                    continue

                if img is None:
                    if variant_name in self._layer_map.keys():
                        self._image_name = Path(self._layer_map[variant_name]).stem
                    else:
                        self._image_name = Path(self._input_data.get("paths")[0]).stem

                    (self._frame_width, self._frame_height) = self._get_size_with_padding(
                        self._get_size_from_variant(variant_name),
                        self._get_padding()
                    )

                    img = variant_img
                    continue

                if group_padding and not first_group and first_variant:
                    frame_size = self._get_size_with_padding(
                        self._get_size_from_variant(variant_name),
                        self._get_padding()
                    )

                    new_width = img.width
                    new_height = img.height

                    if img.width % frame_size[0] != 0:
                        new_width = math.ceil(img.width / frame_size[0]) * frame_size[0]

                    if img.height % frame_size[1] != 0:
                        new_height = math.ceil(img.height / frame_size[1]) * frame_size[1]

                    if new_width != img.width or new_height != img.height:
                        new_img = Image.new("RGBA", (new_width, new_height), (0, 0, 0, 0))

                        new_img.paste(img, (0, 0))

                        img = new_img

                new_size = None
                new_position = None

                if sheet_direction == "horizontal":
                    new_size = (
                        img.width + variant_img.width,
                        max(img.height, variant_img.height)
                    )
                    new_position = (img.width, 0)
                else:
                    new_size = (
                        max(img.width, variant_img.width),
                        img.height + variant_img.height
                    )
                    new_position = (0, img.height)

                new_img = Image.new("RGBA", new_size, (0, 0, 0, 0))

                new_img.paste(img, (0, 0))

                new_img.paste(variant_img, new_position)

                img = new_img

                first_variant = False

            first_group = False

        if img is None:
            return

        self._image_width = img.width
        self._image_height = img.height

        file = self._clean_path(output_path)

        Path(file).parent.mkdir(parents=True, exist_ok=True)

        img.save(file)

    def _output_sheet_split_tiled(self, output_path, frame_index=-1):
        self._variant_name = self._input_name

        sheet_direction = self._config_data.get("sheet_direction", "horizontal")

        frame_len = 1
        if frame_index == -1:
            template = self._input_data["templates"][self._config_data["template"]]
            frame_len = len(template["frames"])

        for group_name, group_data in self._input_data.get("groups", {}).items():
            self._group_name = group_name

            self._references = group_data.get("references", {})

            tiling_size = self._get_tiling_size(group_name, frame_len)

            if tiling_size == None:
                continue

            img = None

            offset_x = 0
            offset_y = 0

            cols = self._config_data.get("sheet_cols", 0)
            rows = self._config_data.get("sheet_rows", 0)

            for variant_name in group_data.get("variants", []):
                variant_name = self._get_reference("*", variant_name)

                if variant_name in self._input_data.get("skip", []):
                    continue

                variant_img = self._get_image_from_variant(
                    group_name,
                    variant_name,
                    frame_index
                )

                if variant_img == None:
                    continue

                if img is None:
                    if variant_name in self._layer_map.keys():
                        self._image_name = Path(self._layer_map[variant_name]).stem
                    else:
                        self._image_name = Path(self._input_data.get("paths")[0]).stem

                    (self._frame_width, self._frame_height) = self._get_size_with_padding(
                        self._get_size_from_variant(variant_name),
                        self._get_padding()
                    )

                    # If rows or cols are set instead of width or height, we
                    # only want the image to be as big as needed
                    if rows > 0 or cols > 0:
                        img = Image.new(
                            "RGBA",
                            (variant_img.width, variant_img.height),
                            (0, 0, 0, 0)
                        )
                    elif tiling_size[0] > 0 and tiling_size[1] > 0:
                        img = Image.new(
                            "RGBA",
                            tiling_size,
                            (0, 0, 0, 0)
                        )
                    elif tiling_size[0] > 0:
                        img = Image.new(
                            "RGBA",
                            (tiling_size[0], variant_img.height),
                            (0, 0, 0, 0)
                        )
                    else:
                        img = Image.new(
                            "RGBA",
                            (variant_img.width, tiling_size[1]),
                            (0, 0, 0, 0)
                        )

                    img.paste(variant_img, (0, 0))

                    if sheet_direction == "horizontal":
                        offset_x += variant_img.width
                    else:
                        offset_y += variant_img.height

                    continue

                new_width = img.width
                new_height = img.height
                new_size = None
                new_position = None

                if sheet_direction == "horizontal":
                    if offset_x + variant_img.width > tiling_size[0]:
                        offset_x = 0
                        offset_y += variant_img.height
                    elif offset_x + variant_img.width > img.width:
                        new_width = offset_x + variant_img.width

                    if offset_y + variant_img.height > img.height:
                        new_height = offset_y + variant_img.height

                    if new_width != img.width or new_height != img.height:
                        new_size = (new_width, new_height)

                    new_position = (offset_x, offset_y)

                    offset_x += variant_img.width
                else:
                    if offset_y + variant_img.height > tiling_size[1]:
                        offset_y = 0
                        offset_x += variant_img.width
                    elif offset_y + variant_img.height > img.height:
                        new_height = offset_y + variant_img.height

                    if offset_x + variant_img.width > img.width:
                        new_width = offset_x + variant_img.width

                    if new_width != img.width or new_height != img.height:
                        new_size = (new_width, new_height)

                    new_position = (offset_x, offset_y)

                    offset_y += variant_img.height

                if new_size is None:
                    img.paste(variant_img, new_position)
                else:
                    new_img = Image.new("RGBA", new_size, (0, 0, 0, 0))

                    new_img.paste(img, (0, 0))

                    new_img.paste(variant_img, new_position)

                    img = new_img

            if img is None:
                return

            self._image_width = img.width
            self._image_height = img.height

            file = self._clean_path(output_path)

            Path(file).parent.mkdir(parents=True, exist_ok=True)

            img.save(file)

    def _output_sheet_grouped_tiled(self, output_path, frame_index=-1):
        sheet_direction = self._config_data.get("sheet_direction", "horizontal")
        group_padding = self._config_data.get("group_padding", False)
        continuous = self._config_data.get("continuous", False)

        frame_len = 1
        if frame_index == -1:
            template = self._input_data["templates"][self._config_data["template"]]
            frame_len = len(template["frames"])

        tiling_size = self._get_tiling_size(None, frame_len)

        if tiling_size == None:
            return

        img = None

        offset_x = 0
        offset_y = 0

        cols = self._config_data.get("sheet_cols", 0)
        rows = self._config_data.get("sheet_rows", 0)

        self._variant_name = self._input_name

        last_img = None

        for group_name, group_data in self._input_data.get("groups", {}).items():
            self._group_name = group_name

            self._references = group_data.get("references", {})

            first_variant = True

            for variant_name in group_data.get("variants", []):
                variant_name = self._get_reference("*", variant_name)

                if variant_name in self._input_data.get("skip", []):
                    continue

                variant_img = self._get_image_from_variant(
                    group_name,
                    variant_name,
                    frame_index
                )

                if variant_img == None:
                    continue

                if img is None:
                    if variant_name in self._layer_map.keys():
                        self._image_name = Path(self._layer_map[variant_name]).stem
                    else:
                        self._image_name = Path(self._input_data.get("paths")[0]).stem

                    (self._frame_width, self._frame_height) = self._get_size_with_padding(
                        self._get_size_from_variant(variant_name),
                        self._get_padding()
                    )

                    if rows > 0 or cols > 0:
                        img = Image.new(
                            "RGBA",
                            (variant_img.width, variant_img.height),
                            (0, 0, 0, 0)
                        )
                    elif tiling_size[0] > 0 and tiling_size[1] > 0:
                        img = Image.new(
                            "RGBA",
                            tiling_size,
                            (0, 0, 0, 0)
                        )
                    elif tiling_size[0] > 0:
                        img = Image.new(
                            "RGBA",
                            (tiling_size[0], variant_img.height),
                            (0, 0, 0, 0)
                        )
                    else:
                        img = Image.new(
                            "RGBA",
                            (variant_img.width, tiling_size[1]),
                            (0, 0, 0, 0)
                        )

                    img.paste(variant_img, (0, 0))

                    if sheet_direction == "horizontal":
                        offset_x += variant_img.width
                    else:
                        offset_y += variant_img.height

                    last_img = variant_img

                    first_variant = False
                    continue

                group_continuous = False
                if isinstance(continuous, bool):
                    group_continuous = continuous
                elif group_name in continuous:
                    group_continuous = True

                if group_continuous and not group_data.get("break", False) and first_variant:
                    if sheet_direction == "horizontal":
                        if variant_img.height != last_img.height:
                            offset_x = 0
                            offset_y += last_img.height
                        elif group_padding:
                            frame_size = self._get_size_with_padding(
                                self._get_size_from_variant(variant_name),
                                self._get_padding()
                            )

                            if offset_x % frame_size[0] != 0:
                                offset_x = math.ceil(offset_x / frame_size[0]) * frame_size[0]
                    else:
                        if variant_img.width != last_img.width:
                            offset_x += last_img.width
                            offset_y = 0
                        elif group_padding:
                            frame_size = self._get_size_with_padding(
                                self._get_size_from_variant(variant_name),
                                self._get_padding()
                            )

                            if offset_y % frame_size[1] != 0:
                                offset_y = math.ceil(offset_y / frame_size[1]) * frame_size[1]
                elif first_variant:
                    if sheet_direction == "horizontal":
                        offset_x = 0
                        offset_y += last_img.height
                    else:
                        offset_x += last_img.width
                        offset_y = 0

                first_variant = False

                new_width = img.width
                new_height = img.height
                new_size = None
                new_position = None

                if sheet_direction == "horizontal":
                    if offset_x + variant_img.width > tiling_size[0]:
                        offset_x = 0
                        offset_y += variant_img.height
                    elif offset_x + variant_img.width > img.width:
                        new_width = offset_x + variant_img.width

                    if offset_y + variant_img.height > img.height:
                        new_height = offset_y + variant_img.height

                    if new_width != img.width or new_height != img.height:
                        new_size = (new_width, new_height)

                    new_position = (offset_x, offset_y)

                    offset_x += variant_img.width
                else:
                    if offset_y + variant_img.height > tiling_size[1]:
                        offset_y = 0
                        offset_x += variant_img.width
                    elif offset_y + variant_img.height > img.height:
                        new_height = offset_y + variant_img.height

                    if offset_x + variant_img.width > img.width:
                        new_width = offset_x + variant_img.width

                    if new_width != img.width or new_height != img.height:
                        new_size = (new_width, new_height)

                    new_position = (offset_x, offset_y)

                    offset_y += variant_img.height

                if new_size is None:
                    img.paste(variant_img, new_position)
                else:
                    new_img = Image.new("RGBA", new_size, (0, 0, 0, 0))

                    new_img.paste(img, (0, 0))

                    new_img.paste(variant_img, new_position)

                    img = new_img

                last_img = variant_img

        if img is None:
            return

        self._image_width = img.width
        self._image_height = img.height

        file = self._clean_path(output_path)

        Path(file).parent.mkdir(parents=True, exist_ok=True)

        img.save(file)

    def _get_image_from_variant(self, group_name, variant_name, frame_index=-1):
        template = self._input_data["templates"][self._config_data["template"]]

        if frame_index == -1:
            frames = template["frames"]
        else:
            frames = [template["frames"][frame_index]]

        frames = self._get_frames(group_name, variant_name, frames)

        variant_size = self._get_size_from_variant(variant_name)

        if variant_size == None:
            return None

        frame_direction = self._config_data.get("frame_direction", "horizontal")
        padding = self._get_padding()

        img_size = self._get_size_from_config(
            variant_size,
            padding,
            len(frames)
        )

        img = Image.new("RGBA", img_size, (0, 0, 0, 0))

        row = 0
        col = 0

        padding_x = 0
        padding_y = 0

        if frame_direction == "horizontal":
            padding_y = padding[0]
        else:
            padding_x = padding[3]

        for frame in frames:
            variant_img = None

            if frame_direction == "horizontal":
                padding_x += padding[3]
            else:
                padding_y += padding[0]

            for frame_layer in frame:
                if frame_layer.get("layer", "*") == "*":
                    variant_img = self._get_layer_image(variant_name)
                else:
                    variant_img = self._get_layer_image(
                       self._get_reference(frame_layer.get("layer"), variant_name)
                    )

                if variant_img is None:
                    continue

                variant_img = self._process_image(
                    variant_img,
                    frame_layer.get("alpha", 1.0),
                    frame_layer.get("transforms", [])
                )

                offset = frame_layer.get("offset", [0, 0])

                img = self._paste_image(
                    img,
                    variant_img,
                    (
                        (col * variant_size[0]) + offset[0] + padding_x,
                        (row * variant_size[1]) + offset[1] + padding_y
                    )
                )

            if frame_direction == "horizontal":
                padding_x += padding[1]

                col += 1

                if col > img_size[0] / variant_size[0]:
                    col = 0
                    row += 1
            else:
                padding_y += padding[2]

                row += 1
                if row > img_size[1] / variant_size[1]:
                    row = 0
                    col += 1

        return img

    def _process_image(self, img, alpha=1.0, transforms=[]):
        color_map = self._get_color_map()

        img = self._replace_colors(img, color_map, alpha)

        for transform in transforms:
            if transform == "trim":
                bbox = img.getbbox()
                img = img.crop(bbox)
            elif transform == "flip_h":
                img = img.transpose(Image.FLIP_LEFT_RIGHT)
            elif transform == "flip_v":
                img = img.transpose(Image.FLIP_TOP_BOTTOM)
            elif transform == "rotate_right":
                img = img.transpose(Image.ROTATE_270)
            elif transform == "rotate_left":
                img = img.transpose(Image.ROTATE_90)

        return img

    def _get_color_map(self):
        input_colors = self._input_data.get("colors")

        if input_colors is None:
            return []

        group_colors = self._input_data.get("groups", {}).get(self._group_name, {}).get("colors", {})

        color_map = []

        for color_name, input_color in input_colors.items():
            output_color = input_color

            if color_name in group_colors:
                output_color = self._theme_data.get(group_colors.get(color_name), output_color)
            else:
                output_color = self._theme_data.get(color_name, output_color)

            color_map.append((input_color, output_color))

        return color_map

    def _replace_colors(self, img, color_map, alpha=1.0):
        def hex_to_rgba(h):
            h = h.lstrip('#')
            return tuple(int(h[i:i+2], 16) for i in range(0, len(h), 2))

        replacements = {}

        for src, dst in color_map:
            src_rgba = hex_to_rgba(src)
            dst_rgba = hex_to_rgba(dst)
            key = src_rgba[:3]
            alpha_match = src_rgba[3] if len(src_rgba) == 4 else None
            replacements[key] = (dst_rgba, alpha_match)

        pixels = img.load()

        w, h = img.size

        for y in range(h):
            for x in range(w):
                r, g, b, a = pixels[x, y]

                if (r, g, b) in replacements:
                    new_rgb, req_a = replacements[(r, g, b)]

                    if req_a is None:
                        if len(new_rgb) == 3:
                            pixels[x, y] = (*new_rgb, round(a * alpha))
                        else:
                            pixels[x, y] = (*new_rgb[:3], round(new_rgb[3] * alpha))
                    elif a == req_a:
                        if len(new_rgb) == 3:
                            pixels[x, y] = (*new_rgb, round(a * alpha))
                        else:
                            pixels[x, y] = (*new_rgb[:3], round(new_rgb[3] * alpha))

        return img

    def _paste_image(self, img, variant_img, position):
        # Image.paste does't blend right so we do it manually

        # Ensure pasted image is same size as background image
        layer_img = Image.new("RGBA", img.size, (0,0,0,0))
        layer_img.paste(variant_img, position)

        a_bg = np.asarray(img).astype(np.float32)
        a_fg = np.asarray(layer_img).astype(np.float32)

        bg_rgb = a_bg[..., :3]
        bg_a = a_bg[..., 3:4] / 255.0

        fg_rgb = a_fg[..., :3]
        fg_a = a_fg[..., 3:4] / 255.0

        out_a = fg_a + bg_a * (1 - fg_a)
        out_rgb = fg_rgb * fg_a + bg_rgb * bg_a * (1 - fg_a)

        out = np.concatenate((out_rgb, out_a * 255.0), axis=-1)

        new_img = Image.fromarray(np.clip(np.round(out),0,255).astype('uint8'), 'RGBA')

        return new_img

    def _get_layer_image(self, layer_name):
        path = self._layer_map.get(layer_name)

        if path is None:
            return None

        layers = self._get_layers_from_ora(path)

        for layer in layers:
            if layer[0] == layer_name:
                with zipfile.ZipFile(path, 'r') as z:
                    with z.open(layer[1]) as f:
                        return Image.open(io.BytesIO(f.read())).convert("RGBA")

        return None

    def _get_layers_from_ora(self, path):
        if self._ora_layers.get(path) is not None:
            return self._ora_layers.get(path)

        layers = []

        with zipfile.ZipFile(path, 'r') as z:
            with z.open("stack.xml") as f:
                tree = ET.parse(f)
                root = tree.getroot()

                def process_element(elem):
                    if elem.tag.endswith('layer'):
                        name = elem.attrib.get('name', '')

                        if name != '':
                            source = elem.attrib.get('src')

                            if source:
                                layers.append((name, source))

                    for child in elem:
                        process_element(child)

                process_element(root)

        self._ora_layers[path] = layers

        return layers

    def _get_size_from_variant(self, variant_name):
        if self._input_data.get("groups") is not None:
            for group_name, group_data in self._input_data["groups"].items():
                if variant_name in group_data.get("variants", []):
                    if group_data.get("size") is not None:
                        return group_data.get("size")

        if self._layer_map.get(variant_name) is None:
            self._errors.append("Variant not found. (" + variant_name + ")")
            return None

        return self._get_size_from_ora(self._layer_map.get(variant_name))

    def _get_size_from_ora(self, path):
        if self._ora_size.get(path) is not None:
            return self._ora_size.get(path)

        with zipfile.ZipFile(path, 'r') as z:
            if "mergedimage.png" in z.namelist():
                with z.open("mergedimage.png") as f:
                    img = Image.open(io.BytesIO(f.read()))
                    return img.size

            for name in z.namelist():
                if name.startswith("data/") and name.endswith(".png"):
                    with z.open(name) as f:
                        img = Image.open(io.BytesIO(f.read()))

                        self._ora_size[path] = img.size

                        return img.size

        self._ora_size[path] = None

        return None

    def _get_size_from_config(self, variant_size, padding, frame_len):
        mode = self._config_data.get("mode", 'images')

        real_size = self._get_size_with_padding(variant_size, padding)

        if mode == "frames":
            return real_size

        frame_direction = self._config_data.get("frame_direction", "horizontal")

        width = self._config_data.get("frame_width", 0)
        height = self._config_data.get("frame_height", 0)
        cols = self._config_data.get("frame_cols", 0)
        rows = self._config_data.get("frame_rows", 0)

        if width <= 0 and height <= 0 and rows <= 0 and cols <= 0:
            if frame_direction == "horizontal":
                return (real_size[0] * frame_len, real_size[1])
            else:
                return (real_size[0], real_size[1] * frame_len)

        frame_rows = 0
        frame_cols = 0

        if width <= 0 and height <= 0:
            if rows > 0:
                if cols > 0:
                    if frame_direction == "horizontal":
                        frame_cols = min(cols, frame_len)
                        frame_rows = math.ceil(frame_len / cols)
                    else:
                        frame_cols = math.ceil(frame_len / rows)
                        frame_rows = min(cols, frame_len)
                else:
                    frame_cols = math.ceil(frame_len / rows)
                    frame_rows = min(cols, frame_len)
            else:
                frame_cols = min(cols, frame_len)
                frame_rows = math.ceil(frame_len / cols)

            return (real_size[0] * frame_cols, real_size[1] * frame_rows)

        if width > 0:
            if height > 0:
                if frame_direction == "horizontal":
                    frame_cols = math.floor(width / real_size[0])
                    frame_rows = math.ceil(frame_len / frame_cols)
                else:
                    frame_rows = math.floor(height/ real_size[1])
                    frame_cols = math.ceil(frame_len / frame_rows)
            else:
                frame_cols = math.floor(width / real_size[0])
                frame_rows = math.ceil(frame_len / frame_cols)
        else:
            frame_rows = math.floor(height/ real_size[1])
            frame_cols = math.ceil(frame_len / frame_rows)

        return (real_size[0] * frame_cols, real_size[1] * frame_rows)

    def _get_padding(self):
        padding = self._config_data.get("padding", 0)

        if isinstance(padding, int):
            return (padding, padding, padding, padding)
        elif isinstance(padding, list):
            if len(padding) == 2:
                return (padding[0], padding[1], padding[0], padding[1])
            elif len(padding) == 3:
                return (padding[0], padding[1], padding[2], padding[1])
            elif len(padding) == 4:
                return padding
            else:
                self._errors.append("Invalid padding. (" + self._output_name + ")")
                return (0, 0, 0, 0)
        else:
            self._errors.append("Invalid padding. (" + self._output_name + ")")
            return (0, 0, 0, 0)

    def _get_size_with_padding(self, size, padding, frames=1):
        if size == None:
            new_size = (
                padding[1] + padding[3],
                padding[0] + padding[2],
            )
        else:
            new_size = (
                size[0] + padding[1] + padding[3],
                size[1] + padding[0] + padding[2],
            )

        if frames > 1:
            frame_direction = self._config_data.get("frame_direction", "horizontal")

            if frame_direction == "horizontal":
                new_size = (
                    new_size[0] * frames,
                    new_size[1],
                )
            else:
                new_size = (
                    new_size[0],
                    new_size[1] * frames,
                )

        return new_size

    def _get_tiling_size(self, group_name=None, frame_len = 1):
        width = self._config_data.get("sheet_width", 0)
        height = self._config_data.get("sheet_height", 0)
        cols = self._config_data.get("sheet_cols", 0)
        rows = self._config_data.get("sheet_rows", 0)

        min_size = self._get_min_group_size(group_name, frame_len, False)

        if width <= 0 and height <= 0 and rows <= 0 and cols <= 0:
            return None

        if width > 0:
            if height > 0:
                return (
                    max(width, min_size[0]),
                    max(height, min_size[1])
                )
            else:
                return (
                    max(width, min_size[0]),
                    0
                )
        elif height > 0:
            return (
                0,
                max(height, min_size[1])
            )

        first_min_size = self._get_min_group_size(group_name, frame_len, True)

        if cols > 0:
            if rows > 0:
                return (
                    max(cols * first_min_size[0], min_size[0]),
                    max(rows * first_min_size[1], min_size[1]),
                )
            else:
                return (
                    max(cols * first_min_size[0], min_size[0]),
                    0
                )
        else:
            return (
                0,
                max(rows * first_min_size[1], min_size[1]),
            )

    def _get_min_group_size(self, group_name=None, frame_len=1, first=False):
        width = 0
        height = 0

        for current_group_name, group_data in self._input_data.get("groups", {}).items():
            if group_name != None and group_name != current_group_name:
                continue

            self._references = group_data.get("references", {})

            for variant_name in group_data.get("variants", []):
                self._get_reference("*", variant_name)

                if variant_name in self._input_data.get("skip", []):
                    continue

                variant_size = self._get_size_from_variant(variant_name)

                if variant_size == None:
                    continue

                variant_size = self._get_size_with_padding(
                    variant_size,
                    self._get_padding(),
                    frame_len
                )

                if variant_size[0] > width:
                    width = variant_size[0]

                if variant_size[1] > height:
                    height = variant_size[1]

                break

            if first and (width > 0 or height > 0):
                break

        return (width, height)

    def _get_reference(self, layer_name, variant_name):
        reference = self._references.get(layer_name, layer_name)

        if isinstance(reference, dict):
            if variant_name in reference:
                reference = reference.get(variant_name, layer_name)
            else:
                result = layer_name

                for s in reference:
                    if not s.startswith("/") or not s.endswith("/"):
                        continue

                    pattern = s.strip("/")
                    match = re.search(pattern, variant_name)

                    if match == None:
                        continue

                    result = reference.get(s, layer_name)

                    for index in range(match.lastindex):
                        result = result.replace(
                            "$" + str(index + 1),
                            match.group(index + 1)
                        )

                    break

                reference = result

        if reference == "*":
            return variant_name

        return reference

    def _get_frames(self, group_name, variant_name, frames):
        frame_references = self._input_data.get("frames", {})

        new_frames = []

        for frame in frames:
            new_frame_layers = []

            for frame_layer in frame:
                if isinstance(frame_layer, str):
                    if frame_references.get(frame_layer) == None:
                        new_frame_layers.append({"layer": frame_layer})
                        continue

                    for frame_reference in frame_references.get(frame_layer):
                        if (frame_reference.get("groups") != None and
                            not self._matches_values(
                                group_name,
                                frame_reference.get("groups")
                            )
                        ):
                            continue

                        if (frame_reference.get("variants") != None and
                            not self._matches_values(
                                variant_name,
                                frame_reference.get("variants")
                            )
                        ):
                            continue

                        new_frame_layer = {
                            "layer": frame_reference.get("layer", "*"),
                            "offset": frame_reference.get("offset", [0, 0]),
                            "alpha": frame_reference.get("alpha", 1.0),
                            "transforms": frame_reference.get("transforms", []),
                        }
                        new_frame_layers.append(new_frame_layer)
                else:
                    if (frame_layer.get("groups") != None and
                        not self._matches_values(
                            group_name,
                            frame_layer.get("groups")
                        )
                    ):
                        continue

                    if (frame_layer.get("variants") != None and
                        not self._matches_values(
                            variant_name,
                            frame_layer.get("variants")
                        )
                    ):
                        continue

                    new_frame_layer = {
                        "layer": frame_layer.get("layer", "*"),
                        "offset": frame_layer.get("offset", [0, 0]),
                        "alpha": frame_layer.get("alpha", 1.0),
                        "transforms": frame_layer.get("transforms", []),
                    }
                    new_frame_layers.append(new_frame_layer)

            new_frames.append(new_frame_layers)

        return new_frames

    def _matches_values(self, s, values):
        if s in values:
            return True

        for value in values:
            if value.startswith("/") and value.endswith("/"):
                pattern = s.strip("/")
                match = re.search(pattern, s)

                if match != None:
                    return True

            parts = value.split("*", 1)

            if len(parts) == 2 and s.startswith(parts[0]) and s.endswith(parts[1]):
                return True

        return False

    def _clean_path(self, s):
        sheet_direction = self._config_data.get("sheet_direction", "horizontal")
        frame_direction = self._config_data.get("frame_direction", "horizontal")

        s = s.replace("[[name]]", self._clean_value(self._name))
        s = s.replace("[[version]]", self._clean_value(str(self._version)))
        s = s.replace("[[theme]]", self._clean_value(self._theme_name))
        s = s.replace("[[variant]]", self._clean_value(self._variant_name))
        s = s.replace("[[sheet_direction]]", sheet_direction)
        s = s.replace("[[input]]", self._clean_value(self._input_name))
        s = s.replace("[[output]]", self._clean_value(self._output_name))
        s = s.replace("[[image]]", self._clean_value(self._image_name))
        s = s.replace("[[group]]", self._clean_value(self._group_name))
        s = s.replace("[[template]]", self._clean_value(self._config_data["template"]))
        s = s.replace("[[mode]]", self._config_data.get("mode", "images"))
        s = s.replace("[[frame]]", str(self._frame_index))
        s = s.replace("[[frame_direction]]", frame_direction)
        s = s.replace("[[frame_width]]", str(self._frame_width))
        s = s.replace("[[frame_height]]", str(self._frame_height))
        s = s.replace("[[image_width]]", str(self._image_width))
        s = s.replace("[[image_height]]", str(self._image_height))

        s = s.replace("[[^name]]", self._clean_value(self._name, True))
        s = s.replace("[[^version]]", self._clean_value(str(self._version)))
        s = s.replace("[[^theme]]", self._clean_value(self._theme_name, True))
        s = s.replace("[[^variant]]", self._clean_value(self._variant_name, True))
        s = s.replace("[[^sheet_direction]]", self._clean_value(sheet_direction, True))
        s = s.replace("[[^input]]", self._clean_value(self._input_name, True))
        s = s.replace("[[^output]]", self._clean_value(self._output_name, True))
        s = s.replace("[[^image]]", self._clean_value(self._image_name, True))
        s = s.replace("[[^group]]", self._clean_value(self._group_name, True))
        s = s.replace("[[^template]]", self._clean_value(self._config_data["template"], True))
        s = s.replace("[[^mode]]", self._clean_value(self._config_data.get("mode", "images"), True))
        s = s.replace("[[^frame]]", str(self._frame_index))
        s = s.replace("[[^frame_direction]]", self._clean_value(frame_direction, True))
        s = s.replace("[[^frame_width]]", str(self._frame_width))
        s = s.replace("[[^frame_height]]", str(self._frame_height))
        s = s.replace("[[^image_width]]", str(self._image_width))
        s = s.replace("[[^image_height]]", str(self._image_height))

        return s

    def _clean_value(self, value, title=False):
        if title:
            value = re.sub(r'[^a-zA-Z0-9-_\ \/\.\(\)\[\]]', '', value)
            value.join(word[0].upper() + word[1:] for word in value.split(' '))
            value.join(word[0].upper() + word[1:] for word in value.split('-'))
            value.join(word[0].upper() + word[1:] for word in value.split('_'))
        else:
            value = value.lower()
            value = re.sub(r'[^a-z0-9-_\ \/\.]', '', value)
            value = value.replace(" ", "_").replace("-", "_")

        return value

    def _load_config(self, file):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data

    def _load_layer_map(self, path):
        layers = self._get_layers_from_ora(path)

        for layer in layers:
            self._layer_map[layer[0]] = path

    def _output_spinner(self):
        print("\rGenerating images... " + self._spinner[self._spinner_index], end="", flush=True)
        self._spinner_index = (self._spinner_index + 1) % len(self._spinner)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export images from open raster image template.")
    parser.add_argument(
        "config",
        help="Path to config file. (default: retrograde-image.json)",
        nargs="?",
        default="retrograde-image.json"
    )

    args = parser.parse_args()

    ri = RetrogradeImage()
    ri.run(args.config)
