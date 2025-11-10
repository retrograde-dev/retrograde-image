# Retrograde Image

The `retrograde-image.py` python script converts the layers in open raster image templates into usable png sprite sheets and images for games.

## Use

By default it will try to load a retrograde-image.json file in the same directory.

```bash
python retograde-image
```

You can pass a specific file to it as well.

```bash
python retograde-image images.json
```

## Open Raster Templates

An open raster image (.ora) where each layer represents either a **Variant** or a shared **Visual** component of an image.

For example, a keyboard key template would have **Variant** layers representing each letter or key face, and then have **Visual** layers to represent the key itself.

The image file name and each **Variant** layer name can be used as part of the output file path. See the [Output Variables](#output-variables) section for details.

## Metadata

```json
{
	"name": "<name>",
	"version": "<version>"
}
```

### name

A name to give this configuration.

It is only used for [Output Variables](#output-variables).

### version

A version to give this configuration.

It is only used for [Output Variables](#output-variables).

## Themes

Themes allow you to override the input template's colors.

```json
{
	"themes": {
		"<theme_name>": {
			"<color_name>": "#FFFFFF",
			...
		}
	}
}
```

### themes.\<theme\_name\>: {...}

A unique name to give this theme.

### themes.\<theme\_name\>.\<color\_name\> : \<color\>

Assign a new hex color to a an input's theme by color name.

Both 6 an 8 digit hex codes are allowed. If only 6 digits are provided, the template image's alpha value will be used on a per pixel basis.

* #RRGGBB
* #RRGGBBAA

## Inputs

Inputs define how to load and use your open raster image templates.

```json
{
	"inputs": {
		"<input_name>": {
			"paths": [
				"</path/to/input.ora>"
				...
			],
			"colors": {
				"<color_name>": "#FFFFFF",
				...
			},
			"groups": {
				"<group_name>": {
					"size": [16, 16],
					"variants": [
						"<layer_name>",
						...
					],
					"references": [
						"<reference_name>": "<layer_name>",
						"<reference_name>": {
							"<variant_name>": "<layer_name>",
							...
						}
						...
					]
				},
				...
			},
			"skip": [
				"<layer_name>",
				...
			],
			"frames": {
				"<frame_name>": [
					{
						"layer": "*",
						"groups": ["<group_name>", ...]
						"variants": ["<variant_name>", ...]
						"offset": [0, 0],
						"alpha": 1.0
					},
					{
						"layer": "<reference_name>",
						"groups": ["<group_name>", ...]
						"variants": ["<variant_name>", ...]
						"offset": [0, 0],
						"alpha": 1.0
					},
					{
						"layer": "<layer_name>",
						"groups": ["<group_name>", ...]
						"variants": ["<variant_name>", ...]
						"offset": [0, 0],
						"alpha": 1.0
					}
				]
			},
			"templates": {
				"<template_name>" : [
					"frames": [
						"<frame_name>",
						"<reference_name>",
						"<layer_name>",
						"*",
						{
							"layer": "<reference_name>",
							"groups": ["<group_name>", ...]
							"variants": ["<variant_name>", ...]
							"offset": [0, 0],
							"alpha": 1.0
						},
						{
							"layer": "<layer_name>",
							"groups": ["<group_name>", ...]
							"variants": ["<variant_name>", ...]
							"offset": [0, 0],
							"alpha": 1.0
						},
						{
							"layer": "*",
							"groups": ["<group_name>", ...]
							"variants": ["<variant_name>", ...]
							"offset": [0, 0],
							"alpha": 1.0
						},
						...
					]
				],
				...
			}
		}
	}
}
```

### inputs.\<input\_name\>: {...}

A unique name to give this input.

### inputs.\<input\_name\>.paths: ["\<path\>", ...]

The paths to all open raster image templates that apply to this input.

### inputs.\<input\_name\>.\<color\_name\> : "\<color\>"

The hex color should match a color in your open raster image template and be 6 or 8 digits.

If only a 6 digit hex code is provided, all alpha values with that color will match.

* #RRGGBB
* #RRGGBBAA

## Input Groups

### inputs.\<input\_name\>.groups: {...}

If you want your template to output images of different sizes, you will need to specify a group for each size.

If no groups are specified, one will automatically be created and given the same name as your \<input\_name\>.

### inputs.\<input\_name\>.groups.\<group\_name\>: {...}

A unique name to give your group.

### inputs.\<input\_name\>.groups.\<group\_name\>.size: [\<width\>, \<height\>]

The size of each **Variant** frame.

The following values are allowed:

* [**\<int\>** width, **\<int\>** height]

### inputs.\<input\_name\>.groups.\<group\_name\>.break: \<break\>

If you have continuous set to true in an output config, setting break to true will force the group to go to the next row or column.

The following values are allowed:

* **\<bool\>** break

### inputs.\<input\_name\>.groups.\<group\_name\>.variants: ["\<layer\_name\>", ...]

A list of all **Variant** layers in your open raster image templates that apply to this group.

\<layer\_name\> should match a layer in your open raster image templates.

### inputs.\<input\_name\>.groups.\<group\_name\>.references: {"\<reference\_name\>": "\<layer\_name\>", ...}

An optional mapping of **Visual** layer names to use in your input templates. This allows each groups **Visual** layers to be referenced in the same template.

\<reference\_name\> being a unique name given to use as a reference to an actual \<layer\_name\>.

In the example of a keyboard key template, you might have two groups, one with a **Visual** layer that is 16x16 and another that is 16x32. Each would have a different \<layer\_name\>. By creating a reference to these layers with the same \<reference\_name\> in each group, you can avoid having to create a separate input template for each group.

If a \<reference\_name\> matches a \<layer\_name\>, the \<reference\_name\> will take precedence.

### inputs.\<input\_name\>.groups.\<group\_name\>.references: {"\<reference\_name\>": {"<variant\_name\>": "<layer_name>"}, ...}

You can also reference layers based on the current **Variant**.

### inputs.\<input\_name\>.skip: ["\<layer\_name\>", ...]

If your did not specify any groups, the names of any layer that is not a **Variant** layer should be listed here.

## Input Frames

### inputs.\<input\_name\>.frames: {...}

If you plan on using the same frames in multiple templates, you can specify them here and reference them in your templates so you only have to write them out once.

### inputs.\<input\_name\>.frames.\<frame\_name\>: [...]

Each layer in a referenced frame that satisfies the current group and **Variant** conditions will be outputted in the order that they appear in.

See [Input Templates Frames](#inputsinput_nametemplatestemplate_nameframes-) for layer definitions.

## Input Templates

### inputs.\<input\_name\>.templates: {...}

Templates specify what makes up each frame in an outputted **Variant**.

### inputs.\<input\_name\>.templates.\<template\_name\>: {...}

A unique name to give this input template.

### inputs.\<input\_name\>.templates.\<template\_name\>.frames: [...]

Each frame represents a frame in an animation. For static images, just have a single frame.

### inputs.\<input\_name\>.templates.\<template\_name\>.frames[n]: [...]

Each layer of a frame will be placed one on top of the other in the order specified to form a resulting image.

### inputs.\<input\_name\>.templates.\<template\_name\>.frames[n][n] : "\<frame\_name\>"

Use a specific frame by reference.

### inputs.\<input\_name\>.templates.\<template\_name\>.frames[n][n] : "\<reference\_name\>"

Use a specific layer by reference.

### inputs.\<input\_name\>.templates.\<template\_name\>.frames[n][n] : "\<layer\_name\>"

Use a specific layer by name.

### inputs.\<input\_name\>.templates.\<template\_name\>.frames[n][n] : "*"

Use the current **Variant** layer.

### inputs.\<input\_name\>.templates.\<template\_name\>.frames[n][n].layer : "\<reference\_name\>"

Use a specific layer by reference.

### inputs.\<input\_name\>.templates.\<template\_name\>.frames[n][n].layer : "\<layer\_name\>"

Use a specific layer by name.

### inputs.\<input\_name\>.templates.\<template\_name\>.frames[n][n].layer : "*"

Use the current **Variant** layer.

### inputs.\<input\_name\>.templates.\<template\_name\>.frames[n][n].groups: [<group_name>, ...]

When specified, this layer will only be outputted if the current group is listed.

### inputs.\<input\_name\>.templates.\<template\_name\>.frames[n][n].variants: [<variant_name>, ...]

When specified, this layer will only be outputted if the current **Variant** is listed.

### inputs.\<input\_name\>.templates.\<template\_name\>.frames[n][n].offset: [\<x\>, \<y\>]

Normally each layer is pasted at (0, 0) from the top left corner. This allows you to specify a different offset so that a layer can move around to a different location each frame.

The following values are allowed:

* [**\<int\>** x, **\<int\>** y]

Negative values are allowed.

### inputs.\<input\_name\>.templates.\<template\_name\>.frames[n][n].alpha: 1.0

An alpha value multiplier. Each pixel's alpha value of the current layer will be multiplied by this value. It should be between 0.0 and 1.0.

The following values are allowed:

* [**\<float\>** a]

## Outputs

Outputs define how your inputs your be outputted. These would be the resulting png images you would be using in your projects.

```json
{
	"outputs": {
		"<output_name>": {
			"inputs": [
				"<input_name>"
				...
			],
			"themes": [
				"<theme_name>",
				...
			],
			"path": "./output/[[theme]]",
			"configs": [
				{
					"mode": "images",
					"template": "<template_name>",
					"path": "/[[input]]_[[template]]/[[variant]]",
					"direction": "horizontal",
					"cols": 12,
					"padding": 2
				},
				{
					"mode": "frames",
					"template": "<template_name>",
					"path": "/[[input]]_[[template]]/[[variant]]/[[frame]]",
					"start_index": 0,
					"padding": 2
				},
				{
					"mode": "sheet",
					"template": "<template_name>",
					"path": "/[[image]]_[[template]]",
					"direction": "vertical"
					"rows": 16,
					"padding": 2,
					"group_padding": true
				},
				{
					"mode": "sheet_frames",
					"template": "<template_name>",
					"path": "/[[image]]_[[template]]_[[group]]/[[frame]]",
					"direction": "horizontal"
					"width" 256,
				},
				...
			}
		}
	}
}
```

### outputs.\<output\_name\>: {...}

A unique name given to this output.

### outputs.\<output\_name\>.inputs: ["\<input\_name\>", ...]

A list of input names to use for this output.

### outputs.\<output\_name\>.themes: ["\<theme\_name\>", ...]

A list of theme names to use for this output.

If more than one theme is specified, the `[[theme]]` variable should be used somewhere in the output path.

If no theme is specified, then the original open raster image colors are used.

### outputs.\<output\_name\>.path: "\<path\>"

The main path to output the resulting images to.

### outputs.\<output\_name\>.configs: [...]

A list of output configurations to generate images from.

## Output Configs

### outputs.\<output\_name\>.configs[n].template: "\<template\_name\>"

The name of the input template to use.

### outputs.\<output\_name\>.configs[n].path: "\<path\>"

An additional path value for this config to append to the main output path.

See [Output Image Size](#output-image-size) for more details.

### outputs.\<output\_name\>.configs[n].mode: "\<mode\>"

The method to use when generating output images.

Can be one of the following:

* images
* frames
* sheet
* sheet_frames

The default mode is *images*. See [Output Modes](#output-modes) for details.

### outputs.\<output\_name\>.configs[n].start\_index: \<start\_index\>

The index the [[frame]] variable should start on. Usually 0 or 1.

In modes *images* and *sheet*, [[frame]] will always be this value.

The default is 0.

### outputs.\<output\_name\>.configs[n].direction: "\<direction\>"

The direction image frames are placed in.

Can be one of the following:

* horizontal
* vertical

The default is *horizontal*

For example, if a **Variant** has 4 frames, and the direction is *horizontal*, the frames will be tiled 4x1.

Note that in *images* mode, the width, height, rows, and cols can change this behavior.

For example, if the direction is *horizontal* and cols is 2, 4 frames would be tiled 2x2.

See [Output Image Size](#output-image-size) for more details.

### outputs.\<output\_name\>.configs[n].width: \<width\>

The maximum width of the resulting output image. **Variants** will be tiled to fit.

See [Output Image Size](#output-image-size) for more details.

### outputs.\<output\_name\>.configs[n].height: \<height\>

The maximum height of the resulting output image. **Variants** will be tiled to fit.

See [Output Image Size](#output-image-size) for more details.

### outputs.\<output\_name\>.configs[n].rows: \<rows\>

The maximum number of rows of image **Variants** that are allowed per column.

In *sheet* mode, if multiple groups are being outputted to the same sheet, rows will be sized to fit the first group's **Variant** height or a minimum of the group **Variant** with the largest height.

See [Output Image Size](#output-image-size) for more details.

### outputs.\<output\_name\>.configs[n].cols: \<cols\>

The maximum number of columns of image **Variants** that are allowed per row.

In *sheet* mode, if multiple groups are being outputted to the same sheet, columns will be sized to fit the first group's **Variant** width or a minimum of the group **Variant** with the largest width.

See [Output Image Size](#output-image-size) for more details.

### outputs.\<output\_name\>.configs[n].padding: \<padding\>

The amount of padding to add.

The following values are allowed:

* **\<int\>** top, right, bottom, and left
* [**\<int\>** top and bottom, **\<int\>** left and right]
* [**\<int\>** top, **\<int\>** left and right, **\<int\>** bottom]
* [**\<int\>** top, **\<int\>** right, **\<int\>** bottom, **\<int\>** left]

### outputs.\<output\_name\>.configs[n].group\_padding: \<group\_padding\>

In *sheet* mode, if multiple groups are being outputted to the same sheet, turning group padding on will ensure that the image starts at an offset that is a multiple of the group size.

The following values are allowed:

* **\<bool\>** group\_padding

### outputs.\<output\_name\>.configs[n].continuous: \<continuous\>

In *sheet* mode, if multiple groups are being outputted to the same sheet, turning on continuous will continue tiling **Variants** on the same row or column as the previous group instead of starting on a new row or column.

Depending on the direction of tiling, the row or column will always remain the same size pushing larger **Variants** to the next row or column.

For example if the **Variants** are being tiled horizontally, only **Variants** with the same height will be tiled on the same row.

The following values are allowed:

* **\<bool\>** continuous
* **\<array\>** continuous

If continuous is set to true, all groups will continue tiling on the same row or column when possible.

If it is an array, only the group names within the array will continue tiling.

## Output Modes

### images

This is the default mode used if none is specified.

In this mode each **Variant** gets its own image. If there is more than one frame, then those frames will be tiled in the configurations direction.

If the *cols* or *rows* output config values are specified, the frames will be organized to fit.

So for example a 4 frame template with cols of 2 would generate a 2 frame x 2 frame image.

### frames

In this mode each frame of a **Variant** gets its own image.

The *cols* and *rows* output config values have no effect.

### sheet

In this mode each **Variant** is tiled onto a single image.

The *direction* output config value specifies the direction the frames are tiled in.

If the *cols* or *rows* output config values are specified, the **Variants** will be organized to fit.

If multiple groups are being outputted to the same sheet, each group will start tiling on its own row or column.

When a configuration of mode *sheet* includes `[[group]]` in its path, the sheet will be split into separate group images.

### sheet\_frames

Similar to sheet, only each frame of a template gets its own tiled image.

## Output Image Size

The following configuration values determine how **Variants** are laid out in the image:

* direction
* width
* height
* rows
* cols

If none of width, height, rows, and cols are specified, **Variants** will all be on the same row or column depending on the direction and the image will be sized accordingly.

In *sheet* mode, if at least one of width, height, rows, and cols is specified,  direction only affects the **Variants** frame layout. If none are specified, the **Variants** will be tiled in the opposite of the direction specified.

If width and/or height is set, cols and rows will be ignored.

If only width is set, the height will adjust to fit the tiled **Variant's** frames.

Similarly if only height is set, the width will adjust to fit the tiled **Variant's** frame.

If both are set, one or the other will act as a minimum only, and grow larger if required to fit all **Variants**. The ones that grows will be determined by the tiling direction as well as the minimum size needed to fit a **Variant**.

For example if tiling **Variants** horizontally, the image will automatically grow vertically as needed.

If both rows and cols are specified, one or the other will take precedence based on the direction.

For example, if the direction is *horizontal*, cols will take precedence and rows will grow as needed to fit.

## Output Variables

The following output values support output variables.

* outputs.\<output\_name\>.path
* outputs.\<output\_name\>.configs[n].path

### Available Variables

|Name|Description
|-|-
|**[[name]]**|The metadata name.
|**[[version]]**|The metadata version.
|**[[theme]]**|The name of the current theme.
|**[[variant]]**| The name of the current **Variant** layer.
|**[[frame]]**| The index of the current frame.
|**[[input]]**| The name of the current input.
|**[[output]]**| The name of the current output.
|**[[image]]**| The name of the current input image. If multiple images, the image the current **Variant** will be used.
|**[[group]]**| The name of the current input group.
|**[[template]]**| The name of the current input template.
|**[[mode]]**| The name of the current mode.
|**[[direction]]**| The name of the current direction.
|**[[frame_width]]**| The width of the current **Variant's** frame.
|**[[frame_height]]**| The height of the current **Variant's** frame.
|**[[image_width]]**| The width of the resulting output image.
|**[[image_height]]**| The height of the resulting output image.

If in *sheet* mode and `[[group]]` is in your path, `[[frame_width]]` and `[[frame_height]]` will return the first group's **Variant** frame width and height.

All values by default will be converted to lower case. If you wish to instead capitalize / keep the existing case of a value, prefix it with "^".

For example `[[^mode]]`.

## Output Paths

The resulting output path for each image generated is:

```
outputs.<output_name>.path +
outputs.<output_name>.configs[n].path +
'.png'
```

It is simple appending so ensure your path separators are in order.
