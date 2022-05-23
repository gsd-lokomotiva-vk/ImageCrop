import tkinter as tk
import tkinter.font as tkFont
from tkinter import filedialog
from PIL import ImageTk, Image
from tkinter import messagebox


class ImageCrop(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.grab_set()

        self.font = tkFont.Font(size=14)
        self.aspect_ratio = 1

        self.cropped_image_aspect_ratio = 7 / 6
        self.hover_crop_box_width = 30
        self.hover_crop_box_height = 35
        
        self.supported_save_filetypes = (".png", )
        self.supported_load_filetypes = (".png", ".jpg")

        # full image is displayed on canvas, it does not expand
        # as loaded image aspect ratio can be different than that of canvas'
        # image corners positions on canvas are necessary
        self.image_on_canvas_topleft_x_pos = 0
        self.image_on_canvas_topleft_y_pos = 0
        self.image_on_canvas_bottomright_x_pos = 0
        self.image_on_canvas_bottomright_y_pos = 0

        self.frame_image = tk.Frame(self, bd=0)
        self.frame_cropped = tk.Frame(self, bd=0)
        self.frame_buttons = tk.Frame(self, bd=0)

        self.image = None
        self.cropped_image = None
        self.resized_cropped_image = None
        self.canvas_full_image = None
        self.hover_crop_box = None  # visible box when hovering over the image

        self.to_save = False

        self.cursor_x_pos = 0
        self.cursor_y_pos = 0

        self.image_width = 0
        self.image_height = 0

        self.canvas_full = tk.Canvas(
            self.frame_image,
            width=590,
            height=450,
            bg="gray80"
        )

        self.canvas_cropped = tk.Canvas(
            self.frame_cropped,
            width=210,
            height=245,
            bg="yellow"
        )

        self.btn_load_image = tk.Button(
            self.frame_buttons,
            text="Load",
            font=self.font,
            command=lambda: self.load_image()
        )

        self.btn_save_cropped = tk.Button(
            self.frame_buttons,
            text="Save",
            bg="grey",
            font=self.font,
            state="disabled",
            command=lambda: self.save_copped()
        )

        self.btn_rotate_right_90 = tk.Button(
            self.frame_buttons,
            text=u"\u27F3",
            font=self.font,
            command=lambda rotation=-90: self.rotate_image(rotation)
        )

        self.btn_rotate_left_90 = tk.Button(
            self.frame_buttons,
            text=u"\u27F2",
            font=self.font,
            command=lambda rotation=90: self.rotate_image(rotation)
        )

        self.frame_buttons.rowconfigure(0, weight=1, uniform="buttons")
        self.frame_buttons.rowconfigure(1, weight=1, uniform="buttons")
        self.frame_buttons.rowconfigure(2, weight=1, uniform="buttons")
        self.frame_buttons.rowconfigure(3, weight=1, uniform="buttons")
        self.frame_buttons.rowconfigure(4, weight=1, uniform="buttons")
        self.frame_buttons.rowconfigure(5, weight=1, uniform="buttons")

        self.frame_buttons.columnconfigure(0, weight=1, uniform="columns")
        self.frame_buttons.columnconfigure(1, weight=5, uniform="columns")
        self.frame_buttons.columnconfigure(2, weight=5, uniform="columns")
        self.frame_buttons.columnconfigure(3, weight=1, uniform="columns")

        self.frame_image.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.frame_cropped.grid(row=0, column=1, sticky="nsew")
        self.frame_buttons.grid(row=1, column=1, sticky="nsew")

        self.btn_rotate_right_90.grid(row=4, column=2, sticky="nsew")
        self.btn_rotate_left_90.grid(row=4, column=1, sticky="nsew")
        self.btn_load_image.grid(row=2, column=1, columnspan=2, sticky="nsew")
        self.btn_save_cropped.grid(row=0, column=1, columnspan=2, sticky="nsew")

        self.canvas_cropped.pack(expand=True, fill="both")
        self.canvas_full.pack(expand=True, fill="both")

        self.columnconfigure(0, weight=3, uniform="columns")
        self.columnconfigure(1, weight=1, uniform="columns")

        self.rowconfigure(0, weight=7, uniform="rows")
        self.rowconfigure(1, weight=6, uniform="rows")

        self.grid_propagate(False)

        self.frame_image.pack_propagate(False)
        self.frame_cropped.pack_propagate(False)
        self.frame_buttons.grid_propagate(False)

    def adjust_hover_box_size(self, event):
        if event.delta > 0 or event.num == 4:  # windows or linux
            if self.check_hover_box_within_image_borders(self.cursor_x_pos, self.cursor_y_pos):
                self.increase_hover_box_size(1)
        elif event.delta < 0 or event.num == 5:
            if (self.check_hover_box_within_image_borders(self.cursor_x_pos, self.cursor_y_pos) 
                    and self.hover_crop_box_width > 30):
                self.decrease_hover_box_size(1)
        self.cursor_on_image_coordinates()

    def decrease_hover_box_size(self, decrease: int):
        self.hover_crop_box_width -= decrease
        self.hover_crop_box_height = self.hover_crop_box_width * self.cropped_image_aspect_ratio

    def increase_hover_box_size(self, increase: int):
        self.hover_crop_box_width += increase
        self.hover_crop_box_height = self.hover_crop_box_width * self.cropped_image_aspect_ratio

    def check_hover_box_within_image_borders(self, x, y):
        return (self.check_hover_box_width_within_image_borders(x)
                and self.check_hover_box_height_within_image_borders(y))

    def check_hover_box_width_within_image_borders(self, cursor_x_pos):
        if (cursor_x_pos + self.hover_crop_box_width < self.image_on_canvas_bottomright_x_pos
                and cursor_x_pos - self.hover_crop_box_width > self.image_on_canvas_topleft_x_pos):
            return True
        return False

    def check_hover_box_height_within_image_borders(self, cursor_y_pos):
        if (cursor_y_pos + self.hover_crop_box_height < self.image_on_canvas_bottomright_y_pos
                and cursor_y_pos - self.hover_crop_box_height > self.image_on_canvas_topleft_y_pos):
            return True
        return False

    def redraw_hover_box(self):
        self.canvas_full.delete(self.hover_crop_box)

        rectangle_topleft = self.cursor_x_pos - self.hover_crop_box_width
        rectangle_bottomleft = self.cursor_y_pos - self.hover_crop_box_height
        rectangle_topright = self.cursor_x_pos + self.hover_crop_box_width
        rectangle_bottomright = self.cursor_y_pos + self.hover_crop_box_height

        self.hover_crop_box = self.canvas_full.create_rectangle(rectangle_topleft, rectangle_bottomleft, 
                                                           rectangle_topright, rectangle_bottomright)

        crop_box = (int((rectangle_topleft - self.image_on_canvas_topleft_x_pos) / self.aspect_ratio),
                    int((rectangle_bottomleft - self.image_on_canvas_topleft_y_pos) / self.aspect_ratio),
                    int((rectangle_topright - self.image_on_canvas_topleft_x_pos) / self.aspect_ratio),
                    int((rectangle_bottomright - self.image_on_canvas_topleft_y_pos) / self.aspect_ratio))

        cropped_width = self.canvas_cropped.winfo_width()
        cropped_height = self.canvas_cropped.winfo_height()

        self.cropped_image = self.image.crop(crop_box)

        self.resized_cropped_image = self.cropped_image.resize((cropped_width, cropped_height), Image.ANTIALIAS)
        self.resized_cropped_image = ImageTk.PhotoImage(self.resized_cropped_image)

        self.canvas_cropped.create_image(0, 0, image=self.resized_cropped_image, anchor="nw")

    def cursor_on_image_coordinates(self, event=None):
        if event:
            if self.check_hover_box_width_within_image_borders(event.x):
                self.cursor_x_pos = event.x
            if self.check_hover_box_height_within_image_borders(event.y):
                self.cursor_y_pos = event.y

        self.redraw_hover_box()

    def save_copped(self):
        if self.cropped_image is not None:
            file = filedialog.asksaveasfilename(title="Choose save location", 
                                                filetypes=[('Image', self.supported_save_filetypes)])
            if file:
                if file[:-4] not in self.supported_save_filetypes:
                    file += ".png"
                self.cropped_image.save(file)

    def rotate_image(self, rotation: int):
        self.image = self.image.rotate(angle=rotation, expand=True)
        image_x0, image_y0, self.image_width, self.image_height = self.image.getbbox()
        self.adjust_image_in_canvas_full()

    def disable_cropped_canvas_refresh(self):
        self.canvas_full.unbind('<Motion>')
        self.canvas_full.unbind('<Enter>')

    def enable_cropped_canvas_refresh(self):
        self.canvas_full.bind('<Motion>', self.cursor_on_image_coordinates)
        self.canvas_full.bind('<Enter>', self.cursor_on_image_coordinates)

    def enable_save_btn(self):
        self.btn_save_cropped["state"] = "active"
        self.btn_save_cropped["bg"] = "green"
        self.btn_save_cropped.update()

    def disable_save_btn(self):
        self.btn_save_cropped["bg"] = "grey"
        self.btn_save_cropped["state"] = "disabled"
        self.btn_save_cropped.update()

    def left_click_on_image(self, event):
        self.to_save = not self.to_save
        if self.to_save:
            self.disable_cropped_canvas_refresh()
            self.enable_save_btn()
        else:
            self.enable_cropped_canvas_refresh()
            self.disable_save_btn()

    def load_image(self):
        file = filedialog.askopenfilename(title="Choose image", filetypes=[('Image', self.supported_load_filetypes)])
        if file:
            self.image = Image.open(file).convert('RGBA')

            image_topleft_x_pos, image_topleft_y_pos, self.image_width, self.image_height = self.image.getbbox()

            self.adjust_image_in_canvas_full()
            self.bind_events_to_canvas_full()

    def bind_events_to_canvas_full(self):
        self.canvas_full.bind('<Motion>', self.cursor_on_image_coordinates)
        self.canvas_full.bind('<Button-1>', self.left_click_on_image)
        self.canvas_full.bind('<Enter>', self.cursor_on_image_coordinates)
        self.canvas_full.bind('<MouseWheel>', self.adjust_hover_box_size)
        self.canvas_full.bind('<Button-4>', self.adjust_hover_box_size)
        self.canvas_full.bind('<Button-5>', self.adjust_hover_box_size)
        self.bind("<Configure>", self.adjust_image_in_canvas_full)

    def get_aspect_ratio_canvas_full(self):
        return self.canvas_full.winfo_width() / self.canvas_full.winfo_height()

    def refresh_aspect_ratio(self):
        canvas_width = self.canvas_full.winfo_width()
        canvas_height = self.canvas_full.winfo_height()

        canvas_full_aspect_ratio = canvas_width / canvas_height
        image_aspect_ratio = self.image_width / self.image_height

        if canvas_full_aspect_ratio < image_aspect_ratio:
            if canvas_width < self.image_width:
                self.aspect_ratio = canvas_width / self.image_width
            else:
                self.aspect_ratio = self.image_width / canvas_width
        else:
            if canvas_height < self.image_height:
                self.aspect_ratio = canvas_height / self.image_height
            else:
                self.aspect_ratio = self.image_height / canvas_height

    def get_image_in_canvas_full_width(self):
        return int(self.image_width * self.aspect_ratio)

    def get_image_in_canvas_full_height(self):
        return int(self.image_height * self.aspect_ratio)

    def get_image_on_canvas_topleft_x_pos(self):
        return int((self.canvas_full.winfo_width() - self.get_image_in_canvas_full_width()) / 2)

    def get_image_on_canvas_topleft_y_pos(self):
        return int((self.canvas_full.winfo_height() - self.get_image_in_canvas_full_height()) / 2)

    def get_image_on_canvas_bottomright_x_pos(self):
        return self.canvas_full.winfo_width() - self.get_image_on_canvas_topleft_x_pos()

    def get_image_on_canvas_bottomright_y_pos(self):
        return self.canvas_full.winfo_height() - self.get_image_on_canvas_topleft_y_pos()

    def refresh_image_in_canvas_full_corners(self):
        self.image_on_canvas_topleft_x_pos = self.get_image_on_canvas_topleft_x_pos()
        self.image_on_canvas_topleft_y_pos = self.get_image_on_canvas_topleft_y_pos()

        self.image_on_canvas_bottomright_x_pos = self.get_image_on_canvas_bottomright_x_pos()
        self.image_on_canvas_bottomright_y_pos = self.get_image_on_canvas_bottomright_y_pos()

    def adjust_image_in_canvas_full(self, event=None):
        self.refresh_aspect_ratio()
        self.refresh_image_in_canvas_full_corners()

        image_in_canvas_full_width = int(self.image_width * self.aspect_ratio)
        image_in_canvas_full_height = int(self.image_height * self.aspect_ratio)

        self.canvas_full_image = self.image.resize((image_in_canvas_full_width, image_in_canvas_full_height),
                                                   Image.ANTIALIAS)
        self.canvas_full_image = ImageTk.PhotoImage(self.canvas_full_image)

        self.canvas_full.create_image(self.image_on_canvas_topleft_x_pos, self.image_on_canvas_topleft_y_pos,
                                      image=self.canvas_full_image, anchor="nw")
