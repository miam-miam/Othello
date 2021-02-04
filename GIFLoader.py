"""Separate thread file that loads GIFs (actually just separate images)"""

from os import path
from time import sleep
import pygame as pg

from Constants import LOCAL_IO


def get_frames(length, filename, pos, duration, queue):
    """Gets all the frames in certain directory and loads them into queue."""

    for x in range(length):
        image = pg.image.load(path.join(filename, str(x) + ".png"))
        scaled_image = keep_aspect_ratio(image, *pos[2:])
        queue.put((LOCAL_IO["Loaded"], image, scaled_image, duration[x]))
        sleep(duration[x]*0.0005)


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
