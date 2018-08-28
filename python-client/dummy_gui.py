from tkinter import *
from PIL import ImageTk, Image
from urllib.request import urlopen
from io import BytesIO

root=Tk()
root.title("Nearer")
root.geometry("800x480") #x600") # for testing
#root.attributes('-fullscreen', True)
root.resizable(0, 0)

# make sure nothing gets too close (within 15px) to the edge
main_box = Frame(root)
main_box.grid(row=0, column=0, padx=15, pady=15)

def load_tk_image(path, max_width=None, max_height=None):
    if path.find("://") != -1:
        image_byt = urlopen(path).read()
        img = Image.open(BytesIO(image_byt))
    else:
        img = Image.open(path)
    old_width = img.width
    old_height = img.height
    wh_ratio = old_width / old_height

    assert (max_height or max_width)
    if max_width and max_height:
        desired_wh_ratio = max_width / max_height
        if desired_wh_ratio >= wh_ratio:
            max_height = None # picture is WIDE (so use max_width)
        else:
            max_width = None # picture is TALL (so use max_height)
    if max_width:
        width = max_width
        height = width / wh_ratio
    else:
        height = max_height
        width = height * wh_ratio

    height = int(old_height * max_width / old_width)
    img = img.resize((width, height))
    img = ImageTk.PhotoImage(img)
    return img
def all_children(wid) :
    _list = wid.winfo_children()

    for item in _list :
        if item.winfo_children() :
            _list.extend(item.winfo_children())

    return _list

thumbnail_img = load_tk_image("http://via.placeholder.com/200x150?text=?", max_width=300)

thumbnail = Label(main_box, image = thumbnail_img, anchor="e")
thumbnail.grid(row=0, rowspan=5, column=2, sticky=E)

Label(main_box, text="Title:", font="Helvetica 24 bold").grid(row=0, column=0, sticky=E)
Label(main_box, text="Progress:", font="Helvetica 24 bold").grid(row=1, column=0, sticky=E)
Label(main_box, text="Status:", font="Helvetica 24 bold").grid(row=2, column=0, sticky=E)
Label(main_box, text="Connection:", font="Helvetica 24 bold").grid(row=3, column=0, sticky=E)
#Label(main_box, text="Ping:", font="Helvetica 24 bold").grid(row=4, column=0, sticky=E)
Label(main_box).grid(row=5, pady=15)
Label(main_box, text="Controls:", font="Helvetica 24 bold").grid(row=6, column=0, sticky=E, pady=20)
Label(main_box, text="Volume:", font="Helvetica 24 bold").grid(row=7, column=0, sticky=E, pady=20)

title = Label(main_box, text="No Song Playing", font="Helvetica 24", width=20, anchor="w")
progress = Label(main_box, text="N/A of N/A", font="Helvetica 24")
status = Label(main_box, text="Unknown", font="Helvetica 24")
connection_frame = Frame(main_box)
connection_status = Label(connection_frame, text="☒", font="Helvetica 48", foreground="red") # ☑, green
reconnect_button = Button(connection_frame, text="↻ Reconnect", font="Helvetica 18")
ping_display = Label(main_box, text="Ping: ?", font="Helvetica 18")
controls_frame = Frame(main_box)
play_button = Button(controls_frame, text="Play", font="Helvetica 28", width=11)
skip_button = Button(controls_frame, text="Skip", font="Helvetica 28", width=11)
pause_button = Button(controls_frame, text="Pause", font="Helvetica 28", width=11)
volume_slider = Scale(main_box, from_=0, to=100, orient=HORIZONTAL)

title.grid(row=0, column=1, sticky=W)
progress.grid(row=1, column=1, sticky=W)
status.grid(row=2, column=1, sticky=W)

connection_frame.grid(row=3, column=1, sticky=W)
connection_status.grid(row=0, column=0)
reconnect_button.grid(row=0, column=1, padx=10)

ping_display.grid(row=4, column=1, sticky=W)

controls_frame.grid(row=6, column=1, columnspan=2, sticky=W)
play_button.grid(row=0, column=0, padx=2)
skip_button.grid(row=0, column=1, padx=2)
pause_button.grid(row=0, column=2, padx=2)

volume_slider.grid(row=7, column=1, columnspan=2, sticky=E+W)

root.configure(background="#eeeeee")
for widget in all_children(root):
    if isinstance(widget, Button):
        widget.configure(padx=10, pady=10, background="#aaaaff", activebackground="#ccccff")
        #widget.configure(foreground="white", background="black")
    else:
        widget.configure(background="#eeeeee")
# TODO set uniform background more cleanly

root.mainloop()
