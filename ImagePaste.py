from __future__ import annotations
import base64
import datetime
import io
from itertools import zip_longest
import os
from pathlib import Path
import re
import shutil
import tempfile
from urllib.parse import quote as uri_quote

from PIL import Image, ImageGrab

import sublime
import sublime_plugin


class image_paste_injector(sublime_plugin.EventListener):
    def on_text_command(
        self,
        view: sublime.View,
        command_name: str,
        args: sublime.CommandArgs | None
    ) -> tuple[str, sublime.CommandArgs] | None:
        if (
            command_name == "paste"
            and not view.settings().get("leave_my_keys_alone.ImagePaste")
        ):
            return ("image_paste", {"paste_stand_in": True})
        return None


class image_paste(sublime_plugin.TextCommand):
    def run(self, edit, confirm_filename=True, paste_stand_in=True):
        view = self.view
        settings = view.settings()
        window = view.window()
        if not window:
            return

        clipboard_image = grab_clipboard()
        if not clipboard_image:
            if paste_stand_in:
                view.run_command("paste")
            else:
                window.status_message("No image in clipboard")
            return

        try:
            root_dir = get_root_dir(view)
        except ValueError as e:
            print("ImagePaste:", e)
            root_dir = str(Path().home())

        full_path = save_clipboard_image(clipboard_image, root_dir)
        if confirm_filename:
            def on_done(input_string):
                if not input_string:
                    on_cancel()
                    return

                dir = os.path.dirname(input_string)
                settings.set("image_paste_last_used_dir", dir)
                os.makedirs(dir, exist_ok=True)
                shutil.move(full_path, input_string)
                self.insert_image_path(input_string)

            def on_cancel():
                try:
                    os.remove(full_path)
                    os.rmdir(os.path.dirname(full_path))
                except Exception:
                    pass

            window.show_input_panel("Filename:", full_path, on_done, None, on_cancel)

        else:
            self.insert_image_path(full_path)

    def insert_image_path(self, full_path: str) -> None:
        view = self.view
        file_name = view.file_name()
        if file_name:
            text_to_insert_ = os.path.relpath(full_path, os.path.dirname(file_name))
        else:
            text_to_insert_ = full_path
        text_to_insert = text_to_insert_.replace("\\", "/")
        for pos in view.sel():
            scope_at_pos = view.scope_name(pos.begin())
            for scope, fn in transformers:
                if scope in scope_at_pos:
                    view.run_command("insert_snippet", {"contents": fn(text_to_insert)})
                    break
            else:
                view.run_command("insert", {"characters": text_to_insert})
            break


transformers = [
    ("text.html.markdown", lambda filename: f"![$0]({escape_for_md(filename)})"),
    ("text.restructuredtext", lambda f: f".. $0image:: {escape_for_rst(f)}"),
]


def get_root_dir(view: sublime.View) -> str:
    root = view.settings().get("image_paste_folder")
    if root:
        if root.startswith('//'):
            window = view.window()
            if not window:
                raise ValueError(
                    f"view is detached but image_paste_folder ('{root}') "
                    f"is set to be relative to one."
                )
            folders = window.folders()
            if not folders:
                raise ValueError(
                    f"window has no folders attached to it but image_paste_folder ('{root}') "
                    f"is set to be relative to one."
                )
            return os.path.join(folders[0], root[2:])
        if os.path.isabs(root):
            return root
        if file_name := view.file_name():
            return os.path.normpath(os.path.join(os.path.dirname(file_name), root))
        raise ValueError(
            f"view is unnamed but image_paste_folder ('{root}') "
            f"is set to be relative to one."
        )

    if (
        (last_used := view.settings().get("image_paste_last_used_dir"))
        and os.path.exists(last_used)
    ):
        return last_used
    if file_name := view.file_name():
        return os.path.dirname(file_name)
    if (window := view.window()) and (folders := window.folders()):
        return folders[0]
    raise ValueError("view is unnamed and 'image_paste_folder' is not set.")


def grab_clipboard() -> Image.Image | None:
    """Cross-platform function to grab an image from the clipboard.

    Raises:
        ImportError: If required modules like PIL.ImageGrab are not available on the system
    """
    # ImageGrab.grabclipboard() can raise ImportError on some platforms
    clipboard_image = ImageGrab.grabclipboard()
    if isinstance(clipboard_image, list):
        for item in clipboard_image:
            if isinstance(item, str) and os.path.isfile(item):
                try:
                    clipboard_image = Image.open(item)
                    break
                except (OSError, IOError):
                    pass

    if not isinstance(clipboard_image, Image.Image):
        return None
    return clipboard_image


def save_clipboard_image(image: Image.Image, root_dir: str) -> str:
    """
    Saves an image from the clipboard as a PNG file (or JPG if PNG is not
    possible), and returns the filename.  If the image is already saved, it is
    just copied to the specified directory.

    Args:
        image (Image.Image): The image to save.
        root_dir (str): The directory where the image will be saved.

    Returns:
        str: The filename of the saved image.

    Raises: ValueError: If the image cannot be processed or saved in the
            specified formats.
    """
    if image.filename:
        os.makedirs(root_dir, exist_ok=True)
        return shutil.copy2(image.filename, root_dir)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H%M%S")
    base_filename = f"Screenshot {timestamp}"
    temp_dir = tempfile.gettempdir()

    # Try saving in different formats
    for format, extension in (("PNG", "png"), ("JPEG", "jpg")):
        filename = f"{base_filename}.{extension}"
        temporary_location = os.path.join(temp_dir, filename)
        try:
            image.save(temporary_location, format)
        except (OSError, ValueError):
            continue
        break

    else:
        raise ValueError("Failed to save image in any of the supported formats")

    final_path = os.path.join(root_dir, filename)
    os.makedirs(root_dir, exist_ok=True)
    shutil.move(temporary_location, final_path)
    return final_path


class image_preview(sublime_plugin.TextCommand):
    phantom_set = None
    key = "image_paste_previews"

    def run(self, edit):
        view = self.view
        if not self.phantom_set:
            self.phantom_set = sublime.PhantomSet(view, self.key)

        imgage_link_regions = view.find_by_selector("markup.underline.link.image.markdown")
        images_to_show = []
        for region in imgage_link_regions:
            image_link = view.substr(region)
            file_name = view.file_name()
            if not os.path.isabs(image_link):
                file_name = view.file_name()
                if not file_name:
                    continue
                path = os.path.normpath(os.path.dirname(file_name))
                image_link = f"{Path(path).as_uri()}/{image_link}"
            images_to_show.append((image_link, region))

        max_width = int(60 * view.em_width())
        phantoms = []
        for image_link, region in images_to_show:
            real_file = from_uri(image_link)
            src = encode_image_to_src(real_file)
            width, height = calculate_image_dimensions(real_file, max_width)
            if width is not None and height is not None:
                content = f"<img src='{src}' width='{width}' height='{height}'/>"
            else:
                content = f"<img src='{src}'/>"
            phantoms.append(sublime.Phantom(region, content, sublime.PhantomLayout.BELOW))

        unchanged = all(a == b for a, b in zip_longest(phantoms, self.phantom_set.phantoms))
        if unchanged:
            self.phantom_set.update([])
        else:
            self.phantom_set.update(phantoms)


def encode_image_to_src(filename: str) -> str:
    """Reads an image file, converts if necessary, and returns an HTML-compatible src string."""
    supported_formats = ('.png', '.jpg', '.jpeg')
    file_ext = os.path.splitext(filename)[1].lower()

    # If already supported, read directly
    if file_ext in supported_formats:
        img_format = "jpeg" if file_ext == ".jpg" else file_ext.lstrip('.')
        with open(filename, "rb") as img_file:
            encoded_string = base64.b64encode(img_file.read()).decode("utf-8")
        return f'data:image/{img_format};base64,{encoded_string}'

    # Otherwise, convert to PNG
    with Image.open(filename) as img:
        buffered = io.BytesIO()
        img.convert("RGBA").save(buffered, format="PNG")  # Convert & save as PNG
        encoded_string = base64.b64encode(buffered.getvalue()).decode("utf-8")

    return f'data:image/png;base64,{encoded_string}'


def calculate_image_dimensions(
    image_path: str, max_width: int
) -> tuple[int, int] | tuple[None, None]:
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            if width > max_width:
                ratio = max_width / width
                return int(width * ratio), int(height * ratio)
            return width, height
    except Exception:
        return None, None


def from_uri(uri: str) -> str:  # roughly taken from Python 3.13
    """Return a new path from the given 'file' URI."""
    from urllib.parse import unquote_to_bytes
    if not uri.startswith('file:'):
        raise ValueError(f"URI does not start with 'file:': {uri!r}")
    path = os.fsdecode(unquote_to_bytes(uri))
    path = path[5:]
    if path[:3] == '///':
        # Remove empty authority
        path = path[2:]
    elif path[:12] == '//localhost/':
        # Remove 'localhost' authority
        path = path[11:]
    if path[:3] == '///' or (path[:1] == '/' and path[2:3] in ':|'):
        # Remove slash before DOS device/UNC path
        path = path[1:]
        path = path[0].upper() + path[1:]
    if path[1:2] == '|':
        # Replace bar with colon in DOS drive
        path = path[:1] + ':' + path[2:]
    path_ = Path(path)
    if not path_.is_absolute():
        raise ValueError(f"URI is not absolute: {uri!r}.  Parsed so far: {path_!r}")
    return str(path_)


def escape_for_md(filename: str) -> str:
    """
    Escapes a filename for use in Markdown image directives.

    If the filename contains any whitespace characters, it wraps the filename
    in angle brackets and replaces any '<' and '>' characters with their
    URL-encoded equivalents (%3C and %3E, respectively).

    Args:
        filename: The filename to escape.

    Returns:
        The escaped filename suitable for Markdown.
    """
    if re.search(r"\s", filename):
        return "<{}>".format(filename.replace("<", r"%3C").replace(">", "%3E"))
    return filename


def escape_for_rst(filename: str) -> str:
    """
    Escape a filename for use in reStructuredText image/figure directives.

    - Returns unmodified filename if it contains only safe characters
    - Uses quotes if spaces or basic special characters are present
    - Uses URI escaping for characters that quotes can't handle safely

    Args:
        filename: The filename to escape

    Returns:
        Properly escaped filename for RST
    """
    # Pattern for "safe" filenames that need no escaping
    safe_pattern = r'^[a-zA-Z0-9_\-./]+$'

    # Pattern for filenames that can be handled with quotes
    quote_safe_pattern = r'^[a-zA-Z0-9_\-./\s!@%&()=+,;]+$'

    if re.match(safe_pattern, filename):
        return filename
    if re.match(quote_safe_pattern, filename):
        return f'"{filename}"'
    return uri_quote(filename)
