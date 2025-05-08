import pygame
import random

# 游戏窗口大小
WIDTH, HEIGHT = 300, 600
BLOCK_SIZE = 30
GAME_WIDTH = WIDTH // BLOCK_SIZE
GAME_HEIGHT = HEIGHT // BLOCK_SIZE

# 定义颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)

COLORS = [CYAN, BLUE, ORANGE, YELLOW, GREEN, RED, MAGENTA]

# 定义俄罗斯方块形状
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 1], [1, 1]],  # O
    [[0, 1, 0], [1, 1, 1]],  # T
    [[1, 1, 0], [0, 1, 1]],  # S
    [[0, 1, 1], [1, 1, 0]],  # Z
    [[1, 0, 0], [1, 1, 1]],  # L
    [[0, 0, 1], [1, 1, 1]],  # J
]

# 游戏主类
class Tetris:
    def __init__(self):
        self.width = GAME_WIDTH
        self.height = GAME_HEIGHT
        self.board = [[0 for _ in range(self.width)] for _ in range(self.height)]
        self.game_over = False
        self.current_piece = None
        self.next_piece = self.random_piece()
        self.score = 0

    def random_piece(self):
        shape = random.choice(SHAPES)
        color = COLORS[SHAPES.index(shape)]
        return {'shape': shape, 'color': color, 'x': GAME_WIDTH // 2 - len(shape[0]) // 2, 'y': 0}

    def rotate(self):
        shape = self.current_piece['shape']
        self.current_piece['shape'] = [list(row) for row in zip(*shape[::-1])]

    def check_collision(self):
        for i, row in enumerate(self.current_piece['shape']):
            for j, cell in enumerate(row):
                if cell and (self.current_piece['y'] + i >= self.height or
                             self.current_piece['x'] + j < 0 or
                             self.current_piece['x'] + j >= self.width or
                             self.board[self.current_piece['y'] + i][self.current_piece['x'] + j]):
                    return True
        return False

    def place_piece(self):
        for i, row in enumerate(self.current_piece['shape']):
            for j, cell in enumerate(row):
                if cell:
                    self.board[self.current_piece['y'] + i][self.current_piece['x'] + j] = COLORS.index(self.current_piece['color']) + 1
        self.clear_lines()
        self.current_piece = self.next_piece
        self.next_piece = self.random_piece()
        if self.check_collision():
            self.game_over = True

    def clear_lines(self):
        full_lines = [i for i, row in enumerate(self.board) if all(cell != 0 for cell in row)]
        for i in full_lines:
            del self.board[i]
            self.board.insert(0, [0] * self.width)
        self.score += len(full_lines)

    def move(self, dx, dy):
        self.current_piece['x'] += dx
        self.current_piece['y'] += dy
        if self.check_collision():
            self.current_piece['x'] -= dx
            self.current_piece['y'] -= dy
            return False
        return True

    def draw(self, screen):
        screen.fill(BLACK)
        for y in range(self.height):
            for x in range(self.width):
                color = self.board[y][x]
                if color:
                    pygame.draw.rect(screen, COLORS[color - 1], (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))
        for i, row in enumerate(self.current_piece['shape']):
            for j, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(screen, self.current_piece['color'],
                                     ((self.current_piece['x'] + j) * BLOCK_SIZE, (self.current_piece['y'] + i) * BLOCK_SIZE,
                                      BLOCK_SIZE, BLOCK_SIZE))
        self.draw_score(screen)

    def draw_score(self, screen):
        font = pygame.font.SysFont('Arial', 24)
        score_text = font.render(f'Score: {self.score}', True, WHITE)
        screen.blit(score_text, (10, 10))

# 主函数
def run_game():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('Tetris')

    clock = pygame.time.Clock()
    game = Tetris()
    game.current_piece = game.random_piece()

    while not game.game_over:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.game_over = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    game.move(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    game.move(1, 0)
                elif event.key == pygame.K_DOWN:
                    game.move(0, 1)
                elif event.key == pygame.K_UP:
                    game.rotate()

        if not game.move(0, 1):
            game.place_piece()

        game.draw(screen)
        pygame.display.update()

        # 调整游戏下落速度
        clock.tick(5)  # 将 10 改为 5，降低下坠速度

    pygame.quit()

if __name__ == '__main__':
    run_game()
