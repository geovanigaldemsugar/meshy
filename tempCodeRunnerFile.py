

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

    window_surface.blit(background, (0, 0))
    manager.draw_ui(window_surface)

    pygame.display.update()