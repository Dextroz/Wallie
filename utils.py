try:
    import subprocess, click, os, requests
    from platform import system
    from colorama import Fore
except ImportError as err:
    print(f"Failed to import required modules: {err}")


def download_image(image_url, file_name):
    """Download the users specified image to the project directory.
    Returns:
        file_name string."""
    def write_file(file_name, resp, bar):
        """Write image file.
        Params:
            file_name: The file name.
            resp: Requests response object.
            bar: Either None (for no progress bar) or ProgressBar object."""
        try:
            with open(f"{file_name}.jpg", "wb") as f:
                for chunk in resp.iter_content(1024):
                    f.write(chunk)
                    if bar is None:
                        pass
                    else:
                        bar.update(1024)
        except IOError:
            click.secho(
                f"Failed to create {file_name}.jpg", fg="bright_yellow", err=True)
            exit()
    # Start of download_image()
    with requests.get(image_url, stream=True) as resp:
        if ((resp.status_code) == (requests.codes.ok)):
            # Check for content-length header or transfer-encoding
            # From: https://github.com/requests/requests/issues/4925
            is_chunked = resp.headers.get("transfer-encoding", "") == "chunked"
            content_length = resp.headers.get("content-length")
            if not is_chunked and content_length.isdigit():
                total_size = int(content_length)
                with click.progressbar(length=total_size, show_eta=True, show_percent=True, fill_char=">", label=f"Downloading {file_name}.jpg", bar_template=click.style("%(label)s  [%(bar)s]  %(info)s", fg="bright_yellow")) as bar:
                    # See write_file above.
                    write_file(file_name, resp, bar)
            else:
                # Fails to get content-length. No progress bar.
                write_file(file_name, resp, None)
        else:
            click.secho(f"{resp.raise_for_status()}", fg="bright_yellow")
            exit()
    click.secho("Download Complete!", fg="bright_yellow")
    return f"{file_name}.jpg"


def present_images(images):
    """Present image choices to the user and request choice.
    Returns:
        user_choice list."""
    for num, item in enumerate(images, 0):
        click.secho(
            f"""Image: {num} -- {item[0]["author_name"]}\nProfile: {item[0]["author_profile"]}\nImage Link: {item[0]["full_image"]}\n""", fg="bright_yellow")
    # Formats prompt all yellow coloured.
    user_choice = int(click.prompt(click.style(
        "Select your preferred image: ", fg="bright_yellow"), prompt_suffix=""))
    user_choice = images[user_choice]
    return user_choice


def check_os(abs_path):
    """Check the operating system and run the respective desktop setting command
    Returns:
        False: If command fails to set desktop wallpaper.
        True: if the command successfully sets the desktop wallpaper."""
    os_name = system()
    if os_name == "Darwin":
        try:
            SCRIPT = """osascript -e 'tell application "Finder" to set desktop picture to "{abs_path}" as POSIX file'"""
            subprocess.run(SCRIPT.format(abs_path=abs_path), shell=True)
            # return True if the command successfully executes.
            return True
        except subprocess.CalledProcessError as err:
            click.secho(
                f"Failed to set desktop wallpaper with the following error:\n{err}", fg="bright_yellow")
            # return False if the command fails.
            return False
    elif os_name == "Windows":
        try:
            ctypes.windll.user32.SystemParametersInfoW(20, 0, abs_path, 0)
            # return True if the command successfully executes.
            return True
        except RuntimeError as err:
            click.secho(
                f"Failed to set desktop wallpaper with the following error:\n{err}", fg="bright_yellow")
            # return False if the command fails.
            return False
    elif os_name == "Linux":
        command = get_linux_envrionment()
        if command is not None:
            try:
                subprocess.run(command.format(abs_path=abs_path), shell=True)
                # return True if the command successfully executes.
                return True
            except subprocess.CalledProcessError as err:
                click.secho(
                    f"Failed to set desktop wallpaper with the following error:\n{err}", fg="bright_yellow")
                # return False if the command fails.
                return False
        # If None: get_linux_envrionment() returns None when envrionment cannot be determined.
        else:
            click.secho(
                "Your Linux desktop envrionment is not supported.", fg="bright_yellow")
            # return False if the command fails.
            return False


def get_linux_envrionment():
    """Get the current linux desktop envrionment of the user
    Returns:
        command: The command to set the desktop environment.
    https://stackoverflow.com/questions/2035657/what-is-my-current-desktop-environment"""
    if os.environ.get("KDE_FULL_SESSION") == "true":
        command = """
                    qdbus org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript '
                        var allDesktops = desktops();
                        print (allDesktops);
                        for (i=0;i<allDesktops.length;i++) {{
                            d = allDesktops[i];
                            d.wallpaperPlugin = "org.kde.image";
                            d.currentConfigGroup = Array("Wallpaper",
                                                   "org.kde.image",
                                                   "General");
                            d.writeConfig("Image", "file:///{abs_path}")
                        }}
                    '
                """
    elif os.environ.get("DESKTOP_SESSION") == "gnome":
        command = "gsettings set org.gnome.desktop.background picture-uri file://{abs_path}"
    elif os.environ.get("DESKTOP_SESSION") == "Lubuntu":
        command = "pcmanfm -w {abs_path} --wallpaper-mode=fit"
    elif os.environ.get("DESKTOP_SESSION") == "mate":
        command = "gsettings set org.mate.background picture-filename {abs_path}"
    else:
        command = None
    return command
