"""Python file used to define UI objects. Each object has an update, check_event and size_update function."""

import time
from os import path
from queue import Empty, Queue
from threading import Thread

import pygame as pg

import GIFLoader
import VideoLoader
from Constants import *


class Button:
    """A general button object."""

    def __init__(self, rect, colour, on_click, **kwargs):
        self.rect_func = rect
        self.rect = pg.Rect(rect())
        self.colour = colour
        self.func_on_click = on_click
        self.clicked = False
        self.hovered = False
        self.hover_text = None
        self.clicked_text = None
        self.text = None
        self.scroll = (0, 0)
        self.process_kwargs(kwargs)
        self.render_text()

    def process_kwargs(self, kwargs):
        """Processes keyword arguments such as button styles."""

        settings = {"text": None,
                    "font": pg.font.Font(None, 16),
                    "call_on_release": True,
                    "hover_colour": None,
                    "clicked_colour": None,
                    "font_colour": pg.Color("white"),
                    "hover_font_colour": None,
                    "clicked_font_colour": None}
        for kwarg in kwargs:
            if kwarg in settings:
                settings[kwarg] = kwargs[kwarg]
            else:
                raise AttributeError("Button has no keyword: {}".format(kwarg))
        self.__dict__.update(settings)

    def render_text(self):
        """Renders the button text."""

        if self.text:
            if self.hover_font_colour:
                colour = self.hover_font_colour
                self.hover_text = self.font.render(self.text, True, colour)
            if self.clicked_font_colour:
                colour = self.clicked_font_colour
                self.clicked_text = self.font.render(self.text, True, colour)
            self.text = self.font.render(self.text, True, self.font_colour)

    def check_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            self.on_click(event)
        elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
            self.on_release()
        elif event.type == pg.MOUSEMOTION:
            self.check_hover()
        elif event.type == pg.VIDEORESIZE:
            self.rect = pg.Rect(self.rect_func())

    def size_update(self, surface):
        self.rect = pg.Rect(self.rect_func())
        self.update(surface)

    def on_click(self, event):
        """Called when a mouse button is clicked."""

        if self.rect.collidepoint(*map(sum, zip(event.pos, self.scroll))):
            self.clicked = True
            if not self.call_on_release:
                self.func_on_click()

    def on_release(self):
        """Called when a mouse button is un-clicked."""

        if self.clicked and self.call_on_release:
            self.func_on_click()
        self.clicked = False

    def check_hover(self):
        """Checks if the button has been hovered over."""

        if self.rect.collidepoint(*map(sum, zip(pg.mouse.get_pos(), self.scroll))):
            if not self.hovered:
                self.hovered = True
        else:
            self.hovered = False

    def update(self, surface):
        colour = self.colour
        text = self.text
        inflate = -4
        if self.clicked and self.clicked_colour:
            colour = self.clicked_colour
            inflate = -6
            if self.clicked_font_colour:
                text = self.clicked_text
        elif self.hovered and self.hover_colour:
            colour = self.hover_colour
            if self.hover_font_colour:
                text = self.hover_text
        pg.draw.rect(surface, (30, 39, 46), self.rect, border_radius=2)
        pg.draw.rect(surface, colour, self.rect.inflate(inflate, inflate), border_radius=2)
        if self.text:
            text_rect = text.get_rect(center=self.rect.center)
            surface.blit(text, text_rect)

    def update_scroll(self, scroll):
        """Updates scroll to ensure mouse collision is updated."""

        self.scroll = scroll


class ContextButton(Button):
    """Button that shows context of what it does."""

    def __init__(self, rect, colour, on_click, help_func, **kwargs):
        super(ContextButton, self).__init__(rect, colour, on_click, **kwargs)
        self.help_func = help_func
        self.sent = False

    def update(self, surface):
        super(ContextButton, self).update(surface)
        if self.hovered and not self.sent:
            self.help_func(True)
            self.sent = True
        elif not self.hovered and self.sent:
            self.sent = False
            self.help_func(False)


class ArgumentCallerButton(Button):
    """A special button used to load from previous games. It calls functions with arguments."""

    def __init__(self, rect, colour, on_click, pointer, *args, **kwargs):
        super(ArgumentCallerButton, self).__init__(lambda: (0, 0, 0, 0), colour, lambda: (), **kwargs)
        self.rect = pg.Rect(rect(pointer))
        self.on_click_func = on_click
        self.rect_func = rect
        self.pointer = pointer
        self.args = args

    def size_update(self, surface):
        self.rect = pg.Rect(self.rect_func(self.pointer))
        self.update(surface)

    def check_event(self, event):
        if event.type == pg.VIDEORESIZE:
            self.rect = pg.Rect(self.rect_func(self.pointer))
        else:
            super(ArgumentCallerButton, self).check_event(event)

    def on_release(self):
        if self.clicked and self.call_on_release:
            self.on_click_func(*self.args)
            self.clicked = False


class SavedBoardButton(Button):
    """A special button used to deal with the previous board."""

    def __init__(self, rect, colour, inactive_colour, oth_board, gui_board, forward, pointer, **kwargs):
        super(SavedBoardButton, self).__init__(lambda: (0, 0, 0, 0), colour, lambda: (), **kwargs)
        self.rect = pg.Rect(rect(pointer))
        self.rect_func = rect
        self.oth_board = oth_board
        self.gui_board = gui_board
        self.forward = forward
        self.inactive_colour = inactive_colour
        self.pointer = pointer
        self.active = False
        self.check_if_can_move()

    def check_if_can_move(self):
        """Check if a board can be moved forwards."""

        if self.forward:
            self.active = not self.oth_board.max_line <= self.oth_board.current_line
        else:
            self.active = self.oth_board.current_line > 0

    def update(self, surface):
        self.check_if_can_move()
        colour = self.colour
        text = self.text
        inflate = -4
        if not self.active:
            colour = self.inactive_colour
        else:
            if self.clicked and self.clicked_colour:
                colour = self.clicked_colour
                inflate = -6
                if self.clicked_font_colour:
                    text = self.clicked_text
            elif self.hovered and self.hover_colour:
                colour = self.hover_colour
                if self.hover_font_colour:
                    text = self.hover_text
        pg.draw.rect(surface, (30, 39, 46), self.rect, border_radius=2)
        pg.draw.rect(surface, colour, self.rect.inflate(inflate, inflate), border_radius=2)
        if self.text:
            text_rect = text.get_rect(center=self.rect.center)
            surface.blit(text, text_rect)

    def on_click(self, event):
        if self.active:
            super(SavedBoardButton, self).on_click(event)

    def on_release(self):
        if self.clicked and self.active and self.call_on_release:
            if self.forward:
                self.gui_board.update_static(self.oth_board.line_load_forwards()[1])
            else:
                self.gui_board.update_static(self.oth_board.line_load_backwards()[1])
            self.clicked = False

    def check_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            self.on_click(event)
        elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
            self.on_release()
        elif event.type == pg.MOUSEMOTION:
            self.check_hover()
        elif event.type == pg.VIDEORESIZE:
            self.rect = pg.Rect(self.rect_func(self.pointer))

    def size_update(self, surface):
        self.rect = pg.Rect(self.rect_func(self.pointer))
        self.update(surface)


class Paragraph:
    """Used to make text that correct fits in a certain bounding box."""

    def __init__(self, text, pos, font, func_size, colour=(0, 0, 0), centered=False):   # TODO Do something if it cannot render
        self.text = text
        self.pos_func = pos
        self.pos = pos()
        self.font = font
        self.func_size = func_size
        self.paragraph_size = func_size()
        self.colour = colour
        self.centered = centered

    def update(self, surface):
        words = [word.split(' ') for word in self.text.splitlines()]  # 2D array where each row is a list of words.
        space = self.font.size(' ')[0]  # The width of a space.
        max_width, max_height = self.paragraph_size
        intermediate = None
        x, y = self.pos
        word_height = 0
        for line in words:
            if self.centered:
                intermediate = pg.surface.Surface(self.paragraph_size)
                intermediate.fill((255, 255, 255))
                intermediate.set_colorkey((255, 255, 255))

            for word in line:
                word_surface = self.font.render(word, 0, self.colour)
                word_width, word_height = word_surface.get_size()
                if x + word_width >= max_width:
                    if self.centered:
                        surface.blit(intermediate, ((max_width - x) / 2, y))
                        intermediate = pg.surface.Surface(self.paragraph_size)
                        intermediate.fill((255, 255, 255))
                        intermediate.set_colorkey((255, 255, 255))
                    x = self.pos[0]  # Reset the x.
                    y += word_height  # Start on new row.
                if self.centered:
                    intermediate.blit(word_surface, (x, 0))
                else:
                    surface.blit(word_surface, (x, y))
                x += word_width + space
            if self.centered:
                surface.blit(intermediate, ((max_width - x)/2, y))
            x = self.pos[0]  # Reset the x.
            y += word_height  # Start on new row.
        return y

    def size_update(self, surface):
        self.paragraph_size = self.func_size()
        self.pos = self.pos_func()
        return self.update(surface)


class Image:
    """Object to load image."""

    def __init__(self, image_loc, func_size, minimum=1):
        self.func_size = func_size
        self.size = self.func_size()
        self.src_image = pg.image.load(image_loc)
        self.minimum = minimum
        self.scaled_image = keep_aspect_ratio(self.src_image, *self.size)

    def update(self, surface, move_pos):
        rect = self.scaled_image.get_rect()
        surface.blit(self.scaled_image, rect.move(move_pos[0] - rect.width / 2, move_pos[1]))
        return rect.bottom + move_pos[1]

    def size_update(self, surface, move_pos):
        self.size = self.func_size()
        self.scaled_image = keep_aspect_ratio(self.src_image, *self.size)
        return self.update(surface, move_pos)


class Board:
    """Object that deals with Othello grid, this is static."""

    def __init__(self, rect, size, colour, line_colour):
        self.rect_func = rect
        self.rect = pg.Rect(0, 0, 0, 0)
        self.rect.size = (self.rect_func()[2], self.rect_func()[2])
        self.rect.center = self.rect_func()[0:2]
        self.size = size
        self.colour = colour
        self.line_colour = line_colour

    def update(self, surface):
        self.draw_board(surface)
        return self.rect

    def draw_board(self, surface):
        """Draws the board."""

        step = self.rect.height // self.size
        self.rect.height = self.size * step
        self.rect.width = self.rect.height
        pg.draw.rect(surface, self.colour, self.rect)
        for x, y in zip(range(self.rect.x, self.rect.right + step, step),
                        range(self.rect.y, self.rect.bottom + step, step)):
            if x == self.rect.x or x == self.rect.right:
                thickness = 3
            else:
                thickness = 1
            pg.draw.line(surface, self.line_colour, (x, self.rect.y), (x, self.rect.y + self.rect.height), thickness)
            pg.draw.line(surface, self.line_colour, (self.rect.x, y), (self.rect.x + self.rect.height, y), thickness)

    def pos_click(self, position):
        """Change board position to GUI position."""

        step = self.rect.height // self.size
        position = ((position[0] + 0.52) * step, (position[1] + 0.52) * step)
        position = (position[0] + self.rect.x, position[1] + self.rect.y)
        return position, step

    def check_event(self, event):
        pass

    def size_update(self, surface):
        self.rect.size = (self.rect_func()[2], self.rect_func()[2])
        self.rect.center = self.rect_func()[0:2]
        return self.update(surface)

    def place_pieces(self, board, surface):
        """Place pieces depending on board."""

        for x in range(self.size):
            for y in range(self.size):
                if board[y][x] == "E":
                    continue

                position = self.pos_click((x, y))

                if board[y][x] == "B":
                    pg.draw.circle(surface, DBLACK, position[0], position[1] / 2)
                elif board[y][x] == "W":
                    pg.draw.circle(surface, LGREY, position[0], position[1] / 2)

                pg.draw.circle(surface, (0, 0, 0), position[0], position[1] / 2, 1)


class OthelloLogicBoard(Board):
    """Creates a dynamic grid that interfaces with the board logic."""

    def __init__(self, rect, size, colour, line_colour, gui_to_oth):
        super().__init__(rect, size, colour, line_colour)
        self.board = pg.surface.Surface(self.rect.size)
        self.board.set_colorkey(DRED)
        self.board_rect = self.rect.copy()
        self.rect.x = 0
        self.rect.y = 0
        self.gui_to_oth = gui_to_oth
        self._Print, self._Colour, self._Possible = (False, [["E" for x in range(BOARD_SIZE)] for y in range(BOARD_SIZE)]), (False, None), (False, {})

    def update(self, surface, size_changed=False):
        if (self._Possible[0] and self._Colour[0] and self._Print[0]) or size_changed:
            self.board.fill(DRED)
            self.draw_board(self.board)
            self.place_pieces(self._Print[1], self.board)
            self.place_pos_pieces(self._Possible[1], self.board)
            self._Print, self._Colour, self._Possible = (False, self._Print[1]), (False, self._Colour[1]), (
                False, self._Possible[1])
            surface.blit(self.board, (self.board_rect.x, self.board_rect.y))
        else:
            surface.blit(self.board, (self.board_rect.x, self.board_rect.y))
        return self.rect

    def size_update(self, surface):
        self.board_rect.size = (self.rect_func()[2], self.rect_func()[2])
        self.rect.size = (self.rect_func()[2], self.rect_func()[2])
        self.board_rect.center = self.rect_func()[0:2]
        self.board = pg.surface.Surface(self.rect.size)
        self.board.set_colorkey(DRED)
        return self.update(surface, True)

    def click_pos(self, position):
        """Change GUI position to specific board position."""

        position = (position[0] - self.board_rect.x, position[1] - self.board_rect.y)
        step = self.rect.height // self.size
        if 0 < position[0] < self.rect.width and 0 < position[1] < self.rect.height:
            position = (position[0] // step, position[1] // step)
        return position

    def check_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN or event.type == pg.MOUSEMOTION:
            position = pg.mouse.get_pos()
            if self.board_rect.collidepoint(*position):
                if event.type == pg.MOUSEMOTION:
                    pass  # Highlight selected?
                elif event.type == pg.MOUSEBUTTONDOWN:
                    self.gui_to_oth.put((LOCAL_IO["Click"], self.click_pos(position)))

    def place_pos_pieces(self, pos, surface):
        """Place possible pieces."""

        for (x, y) in pos.keys():
            position = self.pos_click((x, y))
            pg.draw.circle(surface, (0, 0, 0), position[0], position[1] / 2, 1)

    def queue_get(self, item):
        """Get the information from board logic."""

        if item[0] == LOCAL_IO["Print"]:
            self._Print = (True, item[1])
        elif item[0] == LOCAL_IO["Possible"]:
            self._Possible = (True, item[1])
        elif item[0] == LOCAL_IO["Colour"]:
            self._Colour = (True, item[1])


class SavedGamesBoard(Board):
    """Board that deals with previous games."""

    def __init__(self, rect, size, colour, line_colour, static, pointer):
        super().__init__(lambda: (0, 0, 0), size, colour, line_colour)
        self.static = static
        self.pointer = pointer
        self.rect_func = rect
        self.rect = pg.Rect(0, 0, 0, 0)
        self.changed_static = True
        self.rect.size = (self.rect_func(self.pointer)[2], self.rect_func(self.pointer)[2])
        self.rect.center = self.rect_func(self.pointer)[0:2]

    def update(self, surface):
        if self.changed_static:
            self.changed_static = False
            self.draw_board(surface)
            self.place_pieces(self.static, surface)
        return self.rect

    def size_update(self, surface):
        self.rect.size = (self.rect_func(self.pointer)[2], self.rect_func(self.pointer)[2])
        self.rect.center = self.rect_func(self.pointer)[0:2]
        self.changed_static = True
        self.update(surface)

    def update_static(self, new_static):
        """Update static board."""
        self.static = new_static
        self.changed_static = True


class PieceCount:
    """Makes the piece count above boards."""

    def __init__(self, func_pos, func_count, font, colour):
        self.font = font
        self.func_pos = func_pos
        self.pos = func_pos()
        self.colour = colour
        self.playing = False
        self.word_surface = self.font.render("0", 0, (0, 0, 0))
        self.word_width, self.word_height = self.word_surface.get_size()
        self.func_count = func_count
        self.count = func_count()

    def update(self, surface):
        if self.colour == "B":
            pg.draw.circle(surface, DBLACK, self.count[1], self.count[0])
        else:
            pg.draw.circle(surface, WHITE, self.count[1], self.count[0])
        pg.draw.circle(surface, (0, 0, 0) * (not self.playing) + YELLOW * self.playing, self.count[1],
                       self.count[0], 2 * self.playing + (not self.playing))
        surface.blit(self.word_surface, (self.pos[0] - self.word_width / 2, self.pos[1] - self.word_height / 2))

    def size_update(self, surface):
        self.count = self.func_count()
        self.pos = self.func_pos()
        self.update(surface)

    def queue_get(self, item):
        """Get the count and colour from the board logic."""

        if item[0] == LOCAL_IO["Count"]:
            self.word_surface = self.font.render(str(item[1][self.colour]), 0, (0, 0, 0))
            self.word_width, self.word_height = self.word_surface.get_size()
        elif item[0] == LOCAL_IO["Colour"]:
            self.playing = item[1] == self.colour


class GIFImage:
    """Used to load GIF images."""

    def __init__(self, func, filename, duration):
        self.pos_func = func
        self.pos = func()
        self.src_frames = []
        self.scaled_frames = []
        self.filename = filename
        self.duration = duration
        self.length = len(duration)
        self.get_frames()

        self.current = 0
        self.ptime = time.time()

        self.running = True
        self.breakpoint = self.length - 1
        self.start_point = 0

    def get_frames(self):
        """Get the frames from images in directory."""

        for x in range(self.length):
            image = pg.image.load(path.join(self.filename, str(x) + ".png"))
            scaled_image = keep_aspect_ratio(image, *self.pos[2:])
            self.src_frames.append(image)
            self.scaled_frames.append((scaled_image, self.duration[x]))

    def scale_frames(self):
        """Scales the image correctly."""

        self.scaled_frames = []
        for x in range(self.length):
            scaled_image = keep_aspect_ratio(self.src_frames[x], *self.pos[2:])
            self.scaled_frames.append((scaled_image, self.duration[x]))

    def update(self, screen):
        if self.running and time.time() - self.ptime > self.scaled_frames[self.current][1] * 0.001:
            self.current += 1
            if self.current > self.breakpoint:
                self.current = self.start_point
            self.ptime = time.time()
            screen.blit(self.scaled_frames[self.current][0], self.pos[0:2])

    def size_update(self):
        self.pos = self.pos_func()
        self.scale_frames()

    def seek(self, num):
        """Seeks to a certain image."""

        self.current = num
        if self.current < 0:
            self.current = 0
        if self.current >= self.duration:
            self.current = self.duration - 1

    def set_bounds(self, start, end):
        """Sets the start and end point to play loops."""

        if start < 0:
            start = 0
        if start >= self.duration:
            start = self.duration - 1
        if end < 0:
            end = 0
        if end >= self.duration:
            end = self.duration - 1
        if end < start:
            end = start
        self.start_point = start
        self.breakpoint = end

    def pause(self):
        """Pause the GIF."""
        self.running = False

    def play(self):
        """Play the GIF."""
        self.running = True


class ThreadedGIFImage(GIFImage):
    """A GIF image loader that runs in a thread."""

    def __init__(self, func, filename, duration):
        self.queue = Queue()
        self.image_reader = Thread(target=GIFLoader.get_frames,
                                   args=(len(duration), filename, func(), duration, self.queue), daemon=True)
        self.image_reader.start()
        self.done_frames = 0
        super(ThreadedGIFImage, self).__init__(func, filename, duration)

    def get_frames(self):
        pass

    def update(self, screen):
        while self.done_frames < self.length:
            try:
                get = self.queue.get(False)
            except Empty:
                break
            else:
                if get[0] == LOCAL_IO["Loaded"]:
                    self.src_frames.append(get[1])
                    self.scaled_frames.append(get[2:4])
                    self.done_frames += 1

        if self.current + 1 < self.done_frames and self.running and time.time() - self.ptime > \
                self.scaled_frames[self.current][1] * 0.001:
            self.current += 1
            if self.current >= self.breakpoint:
                self.current = self.start_point
            self.ptime = time.time()
        if self.current + 1 < self.done_frames:
            screen.blit(self.scaled_frames[self.current][0], self.pos[0:2])

    def scale_frames(self):
        """Tells thread to scale frames."""

        if self.done_frames < self.length:
            self.done_frames = self.length
            self.src_frames = []
            self.scaled_frames = []
            super(ThreadedGIFImage, self).get_frames()
        else:
            super(ThreadedGIFImage, self).scale_frames()


class Video:
    """Threaded video loader."""

    def __init__(self, func, filename, time_per_frame, aspect=0, max_look=20):
        self.ptime = time.time()
        self.running = True
        self.aspect = aspect
        self.queue = Queue()
        self.filename = filename
        self.time_per_frame = time_per_frame
        self.max_look = max_look
        self.max_queue = Queue(max_look)
        self.size = func()
        self.func_size = func
        self.get = None
        self.video_reader = Thread(target=VideoLoader.get_video,
                                   args=(self.filename, self.size[2:4], self.queue, self.max_queue, self.aspect))
        self.video_reader.start()

    def update(self, screen):
        if self.running and time.time() - self.ptime > self.time_per_frame:
            try:
                self.get = self.max_queue.get(False)
            except Empty:
                if self.get:
                    screen.blit(self.get[1], self.size[0:2])
            else:
                self.ptime = time.time()
                screen.blit(self.get[1], self.size[0:2])
        elif self.get:
            screen.blit(self.get[1], self.size[0:2])

    def size_update(self):
        self.queue.put((LOCAL_IO["Stop"], None))
        self.max_queue.maxsize = 0
        self.video_reader.join(0.5)
        self.max_queue.maxsize = 1
        self.size = self.func_size()
        self.max_queue = Queue(self.max_look)
        self.queue = Queue()
        self.video_reader = Thread(target=VideoLoader.get_video,
                                   args=(self.filename, self.size[2:4], self.queue, self.max_queue, self.aspect), daemon=True)
        self.video_reader.start()

    def pause(self):
        """Pause video."""

        self.running = False

    def play(self):
        """Play video."""

        self.running = True

    def on_exit(self):
        """Tries to close thread when exiting program or no longer using the video."""

        self.queue.put((LOCAL_IO["Stop"], None))
        self.max_queue.maxsize = 0
        self.video_reader.join(0.5)
        self.max_queue.maxsize = 1


def sub_rect(r1, r2):
    """Gets two pygame rects and removes the area of r2 from r1."""

    if not r1.colliderect(r2):  # Check if collides
        return [r1]
    clip = r2.clip(r1)

    ret = []

    if clip.left > r1.left:
        ret.append(pg.Rect(r1.left, r1.top, clip.left - r1.left, r1.bottom - r1.top))  # Create new left rect
    if clip.right > r1.right:
        ret.append(pg.Rect(clip.right, r1.top, r1.right - clip.right, r1.bottom - r1.top))  # Right
    if clip.top > r1.top:
        ret.append(pg.Rect(r1.left, r1.top, r1.width, clip.top - r1.top))  # Top
    if clip.bottom > r1.bottom:
        ret.append(pg.Rect(r1.left, clip.bottom, r1.width, r1.bottom - clip.bottom))  # Bottom

    return ret


def keep_aspect_ratio(img, bx, by):
    """Scales image to fit into bx/by, this method will retain the original image's aspect ratio."""

    ix, iy = img.get_size()
    if ix > iy:  # fit to width

        scale_factor = bx / float(ix)
        sy = scale_factor * iy
        if sy > by:
            scale_factor = by / float(iy)
            sx = scale_factor * ix
            sy = by
        else:
            sx = bx
    else:  # fit to height

        scale_factor = by / float(iy)
        sx = scale_factor * ix
        if sx > bx:
            scale_factor = bx / float(ix)
            sx = bx
            sy = scale_factor * iy
        else:
            sy = by

    return pg.transform.scale(img, (int(sx), int(sy)))
