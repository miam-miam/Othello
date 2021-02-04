"""Separate thread file to deal with videos."""

from queue import Empty

import cv2 as cv
import pygame

from Constants import LOCAL_IO


def get_video(path, size, queue, max_queue, aspect=0):
    """Get video and add to queue once properly formatted."""

    video = cv.VideoCapture(path)
    if aspect == 0:
        size = keep_aspect_ratio(video, *size)
    elif aspect == 1:
        size = cut(video, *size)
    else:
        size = (int(size[0]), int(size[1]))
    while True:
        try:
            get = queue.get(False)
        except Empty:
            pass
        else:
            if get[0] == LOCAL_IO["Stop"]:
                break

        ret, frame = video.read()
        if not ret:
            video.set(2, 0.0)
            ret, frame = video.read()

        frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        frame = cv.resize(frame, size)
        frame = frame.swapaxes(0, 1)
        surface = pygame.surfarray.make_surface(frame)
        surface.set_colorkey((0, 0, 0))
        max_queue.put((LOCAL_IO["Video"], surface))


def keep_aspect_ratio(vid, bx, by):
    """Scales image to fit into bx/by, this method will retain the original image's aspect ratio."""

    ix = vid.get(cv.CAP_PROP_FRAME_WIDTH)
    iy = vid.get(cv.CAP_PROP_FRAME_HEIGHT)

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

    return int(sx), int(sy)


def cut(vid, bx, by):
    """Scales image without changing aspect ratio but instead growing to at least the size of box bx/by."""

    ix = vid.get(cv.CAP_PROP_FRAME_WIDTH)
    iy = vid.get(cv.CAP_PROP_FRAME_HEIGHT)

    if bx / float(ix) > by / float(iy):  # fit to width

        scale_factor = bx / float(ix)
        sy = scale_factor * iy
        sx = bx

    else:  # fit to height

        scale_factor = by / float(iy)
        sx = scale_factor * ix
        sy = by

    return int(sx), int(sy)
