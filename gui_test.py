import pygame
import pygame_gui
from pygame_gui.elements import *




# hello_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((350, 275), (100, 50)),
#                                             text='Say Hello',
#                                             manager=manager)
# dm = pygame_gui.elements.UIDropDownMenu(options_list=['One', 'Two', 'Three'],
#                                    starting_option='One',
#                                    relative_rect=pygame.Rect((350, 350), (100, 30)),
                                #    manager=manager)

# class UIInputStepper

# Create UI elements
# input_rect = pygame.Rect(50, 50, 100, 30)
# text_input = pygame_gui.elements.UITextEntryLine(relative_rect=input_rect, manager=manager)
# button_up = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(150, 50, 30, 15), text='▲', manager=manager)
# button_down = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(150, 65, 30, 15), text='▼', manager=manager)
# u = pygame_gui.elements.UITextEntryBox(relative_rect=pygame.Rect(200, 50, 100, 300),  manager=manager)
# p = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect(50, 100, 100, 30), manager=manager)
# pygame_gui.elements.UI2DSlider(start_value_x=0.3, value_range_x=(0.0, 1.0), start_value_y=0.3, value_range_y=(0.0, 1.0), relative_rect=pygame.Rect(50, 150, 200, 30), manager=manager)
# pygame_gui.elements.UIHorizontalSlider(start_value=0.5, click_increment=0.1, value_range=(0.0, 1.0), relative_rect=pygame.Rect(50, 200, 200, 30), manager=manager)

class UIInputStepper(pygame_gui.core.UIContainer):
    # # give element id
    # method to get current Value
    # method to set limits

    
    def __init__(self, relative_rect, manager, ratio=(0.2, 0.6), value=0, step=1.1, range=(-10000000, 10000000)):
        print(relative_rect.x, relative_rect.y, relative_rect.w, relative_rect.h)
        self.step = step
        element_id = 'input_stepper'
        object_id = None
        self.range = range
        self._value = value


        super().__init__(relative_rect, manager=manager, element_id=element_id, object_id=object_id)
        btn_width = relative_rect.w * ratio[0]
        entry_width = relative_rect.w * ratio[1]

        print(btn_width, entry_width)
        d_Rect = pygame.Rect(0,
                        0,
                        btn_width,
                        relative_rect.h)
        
        self.decri_button = UIButton(relative_rect=d_Rect,
                                                        manager=manager,
                                                        container=self,
                                                        text='<')

        e_Rect = pygame.Rect(d_Rect.w - 4,
                        0,
                        entry_width,
                        relative_rect.h)
        
        self.entry_line = UITextEntryLine(relative_rect=e_Rect,
                                        manager=manager,
                                        container=self,
                                        initial_text=str(self.value)
                                        )
        
        self.entry_line.set_allowed_characters(list('0123456789.-'))

        i_Rect = pygame.Rect(e_Rect.w + d_Rect.w - 10,
                             0,
                             btn_width,
                        relative_rect.h)
        self.incri_button = UIButton(relative_rect=i_Rect, 
                                                        manager=manager,
                                                        container=self,
                                                        text='>')
        

    def handle_event(self, event):
        # check for button presses(to update_entry) and entry_line updates
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.decri_button:
                self._value -= self.step
                self._value = self._clamp(self._value)
                self.set_value()

            elif event.ui_element == self.incri_button:
                self._value += self.step
                self._value = self._clamp(self._value)
                self.set_value()

        
        if event.type == pygame_gui.UI_TEXT_ENTRY_FINISHED and event.ui_element == self.entry_line:
            text = self.entry_line.get_text()
            if text != '':
                self.value = float(text)
                print(self.value, self._value)
                self.set_value()

    @property
    def value(self):
        return self._value
    
    @value.setter
    def value(self, value):
        self._value = self._clamp(value)
        
    def set_value(self):
        self.entry_line.set_text(str(round(self._value, 5)))

    def _clamp(self, value):
        """ clamp value within specified range"""
        return max(self.range[0], min(value, self.range[1]))


if __name__ == '__main__':

    pygame.init()

    pygame.display.set_caption('Quick Start')
    window_surface = pygame.display.set_mode((800, 600))

    background = pygame.Surface((800, 600))
    background.fill(pygame.Color('#000000'))

    manager = pygame_gui.UIManager((800, 600))
    # decri_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(50, 50, 30, 30), manager=manager, text='<')
    # entry_line = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect(75, 50, 100, 30), manager=manager)
    # incr_button = decri_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(170, 50, 30, 30), manager=manager, text='>')
    # pygame_gui.elements.UITabContainer(relative_rect=pygame.Rect(300, 50, 400, 400), manager=manager)
    x =15
    IS  = UIInputStepper(relative_rect=pygame.Rect(50, 50, 200, 40), manager=manager, value=x)
    clock = pygame.time.Clock()
    is_running = True

    while is_running:
        time_delta = clock.tick(60)/1000.0
        for event in pygame.event.get():
            IS.handle_event(event)
            if event.type == pygame.QUIT:
                is_running = False
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                pass
                print(IS.incri_button)
                print(x)
                
                # if event.ui_element == hello_button:
                #   print('Test button pressed')


            manager.process_events(event)

        manager.update(time_delta)
    # 
        window_surface.blit(background, (0, 0))
        manager.draw_ui(window_surface)

        pygame.display.update()