# ImagePaste for Sublime Text

A Sublime Text package that enables copying images from the clipboard to the
project.  Especially useful for Markdown; here the plugin pastes a correct
image link into the file and allows previewing these images inline.

## Features

- Paste images from clipboard directly into Markdown files
- Automatically saves images with timestamped filenames to a defined directory
  in the project.
- Generates proper Markdown image links with URL-encoded paths
- The quick inline preview for Markdown supports various image formats.  E.g.
  for animated gifs the first frame is displayed.
- Cross-platform support (Windows, macOS, Linux) using Python's pillow/PIL
  library.

## Installation

### Package Control (Recommended)
1. Install Package Control if you haven't already
2. Open Command Palette (Ctrl+Shift+P or Cmd+Shift+P)
3. Select "Package Control: Install Package"
4. Search for "ImagePaste" and select it

### Manual Installation
Clone this repository into your Sublime Text Packages directory:

```bash
git clone https://github.com/kaste/ImagePaste.git
```
To pull the dependencies, make sure to call `Package Control: Satisfy Libraries`
from the Command Palette.

## Usage

### Pasting Images
1. Copy an image to your clipboard (screenshot or copy image)
2. In Sublime Text, place your cursor where you want the image
3. Use the command palette or a keyboard shortcut to paste:
   - Command Palette: `ImagePaste: Paste Image`
   - Default shortcut: None (set your own in key bindings)
4. Optionally modify the suggested filename
5. The image will be saved and a Markdown link will be inserted

### Image Preview
1. Open any Markdown file with image links
2. Toggle image preview:
   - Command Palette: `ImagePaste: Toggle Preview`
   - Default shortcut: None (set your own in key bindings)

You can set your own key bindings for the ImagePaste commands by adding them to
your `Default.sublime-keymap`.  Here's [our](https://github.com/kaste/ImagePaste/blob/master/Default.sublime-keymap).


### Configuration

You can configure the image save location using the `image_paste_folder`
setting. This is a so-called view-setting.  Set it in the project file, in the
global Preferences or Syntax settings, or on the view.

```json
{
    "image_paste_folder": "images",         // Relative to the current file
    "image_paste_folder": "//images",       // Relative to project root
    "image_paste_folder": "/absolute/path"  // Absolute path
}
```

If nothing is set, the files are saved besides the open file.  But do note,
that ImagePaste will ask you to confirm or change the final filename.



### CAVEAT

The preview only supports Mardown files.  Technically, it would work with any
files but only for Markdown there are very simple selectors available (fed by
its syntax) to find and grab the linked images.  So, we would need these
"extractors" for rst or other file types to make this feature broadly useful.
