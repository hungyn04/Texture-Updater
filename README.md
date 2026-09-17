# Texture-Updater

A Python script to easily add new textures to the old Minecraft PE (<0.15) texture atlas

## The problem

Prior to Minecraft PE Alpha 0.15, the game uses a texture atlas (that is, contain a whole bunch of texture stuffed into a single image) instead of separating each texture into individual file.

Because of that, texture replacement on these versions is a nightmare: you have the textures that you want to replace, then you have to manually drag it into the image editor, guess what the corresponding texture is, stich the texture together and risk ruining the entire thing if you don't have a backup.

Thankfully, the game comes with a `.meta` file that map all the texture names and their correspoding dimension in the texture atlas.

This script aims to utilize that to make this task a little less tedious by helping user find the target texture and replace it, along with some small but helpful features and safety stuff that make life extra easy.

## What can this do?

Let's see how the everything in structured first: inside `data/images/` of the game, there is the `terrain-atlas.tga` file, along with its smaller version used as mipmap. And then there is `terrain.meta` file which saves us time by let us know which texture is in this position, what its name is, and its dimension.

Now that you know, here are what this script provides:

- **Replacing textures**: The core feature, you can drag an image into the editor to replace the currently selected one, and there is bulk mode as well which we will talk about later.
- **Backup**: Automatically create a backup of the original texture so you don't have to worry about ruining the entire thing.
- **Creating mimaps**: Automatically create smaller version of the atlas (`mip[i]` suffix), so your texture will be properly rendered in the game.
- **Visual editor**: Allows you to easily navigate the program.
- **Saving work**: Let you save a config file that can be opened later and continue working.

## How to use it

1. Download or clone this repository:

```
git clone https://github.com/hungyn04/Texture-Updater.git
cd Texture-Updater
```

2. Create a virtual environment so not to clutter you Python installation, then install pillow and pygame-ce (or using `requirements.txt`):

```
python -m venv .venv
```

> Depending on your current OS, activate the venv using this guide:
> https://docs.python.org/3/library/venv.html#how-venvs-work

```
pip install -r requirements.txt
```

3. Once done, run the script:

```
python3 ./texture_updater.py
```

You'll be presented with a CLI that asks you for config file, if you've saved work before, just drag the `.conf` file into it or type the file path and press Enter.

You can also open `.conf` file by providing the file path as an argument when running the script:

```
python3 ./texture_updater.py ./example.conf
```

Otherwise, just press Enter to skip it. You will then be asked for `.meta` file, drag the file into it or type the file path and press Enter.
If nothing goes wrong, you will be asked for `.tga` texture atlas file (`.png` is also possible), drag the file into it or type the file path and press Enter.

Visual editor will popup, you can press F1 to show all the features/infomation and keyboard shortcut that you can use. Here are what you can do inside this visual editor:

### 1. Saving/Exporting:

- **_Save changes_**: You can manually close the window or press Ctrl + S to save the current workspace into `.conf` file which you can open later. Note that this does not do anything to the original texture.

  To close without saving, press Esc and the program will exit without creating `.conf` file.

- **_Export changes_**: Press Ctrl + E to export the modified texture atlas, which will first rename your original texture (`original` suffix), and then create a texture with the same name in place of your original file.

  Additionally, you can press Ctrl + Shift + E to create all of its mipmap variants (`mip[i]` suffix), note that this is will replace any existing mipmap-ed textures unlike the full texture, no backup will be created.

### 2. Editing:

> What will be shown in the main editor:
>
> **_Selector_**: Red rectangle that indicate the texture that's currently selected.
>
> **_Tooltip_**: Shown right under the selector, which gives you the name of the current texture for reference, and a preview of old texture right below to help you locating and comparing texture.
>
> **_The darkened texture atlas_**: Show what the original look like, as well as the possible position that you can edit, any newly added texture will sit in front of this layer.

- **_Adding a replacement texture_**: You can replace the selected texture by dragging the image file into the window. Any invalid file will show a red question mark.

  Alternatively, press Enter to use the file with the same name as the texture in the current source directory (shown on the bottom right corner after you press F1, default to the directory where the script is located).

  Note that selector will automatically move to the next position after adding, so you can replace all the textures sequentially without having to move the selector manually.

> You can change the source directory by dragging the folder/directory into the window.

- **_Bulk adding replacement textures_**: Just like before by dragging the directory into the window, but you can populate the directory with all the texture files and the corresponding name. Then press Ctrl + Enter to use all the files with the corresponding name.

- **_Deleting replacement textures_**: There are 3 ways to delete - you can press Delete to remove the current one as normal, or you can press Tab to remove and move the selector the the next position, or press Backspace to remove and move the selector to the previous position.

### 3. Navigating:

- **_Selecting texture_**: You can choose which texture to perform action by pressing arrow key (or WASD) to move the selector around.

- **_Changing view_**: You can drag your mouse around to move the view, you can also use scroll wheel (or + and - key) to zoom in/out.
  Alternatively, you can press Shift to toggle follow selector mode, which will lock the view with the selector position.

- **_Viewing additional info_**: As mentioned before, you can press F1 to show addition guides and info like view position, source directory, tile size, etc.

## License

[MIT](https://choosealicense.com/licenses/mit/)
