# ImagePaste for Sublime Text

A Sublime Text package that enables copying images from the clipboard to the
project.  Especially useful for Markdown; here the plugin pastes a correct
image link into the file and allows previewing these images inline.

## Features

- Paste images from clipboard directly into Markdown files.  You can also
  copy and paste images from Finder/Explorer this way. Huh?[1]
- Automatically saves images with timestamped filenames to a defined directory
  in the project.
- Generates proper Markdown image links with URL-encoded paths
- The quick inline preview for Markdown supports various image formats.  E.g.
  for animated gifs the first frame is displayed.
- Cross-platform support (Windows, macOS, Linux) using Python's pillow/PIL
  library.

[1] Either a bitmap is in the clipboard or a file-object.  Does that make sense?
Not sure about the exact nomenclature for these things.


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
That should come very natural:
1. Copy an image to your clipboard (screenshot or file)
2. In Sublime Text, place your cursor where you want the image
3. Use the command palette or a keyboard shortcut to paste:
   - Command Palette: `ImagePaste: Paste Image`
   - Default shortcut: the one you use for "paste", e.g. `ctrl+v`[2]
4. Optionally modify the suggested filename.  (Hit `[ESC]` to abort.)
5. The image will be saved and a link will be inserted

[2] This plugin listens for "paste" commands, and replaces its functionality
**if** an image is in the clipboard.  If there is not, nothing should change.
You can turn this off by setting `leave_my_keys_alone.ImagePaste` in the user
preferences or anywhere where you can define so-called view-settings, e.g.
in the project file, in the syntax settings, or ... well ... on a view.

Using this approach `ctrl+v`/`super+v` just works, just with a wider
feature set.  But also `win+v` (on Windows) just works.  It is not recommended
to make a standard binding *overwriting* `ctrl+v` in your user key bindings.
It would likely also overrule other packages that might bind that same chord,
but with sophisticated contexts.  Think of: GitSavvy, FileBrowser, or others.

Anyway, if you want to bind the command somehow, here are its options with its
defaults.

```json
    {
        "command": "image_paste",
        "args": {
            // delegate to the standard "paste" command, if there is in fact no
            // image in the clipboard.
            "paste_stand_in": true,
            // open the input box to confirm or alter the filename, or to
            // escape the command.
            "confirm_filename": true,
        }
    },

```


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
