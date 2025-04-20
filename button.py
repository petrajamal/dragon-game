import pygame

# button class
class Button():
    def __init__(self, surface, x, y, image, size_x, size_y, text=''):
        self.surface = surface
        if image is not None:
            self.image = pygame.transform.scale(image, (size_x, size_y))
        else:
            self.image = pygame.Surface((size_x, size_y))
            self.image.fill((200, 200, 200))

        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.clicked = False
        self.text = text

        # Set up a basic font for button text
        self.font = pygame.font.SysFont('Arial', 20)
        self.text_surf = self.font.render(text, True, (0, 0, 0))
        self.text_rect = self.text_surf.get_rect(center=self.rect.center)

    def draw(self):
        action = False

        # get mouse position
        pos = pygame.mouse.get_pos()

        # check mouseover and clicked conditions
        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1 and not self.clicked:
                action = True
                self.clicked = True

        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False

        # draw button
        self.surface.blit(self.image, (self.rect.x, self.rect.y))

        # draw text if any
        if self.text:
            self.surface.blit(self.text_surf, self.text_rect)

        return action
