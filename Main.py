"""
Main python file that deals with all UI, all classes except MainGUI are
used as different states the GUI can be in. Each state is based off
either a State class or Wrapper class.

The State class has a loop function that is run every frame, an event
class that is called with every pygame event and on_end function that
is called when the program is exited.

The Wrapper class is a class that effectively lays above any other class,
intercepts function calls and then passes it on to it's child.
This can be very useful for dialogue boxes as stuff is still shown underneath.
"""

from copy import deepcopy
from os import path, listdir, environ
from queue import Empty, Queue
from time import time

environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"  # Sorry pygame but printing is slow
import Othello
import Networking
from Constants import *
from threading import Thread
import UITools as Ui
import pygame
# Experimental may stop working at anytime
from pygame._sdl2.video import Window  # noqa


class MainGUI:
    """Main GUI class that holds GUI constants and sets up pygame."""

    def __init__(self):
        pygame.init()
        self.font_PT = pygame.font.Font(path.join(RES_DIR, "PTC75F.ttf"), 15)
        self.width = 1000
        self.height = 600
        self.position = (100, 100)
        self.monitor_size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
        self.fullscreen = False
        self.r_width = self.width
        self.r_height = self.height
        self.min_size = min(self.height, self.width)
        self.screen = pygame.display.set_mode((self.width, self.height),
                                              pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
        self.window = Window.from_display_module()
        pygame.display.set_caption('Othello')
        self.clock = pygame.time.Clock()
        self.crashed = False
        self.class_state = None
        self.delta_time = 0
        self.last_tick = pygame.time.get_ticks()

    def loop(self):
        """Main game loop that runs at 60 fps."""

        self.crashed = False
        self.class_state = MainMenu()
        while not self.crashed:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    self.crashed = True
                elif event.type == pygame.VIDEORESIZE:
                    if not self.fullscreen:  # Adjust size of window when resized
                        self.width, self.height = event.size
                        self.width = max(500, self.width)
                        self.height = max(300, self.height)
                        self.screen = pygame.display.set_mode((self.width, self.height),
                                                              pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
                        self.update_screen_vars()

                else:
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_f:
                        self.fullscreen = not self.fullscreen
                        if self.fullscreen:
                            self.position = self.window.position
                            self.screen = pygame.display.set_mode(self.monitor_size, pygame.FULLSCREEN)
                            self.update_screen_vars()
                            self.class_state.event(pygame.event.Event(pygame.VIDEORESIZE))

                        else:
                            self.screen = pygame.display.set_mode((self.width, self.height),
                                                                  pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
                            self.window.position = self.position
                            self.update_screen_vars()
                self.class_state.event(event)

            self.class_state.loop()
            pygame.display.flip()  # TODO Make it only update new tiles and move to separate functions
            self.clock.tick(60)
            fps = self.clock.get_fps()
            if fps < 58:
                # print(round(fps, 2))
                pass
            t = pygame.time.get_ticks()
            self.delta_time = (t - self.last_tick) / 1000.0
            self.last_tick = t
        self.class_state.on_end()
        pygame.quit()

    def update_screen_vars(self):
        """Updates the size of the screen variables so that they can be used by other objects."""

        self.r_width = (not self.fullscreen) * self.width + self.fullscreen * self.monitor_size[0]
        self.r_height = (not self.fullscreen) * self.height + self.fullscreen * self.monitor_size[1]
        self.min_size = min(self.r_height, self.r_width)


class State:
    """Abstract class that ensures there is no errors when running state functions."""

    def __init__(self):
        pass

    def loop(self):
        pass

    def event(self, event):
        pass

    def on_end(self):
        pass

    def click_back(self):
        """A function used to get back to the main menu, defined here as it is used by many states."""

        self.on_end()
        t_gui.class_state = MainMenu()


class Wrapper:
    """Abstract class that ensures that it's child methods are run after interception."""

    def __init__(self, child):
        self.child = child

    def loop(self):
        self.child.loop()

    def event(self, event):
        if event.type == pygame.VIDEORESIZE:
            self.child.event(event)

    def on_end(self):
        self.child.on_end()


class Scroll(State):
    """Abstract class used to scroll."""

    def __init__(self, height):
        super().__init__()
        self.scroll_y = 0
        self.height_func = height
        self.height = height()
        self.intermediate = pygame.surface.Surface((t_gui.r_width, self.height))
        self.intermediate.fill(LGREY)

        def back_func(): return (8, 8, t_gui.r_width / 20 + 45, t_gui.r_height / 20 + 12)

        self.back_button = Ui.Button(back_func, LBLUE, self.click_back, text="Back", font=t_gui.font_PT,
                                     **BUTTON_STYLE)

        self.key_up = False
        self.key_down = False

    def event(self, event):
        if event.type == pygame.VIDEORESIZE:
            self.height = self.height_func()
            self.intermediate = pygame.surface.Surface((t_gui.r_width, self.height))
            self.intermediate.fill(LGREY)
            self.check_scroll()

        elif event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
            if event.key == pygame.K_UP:
                self.key_up = event.type == pygame.KEYDOWN
            elif event.key == pygame.K_DOWN:
                self.key_down = event.type == pygame.KEYDOWN

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:
                self.scroll_y = min(self.scroll_y + 45, 0)
                self.back_button.update_scroll((0, -self.scroll_y))
                self.scroll_ui_objects()
            elif event.button == 5:
                self.scroll_y = max(self.scroll_y - 45, -self.height + t_gui.r_height)
                self.back_button.update_scroll((0, -self.scroll_y))
                self.scroll_ui_objects()

        self.back_button.check_event(event)

    def loop(self):
        self.back_button.update(self.intermediate)
        if self.key_up:
            self.scroll_y = min(self.scroll_y + 1800 * t_gui.delta_time, 0)
            self.back_button.update_scroll((0, -self.scroll_y))
            self.scroll_ui_objects()
        elif self.key_down:
            self.scroll_y = max(self.scroll_y - 1800 * t_gui.delta_time, -self.height + t_gui.r_height)
            self.back_button.update_scroll((0, -self.scroll_y))
            self.scroll_ui_objects()
        t_gui.screen.blit(self.intermediate, (
            0, self.scroll_y))  # Blit to intermediate screen and then move that screen to produce scroll effect

    def scroll_ui_objects(self):
        """Used if children want to update scroll of objects."""

        pass

    def check_scroll(self):
        """Checks that the scroll is in the correct bounds."""

        self.scroll_y = max(min(self.scroll_y, 0), -self.height + t_gui.r_height)


class LoadGame(Wrapper):
    """Dialogue box used to decide how a game should be loaded."""

    def __init__(self, child, save_name, current_line):
        super(LoadGame, self).__init__(child)
        self.save_name = save_name
        self.current_line = current_line
        self.r_width = t_gui.r_width * 2 / 3
        self.r_height = t_gui.r_height * 2 / 3
        self.screen_box = pygame.surface.Surface((t_gui.r_width * 2 / 3, t_gui.r_height * 2 / 3))
        self.screen_box.set_colorkey((0, 0, 0))
        self.font = pygame.font.Font(path.join(RES_DIR, "PTC75F.ttf"), 13)

        def back_func(): return (8, 8, self.r_width / 20 + 45, self.r_height / 20 + 12)

        def play_func(): return (self.r_width / 40 + 45, self.r_height / 2 - 20, self.r_width / 10 + 70,
                                 self.r_height / 22 + 25)

        def ai_func(): return (self.r_width * 7 / 8 - 115, self.r_height / 2 - 20, self.r_width / 10 + 70,
                               self.r_height / 22 + 25)

        self.back_button = Ui.Button(back_func, LBLUE, self.click_back, text="Back", font=t_gui.font_PT,
                                     **BUTTON_STYLE)
        self.play_button = Ui.ContextButton(play_func, LBLUE, self.on_play_click,
                                            lambda x: self.on_context_change(0) if x else self.reset_screen(),
                                            text="Couch Play", font=t_gui.font_PT, **BUTTON_STYLE)
        self.ai_button = Ui.ContextButton(ai_func, LBLUE, self.on_ai_click,
                                          lambda x: self.on_context_change(1) if x else self.reset_screen(), text="AI Play",
                                          font=t_gui.font_PT, **BUTTON_STYLE)
        self.blit_text = -1

        self.context_pos = lambda: (10, self.r_height - 30)

        self.context = [self.font.render(CONTEXT_BUTTON_TEXT0, True, (0, 0, 0)),
                        self.font.render(CONTEXT_BUTTON_TEXT1, True, (0, 0, 0))]

        self.buttons = [self.back_button, self.ai_button, self.play_button]

        for button in self.buttons:
            button.update_scroll((-t_gui.r_width * 1 / 6, -t_gui.r_height * 1 / 6))
        self.border = pygame.rect.Rect(0, 0, self.r_width, self.r_height)
        pygame.draw.rect(self.screen_box, (30, 39, 46), self.border, border_radius=8)
        pygame.draw.rect(self.screen_box, LGREY, self.border.inflate(-8, -8), border_radius=8)

    def event(self, event):
        super(LoadGame, self).event(event)
        if event.type == pygame.VIDEORESIZE:
            self.r_width = t_gui.r_width * 2 / 3
            self.r_height = t_gui.r_height * 2 / 3
            self.screen_box = pygame.surface.Surface((t_gui.r_width * 2 / 3, t_gui.r_height * 2 / 3))
            self.screen_box.set_colorkey((0, 0, 0))
            self.border = pygame.rect.Rect(0, 0, self.r_width, self.r_height)
            for button in self.buttons:
                button.update_scroll((-t_gui.r_width * 1 / 6, -t_gui.r_height * 1 / 6))
                button.size_update(self.screen_box)
        for button in self.buttons:
            button.check_event(event)

    def loop(self):
        super(LoadGame, self).loop()
        pygame.draw.rect(self.screen_box, (30, 39, 46), self.border, border_radius=8)
        pygame.draw.rect(self.screen_box, LGREY, self.border.inflate(-8, -8), border_radius=8)
        for button in self.buttons:
            button.update(self.screen_box)
        if self.blit_text != -1:
            self.screen_box.blit(self.context[self.blit_text], self.context_pos())
        t_gui.screen.blit(self.screen_box, (t_gui.r_width * 1 / 6, t_gui.r_height * 1 / 6))

    def click_back(self):
        t_gui.class_state = self.child
        t_gui.class_state.event(pygame.event.Event(pygame.MOUSEMOTION))  # Ensures buttons are properly updated

    def reset_screen(self):
        """Context sentence reset."""

        self.blit_text = -1

    def on_context_change(self, number):
        """Change context sentence."""

        self.blit_text = number

    def on_play_click(self):
        """Function called when single play button is clicked."""

        t_gui.class_state = LoadSavedGameLocalVersus(self.save_name, self.current_line)

    def on_ai_click(self):
        """Function called when ai play button is clicked."""

        t_gui.class_state = AIDifficultySelect(self, self.save_name, self.current_line)


class EndScreen(Wrapper):
    """Dialogue box used to congratulate winner."""

    def __init__(self, child, board_count, state_name):
        super(EndScreen, self).__init__(child)
        self.board_count = board_count
        self.state_name = state_name
        message = self.message_winner()
        self.r_width = t_gui.r_width * 2 / 3
        self.r_height = t_gui.r_height * 2 / 3
        self.screen_box = pygame.surface.Surface((t_gui.r_width * 2 / 3, t_gui.r_height * 2 / 3))
        self.screen_box.set_colorkey((0, 0, 0))
        self.font = pygame.font.Font(path.join(RES_DIR, "PTC75F.ttf"), 13)
        self.big_font = pygame.font.Font(path.join(RES_DIR, "PTC75F.ttf"), 20)

        def back_func():
            return (8, 8, self.r_width / 20 + 45, self.r_height / 20 + 12)

        def play_again_func():
            return (self.r_width / 40 + 5, self.r_height * 3 / 4 - 10, self.r_width / 10 + 110, self.r_height / 22 + 25)

        def prev_func():
            return (self.r_width * 7 / 8 - 115, self.r_height * 3 / 4 - 10, self.r_width / 10 + 110,
                    self.r_height / 22 + 25)

        def confetti_func():
            return (4, 4, self.r_width - 8, self.r_height - 8)

        def message_pos():
            return (20, 30 + t_gui.r_height / 20)

        def message_size():
            return (self.r_width - 20, self.r_height)

        self.back_button = Ui.Button(back_func, LBLUE, self.click_back, text="Back", font=t_gui.font_PT,
                                     **BUTTON_STYLE)
        self.play_again_button = Ui.ContextButton(play_again_func, LBLUE, self.on_play_again_click,
                                                  lambda x: self.on_context_change(0) if x else self.reset_screen(),
                                                  text="Play Again", font=t_gui.font_PT, **BUTTON_STYLE)
        self.prev_button = Ui.ContextButton(prev_func, LBLUE, self.on_prev_click,
                                            lambda x: self.on_context_change(1) if x else self.reset_screen(),
                                            text="Previous Games",
                                            font=t_gui.font_PT, **BUTTON_STYLE)
        self.confetti = Ui.Video(confetti_func, path.join(RES_DIR, "Confetti_Loop.mov"), CONFETTI_DURATION, 1)
        self.message = Ui.Paragraph(message, message_pos, self.big_font, message_size, (1, 1, 1), True)

        self.blit_text = -1

        self.context_pos = lambda: (10, self.r_height - 25)

        if state_name == "LocalVersus":
            state_play = self.font.render(CONTEXT_BUTTON_TEXT0, True, (0, 0, 0))
        else:
            state_play = self.font.render(CONTEXT_BUTTON_TEXT1, True, (0, 0, 0))

        self.context = [state_play, self.font.render(CONTEXT_BUTTON_TEXT3, True, (0, 0, 0))]

        self.buttons = [self.back_button, self.prev_button, self.play_again_button]

        for button in self.buttons:
            button.update_scroll((-t_gui.r_width * 1 / 6, -t_gui.r_height * 1 / 6))

        self.border = pygame.rect.Rect(0, 0, self.r_width, self.r_height)
        self.border_box = pygame.surface.Surface((self.r_width, self.r_height))
        self.border_box.set_colorkey((0, 0, 0))
        pygame.draw.rect(self.border_box, (30, 39, 46), self.border, border_radius=8)
        pygame.draw.rect(self.border_box, (0, 0, 0), self.border.inflate(-8, -8), border_radius=8)
        pygame.draw.rect(self.screen_box, (30, 39, 46), self.border, border_radius=8)
        pygame.draw.rect(self.screen_box, LGREY, self.border.inflate(-8, -8), border_radius=8)
        self.confetti.update(self.screen_box)
        self.screen_box.blit(self.border_box, (0, 0))

    def event(self, event):
        super(EndScreen, self).event(event)
        if event.type == pygame.VIDEORESIZE:
            self.r_width = t_gui.r_width * 2 / 3
            self.r_height = t_gui.r_height * 2 / 3
            self.screen_box = pygame.surface.Surface((t_gui.r_width * 2 / 3, t_gui.r_height * 2 / 3))
            self.screen_box.set_colorkey((0, 0, 0))
            self.border = pygame.rect.Rect(0, 0, self.r_width, self.r_height)
            self.border_box = pygame.surface.Surface((self.r_width, self.r_height))
            self.border_box.set_colorkey((0, 0, 0))
            pygame.draw.rect(self.border_box, (30, 39, 46), self.border, border_radius=8)
            pygame.draw.rect(self.border_box, (0, 0, 0), self.border.inflate(-8, -8), border_radius=8)
            self.confetti.size_update()
            self.message.size_update(self.screen_box)
            for button in self.buttons:
                button.update_scroll((-t_gui.r_width * 1 / 6, -t_gui.r_height * 1 / 6))
                button.size_update(self.screen_box)
        for button in self.buttons:
            button.check_event(event)

    def loop(self):
        super(EndScreen, self).loop()
        pygame.draw.rect(self.screen_box, (30, 39, 46), self.border, border_radius=8)
        pygame.draw.rect(self.screen_box, LGREY, self.border.inflate(-8, -8), border_radius=8)
        self.confetti.update(self.screen_box)
        self.screen_box.blit(self.border_box, (0, 0))
        self.message.update(self.screen_box)
        for button in self.buttons:
            button.update(self.screen_box)
        if self.blit_text != -1:
            self.screen_box.blit(self.context[self.blit_text], self.context_pos())
        t_gui.screen.blit(self.screen_box, (t_gui.r_width * 1 / 6, t_gui.r_height * 1 / 6))

    def click_back(self):
        self.on_end()
        t_gui.class_state = MainMenu()
        t_gui.class_state.event(pygame.event.Event(pygame.MOUSEMOTION))  # Ensures buttons are properly updated

    def reset_screen(self):
        """Context sentence reset."""

        self.blit_text = -1

    def on_context_change(self, number):
        """Change context sentence."""

        self.blit_text = number

    def on_play_again_click(self):
        """Function called when play again is clicked. Checks which state to go to."""

        self.on_end()
        if self.state_name == "LocalVersus":
            t_gui.class_state = LocalVersus()
        elif self.state_name == "AI":
            t_gui.class_state = AIDifficultySelect(self)
        else:
            raise Exception("Incorrect argument")

    def on_prev_click(self):
        """Function called when previous games is clicked."""

        self.on_end()
        t_gui.class_state = SavedGamesViewer()

    def on_end(self):
        """Correctly close the video thread when closing the Gui."""

        self.confetti.on_exit()
        self.child.on_end()

    def message_winner(self):
        """Create the message used to congratulate the winner."""

        count = list((v, k) for (k, v) in sorted(self.board_count.items(), key=lambda item: item[1], reverse=True) if
                     k != "E")  # Sort list in descending order

        if count[0][0] == count[1][0]:
            message = WIN_MESSAGE_TIE.format(count[0][0])
        elif count[0][0] <= count[1][0] + 3:
            if self.state_name == "AI":
                if count[0][1] == "W":
                    message = WIN_MESSAGE_CLOSE_AI_WIN.format(FULL_NAME[count[0][1]], count[0][0],
                                                              FULL_NAME[count[1][1]],
                                                              count[1][0])
                else:
                    message = WIN_MESSAGE_CLOSE_AI_LOSS.format(FULL_NAME[count[0][1]], count[0][0],
                                                               FULL_NAME[count[1][1]],
                                                               count[1][0])
            else:
                message = WIN_MESSAGE_CLOSE.format(FULL_NAME[count[0][1]], count[0][0], FULL_NAME[count[1][1]],
                                                   count[1][0])
        else:
            if self.state_name == "AI":
                if count[0][1] == "W":
                    message = WIN_MESSAGE_AI_WIN.format(FULL_NAME[count[0][1]], count[0][0], FULL_NAME[count[1][1]],
                                                        count[1][0])
                else:
                    message = WIN_MESSAGE_AI_LOSS.format(FULL_NAME[count[0][1]], count[0][0], FULL_NAME[count[1][1]],
                                                         count[1][0])
            else:
                message = WIN_MESSAGE_DEFAULT.format(FULL_NAME[count[0][1]], count[0][0], FULL_NAME[count[1][1]],
                                                     count[1][0])

        return message


class AIDifficultySelect(Wrapper):
    """Dialogue box used to decide how a game should be loaded."""

    def __init__(self, child, save_name=None, line_count=None):
        super(AIDifficultySelect, self).__init__(child)
        self.save_name = save_name
        self.line_count = line_count
        self.r_width = t_gui.r_width * 2 / 3
        self.r_height = t_gui.r_height * 2 / 3
        self.screen_box = pygame.surface.Surface((t_gui.r_width * 2 / 3, t_gui.r_height * 2 / 3))
        self.screen_box.set_colorkey((0, 0, 0))
        self.font = pygame.font.Font(path.join(RES_DIR, "PTC75F.ttf"), 13)

        def back_func(): return (8, 8, self.r_width / 20 + 45, self.r_height / 20 + 12)

        def easy_func(): return (self.r_width / 40 + 45, self.r_height / 2 - 50, self.r_width / 10 + 70,
                                 self.r_height / 22 + 25)

        def normal_func(): return (self.r_width * 7 / 8 - 115, self.r_height / 2 - 50, self.r_width / 10 + 70,
                                   self.r_height / 22 + 25)

        def hard_func(): return (self.r_width / 40 + 45, self.r_height / 2 + 10, self.r_width / 10 + 70,
                                 self.r_height / 22 + 25)

        def insane_func(): return (self.r_width * 7 / 8 - 115, self.r_height / 2 + 10, self.r_width / 10 + 70,
                                   self.r_height / 22 + 25)

        self.back_button = Ui.Button(back_func, LBLUE, self.click_back, text="Back", font=t_gui.font_PT,
                                     **BUTTON_STYLE)
        self.easy_button = Ui.Button(easy_func, LBLUE, self.on_easy_click, text="Easy", font=t_gui.font_PT,
                                     **BUTTON_STYLE)
        self.normal_button = Ui.Button(normal_func, LBLUE, self.on_normal_click, text="Normal", font=t_gui.font_PT,
                                       **BUTTON_STYLE)
        self.hard_button = Ui.Button(hard_func, LBLUE, self.on_hard_click, text="Hard", font=t_gui.font_PT,
                                     **BUTTON_STYLE)
        self.insane_button = Ui.Button(insane_func, LBLUE, self.on_insane_click, text="Insane", font=t_gui.font_PT,
                                       **BUTTON_STYLE)

        self.buttons = [self.back_button, self.easy_button, self.normal_button, self.hard_button, self.insane_button]

        for button in self.buttons:
            button.update_scroll((-t_gui.r_width * 1 / 6, -t_gui.r_height * 1 / 6))
        self.border = pygame.rect.Rect(0, 0, self.r_width, self.r_height)
        pygame.draw.rect(self.screen_box, (30, 39, 46), self.border, border_radius=8)
        pygame.draw.rect(self.screen_box, LGREY, self.border.inflate(-8, -8), border_radius=8)

    def event(self, event):
        super(AIDifficultySelect, self).event(event)
        if event.type == pygame.VIDEORESIZE:
            self.r_width = t_gui.r_width * 2 / 3
            self.r_height = t_gui.r_height * 2 / 3
            self.screen_box = pygame.surface.Surface((t_gui.r_width * 2 / 3, t_gui.r_height * 2 / 3))
            self.screen_box.set_colorkey((0, 0, 0))
            self.border = pygame.rect.Rect(0, 0, self.r_width, self.r_height)
            for button in self.buttons:
                button.update_scroll((-t_gui.r_width * 1 / 6, -t_gui.r_height * 1 / 6))
                button.size_update(self.screen_box)
        for button in self.buttons:
            button.check_event(event)

    def loop(self):
        super(AIDifficultySelect, self).loop()
        pygame.draw.rect(self.screen_box, (30, 39, 46), self.border, border_radius=8)
        pygame.draw.rect(self.screen_box, LGREY, self.border.inflate(-8, -8), border_radius=8)
        for button in self.buttons:
            button.update(self.screen_box)
        t_gui.screen.blit(self.screen_box, (t_gui.r_width * 1 / 6, t_gui.r_height * 1 / 6))

    def click_back(self):
        t_gui.class_state = self.child
        t_gui.class_state.event(pygame.event.Event(pygame.MOUSEMOTION))  # Ensures buttons are properly updated

    def on_easy_click(self):
        """Function called when easy button is clicked."""

        if self.line_count is None and self.save_name is None:
            t_gui.class_state = AI("Easy")
        else:
            t_gui.class_state = LoadSavedGameAI(self.save_name, self.line_count, "Easy")

    def on_normal_click(self):
        """Function called when normal button is clicked."""

        if self.line_count is None and self.save_name is None:
            t_gui.class_state = AI("Normal")
        else:
            t_gui.class_state = LoadSavedGameAI(self.save_name, self.line_count, "Normal")

    def on_hard_click(self):
        """Function called when hard button is clicked."""

        if self.line_count is None and self.save_name is None:
            t_gui.class_state = AI("Hard")
        else:
            t_gui.class_state = LoadSavedGameAI(self.save_name, self.line_count, "Hard")

    def on_insane_click(self):
        """Function called when insane button is clicked."""

        if self.line_count is None and self.save_name is None:
            t_gui.class_state = AI("Insane")
        else:
            t_gui.class_state = LoadSavedGameAI(self.save_name, self.line_count, "Insane")


class MainMenu(State):
    """Main menu state."""

    def __init__(self):
        super().__init__()

        def play_func(): return (9 * t_gui.r_width / 10 - 110, t_gui.r_height / 6 - 20, t_gui.r_width / 10 + 90,
                                 t_gui.r_height / 22 + 25)

        def ai_func(): return (9 * t_gui.r_width / 10 - 110, 19 * t_gui.r_height / 60 - 20, t_gui.r_width / 10 + 90,
                               t_gui.r_height / 22 + 25)

        def how_func(): return (9 * t_gui.r_width / 10 - 110, 7 * t_gui.r_height / 15 + 60, t_gui.r_width / 10 + 90,
                                t_gui.r_height / 22 + 25)

        def prev_func(): return (9 * t_gui.r_width / 10 - 110, 37 * t_gui.r_height / 60 + 60, t_gui.r_width / 10 + 90,
                                 t_gui.r_height / 22 + 25)

        self.play_button = Ui.ContextButton(play_func, LBLUE, MainMenu.on_play_click,
                                            lambda x: self.on_context_change(0) if x else self.reset_screen(),
                                            text="Couch Play", font=t_gui.font_PT, **BUTTON_STYLE)
        self.ai_button = Ui.ContextButton(ai_func, LBLUE, self.on_ai_click,
                                          lambda x: self.on_context_change(1) if x else self.reset_screen(), text="AI Play",
                                          font=t_gui.font_PT, **BUTTON_STYLE)
        self.how_button = Ui.ContextButton(how_func, LBLUE, self.on_how_click,
                                           lambda x: self.on_context_change(2) if x else self.reset_screen(),
                                           text="How To Play", font=t_gui.font_PT, **BUTTON_STYLE)
        self.prev_button = Ui.ContextButton(prev_func, LBLUE, MainMenu.on_prev_click,
                                            lambda x: self.on_context_change(3) if x else self.reset_screen(),
                                            text="Previous Games", font=t_gui.font_PT, **BUTTON_STYLE)

        self.buttons = [self.play_button, self.how_button, self.prev_button, self.ai_button]

        self.context_pos = lambda: (10, t_gui.r_height - 20)

        self.context = [t_gui.font_PT.render(CONTEXT_BUTTON_TEXT0, True, (0, 0, 0)),
                        t_gui.font_PT.render(CONTEXT_BUTTON_TEXT1, True, (0, 0, 0)),
                        t_gui.font_PT.render(CONTEXT_BUTTON_TEXT2, True, (0, 0, 0)),
                        t_gui.font_PT.render(CONTEXT_BUTTON_TEXT3, True, (0, 0, 0))]

        t_gui.screen.fill(LGREY)

    def event(self, event):
        if event.type == pygame.VIDEORESIZE:
            t_gui.screen.fill(LGREY)
        for button in self.buttons:
            button.check_event(event)

    def loop(self):
        for button in self.buttons:
            button.update(t_gui.screen)

    def reset_screen(self):
        """Used to reset the context sentence."""

        t_gui.screen.fill(LGREY)
        for button in self.buttons:
            button.update(t_gui.screen)

    def on_context_change(self, number):
        """Used to update the context sentence."""

        t_gui.screen.blit(self.context[number], self.context_pos())

    @staticmethod
    def on_play_click():
        """Used to load LocalVersus state."""

        t_gui.class_state = LocalVersus()

    def on_how_click(self):
        """Used to load HelpScreen state."""

        t_gui.class_state = AwaitConnection(self)

    @staticmethod
    def on_prev_click():
        """Used to load Previous state."""

        t_gui.class_state = SavedGamesViewer()

    def on_ai_click(self):
        """Used to load AI state."""

        t_gui.class_state = AIDifficultySelect(self)


class HelpScreen(Scroll):
    """Help screen state that shows how to play the game."""

    def __init__(self):
        super().__init__(lambda: 8 * t_gui.r_height)

        def pos_pg1(): return (20, 30 + t_gui.r_height / 20)

        def size_pg1(): return (t_gui.r_width - 20, t_gui.r_height // 5 - 20)

        self.help_pg1 = Ui.Paragraph(HELP_TEXT1, pos_pg1, t_gui.font_PT, size_pg1)

        def size_img1(): return (t_gui.r_width // 2, t_gui.r_height // 2)

        self.ex_img1 = Ui.Image(path.join(RES_DIR, "Example.png"), size_img1, 800)

        def pos_pg2(): return (20, 10 + self.ex_img1.size_update(self.intermediate, (
            t_gui.r_width / 2, self.help_pg1.size_update(self.intermediate) + 5)))

        def size_pg2(): return (t_gui.r_width - 20, t_gui.r_height // 5 - 20)

        self.help_pg2 = Ui.Paragraph(HELP_TEXT2, pos_pg2, t_gui.font_PT, size_pg2)

        self.ex_img2 = Ui.Image(path.join(RES_DIR, "Example1.png"),
                                lambda: (t_gui.r_width // 2, t_gui.r_height // 2), 800)

        def pos_pg3(): return (20, 10 + self.ex_img2.size_update(self.intermediate, (
            t_gui.r_width / 2, self.help_pg2.size_update(self.intermediate) + 5)))

        def size_pg3(): return (t_gui.r_width - 20, t_gui.r_height // 5 - 20)

        self.help_pg3 = Ui.Paragraph(HELP_TEXT2, pos_pg3, t_gui.font_PT, size_pg3)

        self.ex_img3 = Ui.Image(path.join(RES_DIR, "Example2.png"),
                                lambda: (t_gui.r_width // 2, t_gui.r_height // 2), 800)
        self.ex_img3.size_update(self.intermediate,
                                 (t_gui.r_width / 2, self.help_pg3.size_update(self.intermediate) + 5))

    def event(self, event):
        super(HelpScreen, self).event(event)
        if event.type == pygame.VIDEORESIZE:
            self.ex_img3.size_update(self.intermediate,
                                     (t_gui.r_width / 2, self.help_pg3.size_update(self.intermediate) + 5))

    def loop(self):
        super(HelpScreen, self).loop()


class LocalVersus(State):
    """Used to play normal couch multiplayer."""

    def __init__(self, gui_to_oth=None, oth_to_gui=None):
        super().__init__()
        t_gui.screen.fill(LGREY)
        if gui_to_oth is None:
            self.gui_to_oth: Queue = Queue()
        else:
            self.gui_to_oth = gui_to_oth
        if oth_to_gui is None:
            self.oth_to_gui: Queue = Queue()
        else:
            self.oth_to_gui = oth_to_gui

        def pos_func(): return (t_gui.r_width / 2, t_gui.r_height / 2 + 40, t_gui.min_size / 2 + 50)

        self.board = Ui.OthelloLogicBoard(pos_func, BOARD_SIZE, DGREEN, DBLACK, self.gui_to_oth)
        self.board_logic = None
        self.start_board_ai()

        def back_func(): return (8, 8, t_gui.r_width / 20 + 45, t_gui.r_height / 20 + 12)

        self.back_button = Ui.Button(back_func, LBLUE, self.click_back, text="Back", font=t_gui.font_PT,
                                     **BUTTON_STYLE)

        def b_pos(): return (t_gui.r_width / 2 - t_gui.min_size / BOARD_SIZE + 1,
                             35 + t_gui.r_height / 25 + (t_gui.r_height / 4 + 30) / BOARD_SIZE)

        def b_count(): return ((t_gui.r_height / 4 + 30) // BOARD_SIZE,
                               (t_gui.r_width / 2 - t_gui.min_size / BOARD_SIZE, 25 + t_gui.r_height / 25))

        self.b_count = Ui.PieceCount(b_pos, b_count, t_gui.font_PT, "B")

        def w_pos(): return (t_gui.r_width / 2 + t_gui.min_size / BOARD_SIZE + 2,
                             35 + t_gui.r_height / 25 + (t_gui.r_height / 4 + 30) / BOARD_SIZE)

        def w_count(): return ((t_gui.r_height / 4 + 30) // BOARD_SIZE,
                               (t_gui.r_width / 2 + t_gui.min_size / BOARD_SIZE, 25 + t_gui.r_height / 25))

        self.w_count = Ui.PieceCount(w_pos, w_count, t_gui.font_PT, "W")

        self.queue_listeners = [self.w_count, self.b_count, self.board]

        self.board.update(t_gui.screen, True)
        self.playing_colour = "B"
        self.b_count.update(t_gui.screen)
        self.w_count.update(t_gui.screen)
        self.win_time = None
        self.win_package = None

    def loop(self):
        while True:
            try:
                get = self.oth_to_gui.get(False)
            except Empty:
                break
            else:
                if get[0] == LOCAL_IO["Winner"]:
                    self.win_time = time()
                    self.win_package = get[1]
                for item in self.queue_listeners:
                    try:
                        item.queue_get(get)
                    except AttributeError:
                        raise Exception("Item does not handle queues")

        if self.win_time is not None and self.win_time + 0.5 <= time():
            t_gui.class_state = EndScreen(self, self.win_package, "LocalVersus")
            self.win_package, self.win_time = None, None
        t_gui.screen.fill(LGREY)
        self.board.update(t_gui.screen)
        self.w_count.update(t_gui.screen)
        self.b_count.update(t_gui.screen)
        self.back_button.update(t_gui.screen)

    def event(self, event):
        if event.type == pygame.VIDEORESIZE:
            t_gui.screen.fill(LGREY)
            self.board.size_update(t_gui.screen)
            self.b_count.size_update(t_gui.screen)
            self.w_count.size_update(t_gui.screen)
        elif event.type == pygame.VIDEOEXPOSE:
            t_gui.screen.fill(LGREY)
            self.board.size_update(t_gui.screen)
            self.b_count.size_update(t_gui.screen)
            self.w_count.size_update(t_gui.screen)
        self.board.check_event(event)
        self.back_button.check_event(event)

    def on_end(self):
        """End the board logic thread."""

        self.gui_to_oth.put((LOCAL_IO["End"], None))
        if self.board_logic:
            self.board_logic.join()

    def start_board_ai(self):
        """Start the board logic thread, in separate function as type of board can be dependent on state."""

        self.board_logic = Thread(target=Othello.LocalVersus, args=(self.gui_to_oth, self.oth_to_gui))
        self.board_logic.start()


class LoadSavedGameLocalVersus(LocalVersus):
    """State that loads from a save file."""

    def __init__(self, save_name, line_count):
        self.save_name = save_name
        self.line_count = line_count
        super().__init__()

    def start_board_ai(self):
        """Start the board logic thread, in separate function as type of board can be dependent on state."""

        self.board_logic = Thread(target=Othello.LoadLocalVersus,
                                  args=(self.gui_to_oth, self.oth_to_gui, self.save_name, self.line_count))
        self.board_logic.start()


class AI(LocalVersus):
    """AI state."""

    def __init__(self, difficulty):
        self.difficulty = difficulty
        super().__init__()

    def loop(self):
        while True:
            try:
                get = self.oth_to_gui.get(False)
            except Empty:
                break
            else:
                if get[0] == LOCAL_IO["Winner"]:
                    self.win_time = time()
                    self.win_package = get[1]

                for item in self.queue_listeners:
                    try:
                        item.queue_get(get)
                    except AttributeError:
                        raise Exception("Item does not handle queues")

        if self.win_time is not None and self.win_time + 0.5 <= time():
            t_gui.class_state = EndScreen(self, self.win_package, "AI")
            self.win_package, self.win_time = None, None
        t_gui.screen.fill(LGREY)
        self.board.update(t_gui.screen)
        self.w_count.update(t_gui.screen)
        self.b_count.update(t_gui.screen)
        self.back_button.update(t_gui.screen)

    def start_board_ai(self):
        """Start the board logic thread, in separate function as type of board can be dependent on state."""

        self.board_logic = Thread(target=Othello.AI, args=(self.gui_to_oth, self.oth_to_gui, self.difficulty))
        self.board_logic.start()

class Network(LocalVersus):
    """Network state."""

    def __init__(self, gui_to_oth, oth_to_gui, oth_to_network, networking_logic):
        self.networking_logic = networking_logic
        self.oth_to_network = oth_to_network
        super().__init__(gui_to_oth, oth_to_gui)

    def loop(self):
        if not self.networking_logic.is_alive():
            self.on_end()
            t_gui.class_state = NetworkError(State())

        while True:
            try:
                get = self.oth_to_gui.get(False)
            except Empty:
                break
            else:
                if get[0] == LOCAL_IO["Winner"]:
                    self.win_time = time()
                    self.win_package = get[1]

                for item in self.queue_listeners:
                    try:
                        item.queue_get(get)
                    except AttributeError:
                        raise Exception("Item does not handle queues")

        if self.win_time is not None and self.win_time + 0.5 <= time():
            t_gui.class_state = EndScreen(self, self.win_package, "Network")
            self.win_package, self.win_time = None, None
        t_gui.screen.fill(LGREY)
        self.board.update(t_gui.screen)
        self.w_count.update(t_gui.screen)
        self.b_count.update(t_gui.screen)
        self.back_button.update(t_gui.screen)

    def start_board_ai(self):
        """Start the board logic thread, in separate function as type of board can be dependent on state."""

        self.board_logic = Thread(target=Othello.NetworkVersus, args=(self.gui_to_oth, self.oth_to_gui, self.oth_to_network))
        self.board_logic.start()

    def on_end(self):

        self.oth_to_network.put((LOCAL_IO["Net_End"], None))
        self.gui_to_oth.put((LOCAL_IO["End"], None))
        if self.networking_logic:
            self.networking_logic.join()
        if self.board_logic:
            self.board_logic.join()

class AwaitConnection(Wrapper):

    def __init__(self, child):
        super(AwaitConnection, self).__init__(child)
        self.network_to_load, self.gui_to_oth, self.oth_to_network = Queue(), Queue(), Queue()

        self.r_width = t_gui.r_width * 2 / 3
        self.r_height = t_gui.r_height * 2 / 3
        self.screen_box = pygame.surface.Surface((t_gui.r_width * 2 / 3, t_gui.r_height * 2 / 3))
        self.screen_box.set_colorkey((0, 0, 0))
        self.big_font = pygame.font.Font(path.join(RES_DIR, "PTC75F.ttf"), 20)

        def back_func():
            return (8, 8, self.r_width / 20 + 45, self.r_height / 20 + 12)

        def load_func():
            return (0.47*self.r_width -20, 9/20*self.r_height - 20, self.r_width / 10 + 40, self.r_height / 10 + 40)

        def message_pos():
            return (0, - 10 + self.r_height *15 / 20)

        def message_size():
            return (self.r_width, self.r_height / 4)

        self.back_button = Ui.Button(back_func, LBLUE, self.click_back, text="Back", font=t_gui.font_PT,
                                     **BUTTON_STYLE)
        self.load = Ui.ThreadedGIFImage(load_func, path.join(RES_DIR, "load"), LOAD_DURATION)
        self.message = Ui.Paragraph(LOADING_CONN_MESSAGE, message_pos, self.big_font, message_size, (1, 1, 1), True)

        self.back_button.update_scroll((-t_gui.r_width * 1 / 6, -t_gui.r_height * 1 / 6))

        self.border = pygame.rect.Rect(0, 0, self.r_width, self.r_height)
        self.border_box = pygame.surface.Surface((self.r_width, self.r_height))
        self.border_box.set_colorkey((0, 0, 0))
        pygame.draw.rect(self.border_box, (30, 39, 46), self.border, border_radius=8)
        pygame.draw.rect(self.border_box, (0, 0, 0), self.border.inflate(-8, -8), border_radius=8)
        pygame.draw.rect(self.screen_box, (30, 39, 46), self.border, border_radius=8)
        pygame.draw.rect(self.screen_box, LGREY, self.border.inflate(-8, -8), border_radius=8)
        self.load.update(self.screen_box)
        self.screen_box.blit(self.border_box, (0, 0))

        self.networking_logic = Thread(target = Networking.main, args = (self.gui_to_oth, self.oth_to_network, self.network_to_load), daemon=True)
        self.networking_logic.start()


    def event(self, event):
        super(AwaitConnection, self).event(event)
        if event.type == pygame.VIDEORESIZE:
            self.r_width = t_gui.r_width * 2 / 3
            self.r_height = t_gui.r_height * 2 / 3
            self.screen_box = pygame.surface.Surface((t_gui.r_width * 2 / 3, t_gui.r_height * 2 / 3))
            self.screen_box.set_colorkey((0, 0, 0))
            self.border = pygame.rect.Rect(0, 0, self.r_width, self.r_height)
            self.border_box = pygame.surface.Surface((self.r_width, self.r_height))
            self.border_box.set_colorkey((0, 0, 0))
            pygame.draw.rect(self.border_box, (30, 39, 46), self.border, border_radius=8)
            pygame.draw.rect(self.border_box, (0, 0, 0), self.border.inflate(-8, -8), border_radius=8)
            self.load.size_update()
            self.message.size_update(self.screen_box)
            self.back_button.update_scroll((-t_gui.r_width * 1 / 6, -t_gui.r_height * 1 / 6))
            self.back_button.size_update(self.screen_box)

        self.back_button.check_event(event)

    def loop(self):
        super(AwaitConnection, self).loop()
        pygame.draw.rect(self.screen_box, (30, 39, 46), self.border, border_radius=8)
        pygame.draw.rect(self.screen_box, LGREY, self.border.inflate(-8, -8), border_radius=8)
        self.load.update(self.screen_box)
        self.screen_box.blit(self.border_box, (0, 0))
        self.message.update(self.screen_box)
        self.back_button.update(self.screen_box)
        t_gui.screen.blit(self.screen_box, (t_gui.r_width * 1 / 6, t_gui.r_height * 1 / 6))
        try:
            get = self.network_to_load.get(False)
        except Empty:
            pass
        else:
            if get[0] == LOCAL_IO["Net_Loaded"]:
                t_gui.class_state = Network(self.gui_to_oth, None, self.oth_to_network, self.networking_logic)
                t_gui.class_state.event(pygame.event.Event(pygame.MOUSEMOTION))


    def click_back(self):
        self.on_end()
        t_gui.class_state = self.child
        t_gui.class_state.event(pygame.event.Event(pygame.MOUSEMOTION))  # Ensures buttons are properly updated

    def on_end(self):

        self.oth_to_network.put((LOCAL_IO["Net_End"], None))
        if self.networking_logic:
            self.networking_logic.join()

        self.child.on_end()

class NetworkError(Wrapper):

    def __init__(self, child):
        super(NetworkError, self).__init__(child)
        self.r_width = t_gui.r_width * 2 / 3
        self.r_height = t_gui.r_height * 2 / 3
        self.screen_box = pygame.surface.Surface((t_gui.r_width * 2 / 3, t_gui.r_height * 2 / 3))
        self.screen_box.set_colorkey((0, 0, 0))
        self.big_font = pygame.font.Font(path.join(RES_DIR, "PTC75F.ttf"), 20)

        def back_func():
            return (8, 8, self.r_width / 20 + 45, self.r_height / 20 + 12)

        def message_pos():
            return (0, - 10 + self.r_height *1 / 2)

        def message_size():
            return (self.r_width, self.r_height / 4)

        self.back_button = Ui.Button(back_func, LBLUE, self.click_back, text="Back", font=t_gui.font_PT,
                                     **BUTTON_STYLE)
        self.message = Ui.Paragraph(CON_ERROR_MESSAGE, message_pos, self.big_font, message_size, (1, 1, 1), True)

        self.back_button.update_scroll((-t_gui.r_width * 1 / 6, -t_gui.r_height * 1 / 6))

        self.border = pygame.rect.Rect(0, 0, self.r_width, self.r_height)
        self.border_box = pygame.surface.Surface((self.r_width, self.r_height))
        self.border_box.set_colorkey((0, 0, 0))
        pygame.draw.rect(self.border_box, (30, 39, 46), self.border, border_radius=8)
        pygame.draw.rect(self.border_box, (0, 0, 0), self.border.inflate(-8, -8), border_radius=8)
        pygame.draw.rect(self.screen_box, (30, 39, 46), self.border, border_radius=8)
        pygame.draw.rect(self.screen_box, LGREY, self.border.inflate(-8, -8), border_radius=8)
        self.screen_box.blit(self.border_box, (0, 0))


    def event(self, event):
        super(NetworkError, self).event(event)
        if event.type == pygame.VIDEORESIZE:
            self.r_width = t_gui.r_width * 2 / 3
            self.r_height = t_gui.r_height * 2 / 3
            self.screen_box = pygame.surface.Surface((t_gui.r_width * 2 / 3, t_gui.r_height * 2 / 3))
            self.screen_box.set_colorkey((0, 0, 0))
            self.border = pygame.rect.Rect(0, 0, self.r_width, self.r_height)
            self.border_box = pygame.surface.Surface((self.r_width, self.r_height))
            self.border_box.set_colorkey((0, 0, 0))
            pygame.draw.rect(self.border_box, (30, 39, 46), self.border, border_radius=8)
            pygame.draw.rect(self.border_box, (0, 0, 0), self.border.inflate(-8, -8), border_radius=8)
            self.message.size_update(self.screen_box)
            self.back_button.update_scroll((-t_gui.r_width * 1 / 6, -t_gui.r_height * 1 / 6))
            self.back_button.size_update(self.screen_box)

        self.back_button.check_event(event)

    def loop(self):
        super(NetworkError, self).loop()
        pygame.draw.rect(self.screen_box, (30, 39, 46), self.border, border_radius=8)
        pygame.draw.rect(self.screen_box, LGREY, self.border.inflate(-8, -8), border_radius=8)
        self.screen_box.blit(self.border_box, (0, 0))
        self.message.update(self.screen_box)
        self.back_button.update(self.screen_box)
        t_gui.screen.blit(self.screen_box, (t_gui.r_width * 1 / 6, t_gui.r_height * 1 / 6))

    def click_back(self):
        self.on_end()
        t_gui.class_state = MainMenu()
        t_gui.class_state.event(pygame.event.Event(pygame.MOUSEMOTION))  # Ensures buttons are properly updated

    def on_end(self):

        self.child.on_end()


class LoadSavedGameAI(AI):
    """State that loads from a save file."""

    def __init__(self, save_name, line_count, difficulty):
        self.save_name = save_name
        self.line_count = line_count
        super().__init__(difficulty)

    def start_board_ai(self):
        """Start the board logic thread, in separate function as type of board can be dependent on state."""

        self.board_logic = Thread(target=Othello.LoadAI,
                                  args=(self.gui_to_oth, self.oth_to_gui, self.save_name, self.line_count, self.difficulty))
        self.board_logic.start()


class SavedGamesViewer(Scroll):  # TODO Scroll to top.
    """State that shows previous games."""

    def __init__(self):
        self.save_games = []
        self.ui_objects = []
        self.saves = False
        for file in sorted(listdir(SAVE_DIR), key=lambda x: path.getmtime(path.join(SAVE_DIR, x))):
            if file.endswith(SAVE_SUFFIX):
                self.save_games.insert(0, file)
                self.saves = True
        if self.saves:
            self.oth_to_gui = Queue()
            loader = Thread(target=Othello.load_othello, args=(deepcopy(self.save_games), self.oth_to_gui), daemon=True)
            loader.start()
            self.pointer = 0
        super().__init__(lambda: max(t_gui.r_height,
                                     int(t_gui.r_height / 2 - 150 + len(self.save_games) * (t_gui.min_size / 2 + 150))))

    def event(self, event):
        super(SavedGamesViewer, self).event(event)
        if event.type == pygame.VIDEORESIZE:
            for ui in self.ui_objects:
                ui.size_update(self.intermediate)
        for ui in self.ui_objects:
            ui.check_event(event)

    def loop(self):
        if self.saves and self.pointer < len(self.save_games):
            try:
                get = self.oth_to_gui.get(False)
            except Empty:
                pass
            else:
                if get[0] == LOCAL_IO["Loader"]:
                    def pos_func(x):
                        return (
                            t_gui.r_width / 2, t_gui.r_height / 2 + x * (t_gui.min_size / 2 + 150),
                            t_gui.min_size / 2 + 50)

                    self.ui_objects.append(
                        board := Ui.SavedGamesBoard(pos_func, BOARD_SIZE, DGREEN, DBLACK, get[1].line_load_current()[1],
                                                    self.pointer))

                    def pos_func(x):
                        return (
                            t_gui.r_width / 2 - t_gui.min_size // BOARD_SIZE - (t_gui.r_width / 20 + 53),
                            t_gui.r_height / 2 + x * (t_gui.min_size / 2 + 150) - (t_gui.min_size / 4 + 25) - (
                                    t_gui.r_height / 20 + 20), t_gui.r_width / 20 + 50,
                            t_gui.r_height / 20 + 12)

                    self.ui_objects.append(
                        Ui.SavedBoardButton(pos_func, LBLUE, LGREY, get[1], board, False, self.pointer, text="Previous",
                                            font=t_gui.font_PT, **BUTTON_STYLE))

                    def pos_func(x):
                        return (
                            t_gui.r_width / 2 - t_gui.r_width / 40 - 10,
                            t_gui.r_height / 2 + x * (t_gui.min_size / 2 + 150) - (t_gui.min_size / 4 + 25) - (
                                    t_gui.r_height / 20 + 20), t_gui.r_width / 20 + 20,
                            t_gui.r_height / 20 + 12)

                    self.ui_objects.append(
                        Ui.ArgumentCallerButton(pos_func, LBLUE, self.on_launch, self.pointer, get[1], text="Load",
                                                font=t_gui.font_PT, **BUTTON_STYLE))

                    def pos_func(x):
                        return (
                            t_gui.r_width / 2 + t_gui.min_size // BOARD_SIZE,
                            t_gui.r_height / 2 + x * (t_gui.min_size / 2 + 150) - (t_gui.min_size / 4 + 25) - (
                                    t_gui.r_height / 20 + 20), t_gui.r_width / 20 + 50,
                            t_gui.r_height / 20 + 12)

                    self.ui_objects.append(
                        Ui.SavedBoardButton(pos_func, LBLUE, LGREY, get[1], board, True, self.pointer,
                                            text="Forwards", font=t_gui.font_PT, **BUTTON_STYLE))

                    self.pointer += 1

                elif get[0]:
                    self.save_games.pop(self.pointer)
                    self.event(pygame.event.Event(pygame.VIDEORESIZE))
                    print("Failed to load the board: " + get[1].save_name + ", deleting file!")
                    try:
                        get[1].delete_file()
                    except FileNotFoundError:
                        print("Failed to delete board!")

        for ui in self.ui_objects:
            ui.update(self.intermediate)
        super(SavedGamesViewer, self).loop()

    def scroll_ui_objects(self):
        """Scrolls all ui objects."""

        for ui in self.ui_objects:
            try:
                ui.update_scroll((0, -self.scroll_y))
            except AttributeError:
                pass

    def on_launch(self, board):
        """Open loading dialogue box."""

        t_gui.class_state = LoadGame(self, board.save_name, board.current_line)


if __name__ == "__main__":
    t_gui = MainGUI()
    t_gui.loop()
    quit()
