from pathlib import Path
import pygame
import random
import button 
import math
import pandas as pd
import tensorflow as tf
import numpy as np

pygame.init()

clock = pygame.time.Clock()
fps = 60

#font
font = pygame.font.SysFont('Times New Roman', 26)

#game window
bottom_panel = 150
screen_width = 800
screen_height = 400 + bottom_panel

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Battle')
summary_shown = False

class GameState():
    def __init__(self):
        #define game variables
        self.summary_shown = False
        self.player_action_count = {"attack": 0, "potion": 0}
        self.performance_data = []
        self.reaction_time = 0
        self.turn_start_time = 0
        self.turn_count = 0
        self.current_fighter = 1
        self.total_fighters = 2
        self.action_cooldown = 0
        self.action_wait_time = 90
        self.attack = False
        self.potion = False
        self.potion_effect = 15
        self.clicked = False
        self.game_over = 0
        self.run = True
        self.model = None

game_state = GameState()

#define colours
red = (255, 0, 0)
green = (0, 255, 0)
silver = (192, 192, 192)

#load images
#panel image
panel_img = pygame.image.load('img/Icons/panel.png').convert_alpha()
#sword image 
sword_img = pygame.image.load('img/Icons/sword.png').convert_alpha()
#button image
potion_img = pygame.image.load('img/Icons/potion.png').convert_alpha()
restart_img = pygame.image.load('img/Icons/restart.png').convert_alpha()
#load victory and defeat images
victory_img = pygame.image.load('img/Icons/victory.png').convert_alpha()
defeat_img = pygame.image.load('img/Icons/defeat.png').convert_alpha()

#load theme images
themes = {
    'Dark forest': pygame.image.load('img/Background/forest.png').convert_alpha(),
    'Green field': pygame.image.load('img/Background/green_field.jpg').convert_alpha(),
    'Winter realm': pygame.image.load('img/Background/winter.jpg').convert_alpha(),
}

#create theme menu
def theme_selection():
    selecting = True
    while selecting:
        screen.fill((0, 0, 0))
        draw_text("Choose a Theme:", 'Times New Roman', 32, silver, 290, 50)
        pygame.event.clear(pygame.MOUSEBUTTONDOWN)

        y = 150
        theme_buttons = {}
        for name in themes:
            theme_buttons[name] = button.Button(screen, 300, y, None, 200, 40, text=name)
            if theme_buttons[name].draw():
                pygame.time.delay(200)
                pygame.event.clear()
                return name, themes[name]
            y += 60

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return None, None
        pygame.display.update()

#load character images
characters = ['Knight', 'Bandit']

#create character menu
def character_selection():
    selecting = True
    while selecting:
        screen.fill((0, 0, 0))
        draw_text("Choose Your Character:", 'Times New Roman', 32, silver, 245, 50)
        pygame.event.clear(pygame.MOUSEBUTTONDOWN)

        y = 150
        character_buttons = {}
        for filename in characters:
            name = filename
            character_buttons[filename] = button.Button(screen, 300, y, None, 200, 40, text=name)
            if character_buttons[filename].draw():
                pygame.time.delay(200)
                pygame.event.clear()
                return filename
            y += 60

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return None
        pygame.display.update()

#create difficulty levels
difficulty_levels = {
    'Easy': {
        'dragon_max_hp': 20,
        'dragon_regen': 1600,
        'dragon_strength': 8,
        'fighter_max_hp': 35,
        'fighter_strength': 12,
        'fighter_potions': 4
    },
    'Medium': {
        'dragon_max_hp': 30,
        'dragon_regen': 1300,
        'dragon_strength': 10,
        'fighter_max_hp': 30,
        'fighter_strength': 10,
        'fighter_potions': 3
    },
    'Hard': {
        'dragon_max_hp': 40,
        'dragon_regen': 1000,
        'dragon_strength': 12,
        'fighter_max_hp': 25,
        'fighter_strength': 8,
        'fighter_potions': 2
    }
}

#create difficulty level selection menu
def difficulty_selection():
    selecting = True
    while selecting:
        screen.fill((0, 0, 0))
        draw_text("Select Difficulty:", 'Times New Roman', 32, silver, 290, 50)
        
        difficulty_buttons = {}
        y = 150
        for difficulty in difficulty_levels:
            difficulty_buttons[difficulty] = button.Button(screen, 300, y, None, 200, 40, text=difficulty)
            if difficulty_buttons[difficulty].draw():
                pygame.time.delay(200)
                pygame.event.clear()
                return difficulty_levels[difficulty]
            y += 60

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return None
        pygame.display.update()

#create function for drawing text
def draw_text(text, font, font_size, text_col, x, y):
    font = pygame.font.SysFont('Times New Roman', font_size)
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

#function for drawing background
def draw_bg():
    screen.blit(bg_img, (0, 0))

#function for drawing panel
def draw_panel():
    screen.blit(panel_img, (0, screen_height - bottom_panel))
    #show knight stats
    draw_text(f'{knight.name} HP: {knight.hp}', 'Times New Roman', 26, silver, 120, screen_height - bottom_panel + 10)
    draw_text(f'{dragon.name} HP: {dragon.hp}', 'Times New Roman', 26, silver, 520, screen_height - bottom_panel + 10)

#fighter class
class Fighter():
    def __init__(self, name, max_hp, strength, potions):
        self.name = name
        self.x = 200
        self.y = 260 if self.name == 'Knight' else 270
        self.max_hp = max_hp
        self.hp = max_hp
        self.strength = strength
        self.start_potions = potions
        self.potions = potions
        self.alive = True
        self.animation_list = []
        self.frame_index = 0
        #0:idle 1:attack 2:hurt 3:dead
        self.action = 0
        self.update_time = pygame.time.get_ticks()
        #load idle images
        temp_list = []
        for i in range(8):
            img = pygame.image.load(f'img/{self.name}/Idle/{i}.png')
            img = pygame.transform.scale(img, (img.get_width() * 3, img.get_height() * 3))
            temp_list.append(img)
        self.animation_list.append(temp_list)
        #load attack images
        temp_list = []
        for i in range(8):
            img = pygame.image.load(f'img/{self.name}/Attack/{i}.png')
            img = pygame.transform.scale(img, (img.get_width() * 3, img.get_height() * 3))
            temp_list.append(img)
        self.animation_list.append(temp_list)
        #load hurt images
        temp_list = []
        for i in range(3):
            img = pygame.image.load(f'img/{self.name}/Hurt/{i}.png')
            img = pygame.transform.scale(img, (img.get_width() * 3, img.get_height() * 3))
            temp_list.append(img)
        self.animation_list.append(temp_list)
        #load dead images
        temp_list = []
        for i in range(10):
            img = pygame.image.load(f'img/{self.name}/Death/{i}.png')
            img = pygame.transform.scale(img, (img.get_width() * 3, img.get_height() * 3))
            temp_list.append(img)
        self.animation_list.append(temp_list)
        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)

    def update(self):
        animation_cooldown = 100
        #handle animation
        #update image
        self.image = self.animation_list[self.action][self.frame_index]
        #check if enough time has passed since the last update
        if pygame.time.get_ticks() - self.update_time > animation_cooldown:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
        #if the animation has run out of time reset back to the start
        if self.frame_index >= len(self.animation_list[self.action]):
            if self.action == 3:
                self.frame_index = len(self.animation_list[self.action]) - 1
            else:
                self.idle()

    def idle(self):
        #set variables to idle animation
        self.action = 0
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()

    def attack(self, target):
        #deal damage to enemy
        damage = self.strength + math.floor(random.random() * 7) - 3
        target.hp -= damage
        #run enemy hurt animation
        target.hurt()
        #check if target has died
        if target.hp <= 0:
            target.hp = 0
            target.alive = False
            target.death()
        damage_text = DamageText(target.rect.centerx, target.rect.y, str(damage), red)
        damage_text_group.add(damage_text)
        #set variables to attack animation
        self.action = 1
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()

    def hurt(self):
        #set variables to hurt animation
        self.action = 2
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()

    def death(self):
        #set variables to death animation
        self.action = 3
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()

    def reset(self):
        self.alive = True
        self.potions = self.start_potions
        self.hp = self.max_hp
        self.frame_index = 0
        self.action = 0
        self.update_time = pygame.time.get_ticks()

    def draw(self):
        screen.blit(self.image, self.rect)

#dragon class
class Dragon():
    def __init__(self, x, y, name, max_hp, strength, regen_cooldown):
        self.name = name
        self.start_x = x
        self.start_y = y
        self.max_hp = max_hp
        self.hp = max_hp
        self.strength = strength
        self.alive = True
        self.animation_list = []
        self.frame_index = 0
        self.counter = 0
        self.visible = True
        self.regen_cooldown = regen_cooldown
        self.last_regen = pygame.time.get_ticks()

        #0:idle 1:attack 2:hurt 3:dead
        self.action = 0
        self.update_time = pygame.time.get_ticks()
        #load idle images
        temp_list = []
        for i in range(4):
            img = pygame.image.load(f'img/{self.name}/Idle/{i}.png')
            img = pygame.transform.scale(img, (img.get_width() * 3, img.get_height() * 3))
            temp_list.append(img)
        self.animation_list.append(temp_list)
        #load attack images
        temp_list = []
        for i in range(6):
            img = pygame.image.load(f'img/{self.name}/Attack/{i}.png')
            img = pygame.transform.scale(img, (img.get_width() * 3, img.get_height() * 3))
            temp_list.append(img)
        self.animation_list.append(temp_list)
        #load hurt images
        temp_list = []
        for i in range(2):
            img = pygame.image.load(f'img/{self.name}/Hurt/{i}.png')
            img = pygame.transform.scale(img, (img.get_width() * 3, img.get_height() * 3))
            temp_list.append(img)
        self.animation_list.append(temp_list)
        #load dead images
        temp_list = []
        for i in range(2):
            img = pygame.image.load(f'img/{self.name}/Hurt/{i}.png')
            img = pygame.transform.scale(img, (img.get_width() * 3, img.get_height() * 3))
            temp_list.append(img)
        self.animation_list.append(temp_list)
        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
    
    def update(self):
        animation_cooldown = 200
        if self.alive and self.hp < self.max_hp:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_regen >= self.regen_cooldown:
                self.hp += 1
                self.hp = min(self.hp, self.max_hp)
                self.last_regen = current_time
        #handle animation
        #check if enough time has passed since the last update
        if pygame.time.get_ticks() - self.update_time > animation_cooldown:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
        #if the animation has run out of time reset back to the start
        if self.frame_index >= len(self.animation_list[self.action]):
            self.idle()
        center = self.rect.center
        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = center

    def idle(self):
        #set variables to idle animation
        self.action = 0
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()

    def attack(self, target):
        #deal damage to enemy
        damage = self.strength + math.floor(random.random() * 7) - 3
        target.hp -= damage
        #run enemy hurt animation
        target.hurt()
        #check if target has died
        if target.hp <= 0:
            target.hp = 0
            target.alive = False
            target.death()
        damage_text = DamageText(target.rect.centerx, target.rect.y, str(damage), red)
        damage_text_group.add(damage_text)
        #set variables to attack animation
        self.action = 1
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()

    def hurt(self):
        #set variables to hurt animation
        animation_cooldown = 300
        self.action = 2
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()

    def death(self):
        #set variables to death animation
        animation_cooldown = 300
        self.action = 3
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()

    def reset(self):
        self.alive = True
        self.hp = self.max_hp
        self.rect.center = (self.start_x, self.start_y)
        self.frame_index = 0
        self.visible = True
        self.action = 0
        self.update_time = pygame.time.get_ticks()
    
    def draw(self):
        if not self.visible:
            return 
        offset_x = 0
        if self.action == 1:
            offset_x = -50
        elif self.action == 2:
            offset_x = 10
        elif self.action == 3:
            #move dragon up
            self.rect.x += 13
            #dragon disappears after a few seconds
            self.counter += 1
            if self.counter > 30:
                self.visible = False
                return 
        screen.blit(self.image, (self.rect.x + offset_x, self.rect.y))

#health bar class
class HealthBar():
    def __init__(self, x, y, hp, max_hp):
        self.x = x
        self.y = y
        self.hp = hp
        self.max_hp = max_hp
    
    def draw(self, hp):
        #update with new health
        self.hp = hp
        #calculate health ratio
        ratio = self.hp / self.max_hp
        pygame.draw.rect(screen, red, (self.x, self.y, 150, 20))
        pygame.draw.rect(screen, green, (self.x, self.y, 150 * ratio, 20))

class DamageText(pygame.sprite.Sprite):
    def __init__(self, x, y, damage, colour):
        pygame.sprite.Sprite.__init__(self)
        self.image = font.render(damage, True, colour)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.counter = 0

    def update(self):
        #move damage text up
        self.rect.y -= 1
        #delete the text after a few seconds
        self.counter += 1
        if self.counter > 50:
            self.kill()

damage_text_group = pygame.sprite.Group()

#decide dragon strategy
def get_dragon_strategy():
    total = sum(game_state.player_action_count.values()) or 1
    attack = game_state.player_action_count['attack']/total
    potion = game_state.player_action_count['potion']/total
    if attack > 0.6: return 'defensive'
    if potion > 0.4: return 'aggressive'
    return 'normal'

def init_ml_model():
    try:
        if Path('ai_difficulty_model.h5').exists():
            game_state.model = tf.keras.models.load_model('ai_difficulty_model.h5')
            print("Loaded existing ML model")
        else:
            game_state.model = tf.keras.Sequential([
                tf.keras.layers.Input(shape=(3,)),
                tf.keras.layers.Dense(16, activation='relu'),
                tf.keras.layers.Dense(8, activation='relu'),
                tf.keras.layers.Dense(1, activation='linear')
            ])
            game_state.model.compile(optimizer='adam', loss='mse')
            print("Created new ML model")
    except Exception as e:
        print(f"ML model initialization failed: {e}")
        game_state.model = None

def process_game_data():
    try:
        csv_path = Path('game_stats.csv')
        if not csv_path.exists() or csv_path.stat().st_size == 0:
            return
            
        df = pd.read_csv(csv_path)
        
        # Validate columns
        required_cols = ['accuracy', 'reaction_time', 'turns']
        if not all(col in df.columns for col in required_cols):
            print("Missing required columns in CSV")
            return
            
        # Clean data
        df = df.dropna()
        if len(df) < 5:  # Minimum data points
            return
            
        X = df[required_cols].values
        y = np.clip(
            0.4*X[:,0] + 0.3*(1/X[:,1]) + 0.3*X[:,2], 
            1, 5
        )
        
        if game_state.model:
            # Manual train/validation split (no scikit-learn)
            split_idx = int(0.8 * len(X))
            X_train, y_train = X[:split_idx], y[:split_idx]
            X_val, y_val = X[split_idx:], y[split_idx:]
            
            # Custom training loop
            best_loss = float('inf')
            patience = 5
            patience_counter = 0
            
            for epoch in range(50):
                history = game_state.model.fit(
                    X_train, y_train,
                    validation_data=(X_val, y_val),
                    epochs=1,
                    batch_size=4,
                    verbose=0
                )
                
                # Early stopping implementation
                current_val_loss = history.history['val_loss'][0]
                if current_val_loss < best_loss:
                    best_loss = current_val_loss
                    patience_counter = 0
                else:
                    patience_counter += 1
                    if patience_counter >= patience:
                        print(f"Early stopping at epoch {epoch}")
                        break
            
            # Predict difficulty
            prediction = game_state.model.predict(X[-1:], verbose=0)[0][0]
            game_state.predicted_difficulty = int(np.clip(np.round(prediction), 1, 5))
            
    except Exception as e:
        print(f"Data processing failed: {e}")
    finally:
        print(f"Final difficulty: {game_state.predicted_difficulty}")

init_ml_model()
process_game_data()

selected_theme_name, bg_img = theme_selection()
selected_character_name = character_selection()
selected_difficulty = difficulty_selection()

#background selection
if selected_theme_name != 'Dark forest':
    bg_img = pygame.transform.scale(bg_img, (screen_width, screen_height))

#create fighter with selected name and difficulty
knight = Fighter(
    name = selected_character_name,
    max_hp = selected_difficulty['fighter_max_hp'],
    strength = selected_difficulty['fighter_strength'],
    potions = selected_difficulty['fighter_potions']
)

#create dragon with selected difficulty
dragon = Dragon(
    x = 600,
    y = 275,
    name = 'Dragon',
    max_hp = selected_difficulty['dragon_max_hp'],
    strength = selected_difficulty['dragon_strength'],
    regen_cooldown = selected_difficulty['dragon_regen']
)

knight_health_bar = HealthBar(120, screen_height - bottom_panel + 50, knight.hp, knight.max_hp)
dragon_health_bar = HealthBar(520, screen_height - bottom_panel + 50, dragon.hp, dragon.max_hp)

#create buttons
potion_button = button.Button(screen, 170, screen_height - bottom_panel + 80, potion_img, 50, 50)
restart_button = button.Button(screen, 340, 120, restart_img, 120, 30)

def main_loop():
    global run, clicked, attack, potion, current_fighter, action_cooldown, game_over, summary_shown
    run = True
    while run:
        clock.tick(fps)

        draw_bg()
        draw_panel()
        knight_health_bar.draw(knight.hp)
        dragon_health_bar.draw(dragon.hp)

        #draw fighter
        knight.update()
        knight.draw()

        #draw dragon
        dragon.update()
        dragon.draw()

        #draw the damage text
        damage_text_group.update()
        damage_text_group.draw(screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                clicked = True
            elif event.type == pygame.MOUSEBUTTONUP:
                clicked = False

        #control player actions
        #reset action variables
        attack = False
        potion = False
        target = None 
        #make sure mouse is visible
        pygame.mouse.set_visible(True)
        pos = pygame.mouse.get_pos()
        if dragon.rect.collidepoint(pos):
            #hide mouse
            pygame.mouse.set_visible(False)
            #show sword in place of mouse cursor
            screen.blit(sword_img, pos)
            if clicked == True and dragon.alive == True:
                attack = True
                target = dragon
        if potion_button.draw():
            potion = True

        # Count player's choices for AI tracking
        if attack:
            game_state.player_action_count["attack"] += 1
        if potion:
            game_state.player_action_count["potion"] += 1

        #show number of potions remaining
        draw_text(str(knight.potions), 'Times New Roman', 16, (0, 0, 0), 192, screen_height - bottom_panel + 103)

        if game_over == 0:
            #player action
            if knight.alive == True:
                if current_fighter == 1:
                    action_cooldown += 1
                    if action_cooldown == 1:
                        turn_start_time = pygame.time.get_ticks()
                    if action_cooldown >= game_state.action_wait_time:
                        #look for player action
                        #attack
                        if attack == True and target != None:
                            reaction_time += pygame.time.get_ticks() - turn_start_time
                            turn_count += 1
                            knight.attack(target)
                            current_fighter += 1
                            action_cooldown = 0
                        #potion
                        if potion == True:
                            if knight.potions > 0:
                                reaction_time += pygame.time.get_ticks() - turn_start_time
                                turn_count += 1
                                #check if the potion would heal the player beyond max health
                                if knight.max_hp - knight.hp > game_state.potion_effect:
                                    heal_amount = game_state.potion_effect
                                else:
                                    heal_amount = knight.max_hp - knight.hp
                                knight.hp += heal_amount
                                knight.potions -= 1
                                damage_text = DamageText(knight.rect.centerx, knight.rect.y, str(heal_amount), green)
                                damage_text_group.add(damage_text)
                                current_fighter += 1
                                action_cooldown = 0
            else:
                game_over = -1

            #enemy action
            if current_fighter == 2:
                if dragon.alive == True:
                    action_cooldown += 1
                    if action_cooldown >= game_state.action_wait_time:
                        strategy = get_dragon_strategy()
                        if strategy == "defensive":
                            dragon.attack(knight)
                            knight.hp += 3
                            damage_text_group.add(DamageText(knight.rect.centerx, knight.rect.y, "-3 DR", silver))
                        elif strategy == "aggressive":
                            dragon.attack(knight)
                            knight.hp -= 3 # simulate bonus damage
                            damage_text_group.add(DamageText(knight.rect.centerx, knight.rect.y, "+3 DMG", red))
                        else:
                            dragon.attack(knight)
                        current_fighter += 1
                        action_cooldown = 0
                else:
                    current_fighter += 1
            
            #if all fighters have had a turn then reset
            if current_fighter > game_state.total_fighters:
                current_fighter = 1
                player_action_count = {"attack": 0, "potion": 0}

        #check if dragon is dead
        if dragon.alive == False:
            game_over = 1

        #check if game is over
        if game_over != 0 and not summary_shown:
            #save performance after battle ends
            total_actions = sum(player_action_count.values()) or 1
            accuracy = player_action_count['attack'] / total_actions
            avg_reaction = reaction_time / turn_count if turn_count else 0
            game_state.performance_data.append([accuracy, avg_reaction, turn_count])
            df = pd.DataFrame(game_state.performance_data, columns=['accuracy', 'reaction_time', 'turns'])
            df.to_csv('game_stats.csv', index=False)
            game_state.performance_data.clear()
            print(f"Game summary: accuracy={accuracy:.2f}, avg_reaction={avg_reaction:.0f}ms, turns={turn_count}")
            summary_shown = True

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                clicked = True
            elif event.type == pygame.MOUSEBUTTONUP:
                clicked = False

        if game_over != 0:
            if game_over == 1:
                screen.blit(victory_img, (260, 50))
            if game_over == -1:
                screen.blit(defeat_img, (280, 50))
            if restart_button.draw():
                knight.reset()
                dragon.reset()
                current_fighter = 1
                action_cooldown = 0
                game_over = 0
                summary_shown = False

        pygame.display.update()
                
    pygame.quit()