import pygame
import sys
from pygame.locals import *
import socket
import threading
import re
import time
# 初始化
pygame.init()

# 常量定义
BOARD_SIZE = 15  # 15x15的棋盘
GRID_SIZE = 40   # 每个格子的像素大小
PIECE_RADIUS = 15  # 棋子半径
MARGIN = 50      # 棋盘边距
WINDOW_WIDTH = BOARD_SIZE * GRID_SIZE + 2 * MARGIN  # 窗口宽度
WINDOW_HEIGHT = BOARD_SIZE * GRID_SIZE + 2 * MARGIN + 80  # 窗口高度(增加底部状态栏空间)
positions=[]

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BOARD_COLOR = (220, 179, 92)  # 棋盘颜色
LINE_COLOR = (0, 0, 0)        # 棋盘线颜色
HIGHLIGHT_COLOR = (255, 0, 0)  # 高亮颜色
TEXT_COLOR = (50, 50, 50)      # 文本颜色
COORD_COLOR = (100, 100, 100)  # 坐标颜色
STATUS_BAR_COLOR = (240, 240, 240)  # 状态栏背景色
HOVER_COLOR = (200, 200, 200, 100)  # 鼠标悬停半透明效果

# 创建窗口
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('五子棋')

# 字体
font_large = pygame.font.Font(None, 48)  # 大字体用于胜利提示
font_medium = pygame.font.Font(None, 36)  # 中字体用于状态显示
font_small = pygame.font.Font(None, 24)  # 小字体用于坐标
font_coord = pygame.font.Font(None, 20)  # 更小的字体用于鼠标坐标

# 游戏状态
board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]  # 0=空, 1=黑, 2=白
current_player = 1  # 1为黑棋, 2为白棋
game_over = False
winner = None
last_move = None  # 记录最后一步棋
hover_pos = None  # 鼠标悬停位置

def draw_board():
    """绘制棋盘和坐标"""
    screen.fill(BOARD_COLOR)
    
    # 绘制坐标标记 (A-O)
    for i in range(BOARD_SIZE):
        # 横坐标 (A-O)
        char = chr(ord('A') + i)
        text = font_small.render(char, True, COORD_COLOR)
        screen.blit(text, (MARGIN + i * GRID_SIZE - 5, MARGIN - 30))
        
        
        # 纵坐标 (1-15)
        num = str(i+1)
        text = font_small.render(num, True, COORD_COLOR)
        screen.blit(text, (MARGIN - 30, MARGIN + i * GRID_SIZE - 8))
        
    
    # 绘制网格线
    for i in range(BOARD_SIZE):
        # 横线
        pygame.draw.line(screen, LINE_COLOR, 
                        (MARGIN, MARGIN + i * GRID_SIZE), 
                        (WINDOW_WIDTH - MARGIN-40, MARGIN + i * GRID_SIZE),2)
        # 竖线
        pygame.draw.line(screen, LINE_COLOR, 
                        (MARGIN + i * GRID_SIZE, MARGIN), 
                        (MARGIN + i * GRID_SIZE, WINDOW_HEIGHT - MARGIN - 120), 2)
    
    # 绘制五个小黑点(天元、星位)
    dots = [(3, 3), (3, 11), (7, 7), (11, 3), (11, 11)]
    for dot in dots:
        pygame.draw.circle(screen, BLACK, 
                         (MARGIN + dot[0] * GRID_SIZE, MARGIN + dot[1] * GRID_SIZE), 5)

def draw_pieces():
    """绘制棋子"""
    for y in range(BOARD_SIZE):
        for x in range(BOARD_SIZE):
            if board[y][x] == 1:  # 黑棋
                pygame.draw.circle(screen, BLACK, 
                                 (MARGIN + x * GRID_SIZE, MARGIN + y * GRID_SIZE), 
                                 PIECE_RADIUS)
            elif board[y][x] == 2:  # 白棋
                pygame.draw.circle(screen, WHITE, 
                                 (MARGIN + x * GRID_SIZE, MARGIN + y * GRID_SIZE), 
                                 PIECE_RADIUS)
    
    # 高亮显示最后一步棋
    if last_move:
        x, y = last_move
        pygame.draw.circle(screen, HIGHLIGHT_COLOR, 
                         (MARGIN + x * GRID_SIZE, MARGIN + y * GRID_SIZE), 
                         PIECE_RADIUS // 2, 2)
    
    # 绘制鼠标悬停位置的半透明效果和坐标
    if hover_pos and not game_over:
        x, y = hover_pos

        # 始终绘制坐标（不管是否可落子）
        coord_text = f"{chr(ord('A') + x)}{y+1}"
        coord_surface = font_coord.render(coord_text, True, BLACK)
        coord_rect = coord_surface.get_rect(center=(MARGIN + x * GRID_SIZE, MARGIN + y * GRID_SIZE - 20))

        # 坐标背景
        bg_surface = pygame.Surface((coord_rect.width + 4, coord_rect.height + 4), pygame.SRCALPHA)
        bg_surface.fill((255, 255, 255, 200))
        screen.blit(bg_surface, (coord_rect.x - 2, coord_rect.y - 2))
        screen.blit(coord_surface, coord_rect)

        # 如果当前位置还没落子，就显示半透明悬停效果
        if 0 <= x < 15 and 0 <= y < 15:
            if board[y][x] == 0:
                s = pygame.Surface((PIECE_RADIUS*2, PIECE_RADIUS*2), pygame.SRCALPHA)
                pygame.draw.circle(s, HOVER_COLOR, (PIECE_RADIUS, PIECE_RADIUS), PIECE_RADIUS)
                screen.blit(s, (MARGIN + x * GRID_SIZE - PIECE_RADIUS,
                                MARGIN + y * GRID_SIZE - PIECE_RADIUS))


def draw_game_status():
    """绘制游戏状态"""
    # 状态栏背景
    pygame.draw.rect(screen, STATUS_BAR_COLOR, (0, WINDOW_HEIGHT - 80, WINDOW_WIDTH, 80))
    
    # 显示当前玩家
    status_text = f"Current: {'Black' if current_player == 1 else 'White'}"
    text_surface = font_medium.render(status_text, True, TEXT_COLOR)
    screen.blit(text_surface, (20, WINDOW_HEIGHT - 70))
    
    # 显示最后一步棋的坐标
    if last_move:
        x, y = last_move
        coord_text = f"Last move: {chr(ord('A') + x)}{y+1}"
        coord_surface = font_small.render(coord_text, True, TEXT_COLOR)
        screen.blit(coord_surface, (20, WINDOW_HEIGHT - 40))
    
    

   

    # 胜利提示
    if game_over:
        if winner:
            text = f"{'Black' if winner == 1 else 'White'} Wins!"
            color = BLACK if winner == 1 else (100, 100, 100)
        else:
            text = "Draw!"
            color = TEXT_COLOR
        
        # 创建半透明背景
        text_surface = font_large.render(text, True, color)
        text_rect = text_surface.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2))
        
        bg_rect = text_rect.inflate(40, 20)
        s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        s.fill((220, 179, 92, 200))  # 半透明棋盘色
        screen.blit(s, bg_rect)
        
        # 绘制边框
        pygame.draw.rect(screen, color, bg_rect, 2)
        screen.blit(text_surface, text_rect)
        
        # 添加重新开始提示
        restart_text = font_small.render("Click anywhere to restart", True, TEXT_COLOR)
        screen.blit(restart_text, (WINDOW_WIDTH//2 - restart_text.get_width()//2, 
                                  WINDOW_HEIGHT//2 + 50))
    if hover_pos:
        x, y = hover_pos
        hover_text = f"Hover: {chr(ord('A') + x)}{y+1}"
        hover_surface = font_small.render(hover_text, True, TEXT_COLOR)
        screen.blit(hover_surface, (WINDOW_WIDTH - 150, WINDOW_HEIGHT - 40))


def get_board_position(mouse_pos):
    """将鼠标位置转换为棋盘坐标"""
    x, y = mouse_pos
    # 检查是否在棋盘内
    if (MARGIN <= x < WINDOW_WIDTH - MARGIN and 
        MARGIN <= y < WINDOW_HEIGHT - MARGIN - 50):
        board_x = round((x - MARGIN) / GRID_SIZE)
        board_y = round((y - MARGIN) / GRID_SIZE)
        return board_x, board_y
    return None

def is_valid_move(x, y):
    """检查落子是否有效"""
    return 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE and board[y][x] == 0

def make_move(x, y, player):
    """落子"""
    global board, last_move, current_player
    if is_valid_move(x, y):
        board[y][x] = player
        last_move = (x, y)
        current_player = 3 - player  # 切换玩家(1<->2)
        return True
    return False

def check_win(x, y):
    """检查是否获胜"""
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]  # 横、竖、斜、反斜
    player = board[y][x]
    
    for dx, dy in directions:
        count = 1  # 当前棋子
        
        # 正向检查
        nx, ny = x + dx, y + dy
        while 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and board[ny][nx] == player:
            count += 1
            nx += dx
            ny += dy
        
        # 反向检查
        nx, ny = x - dx, y - dy
        while 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and board[ny][nx] == player:
            count += 1
            nx -= dx
            ny -= dy
        
        if count >= 5:
            return True
    
    return False

def check_draw():
    """检查平局"""
    for row in board:
        if 0 in row:
            return False
    return True

def restart_game():
    """重新开始游戏"""
    global board, current_player, game_over, winner, last_move
    board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    current_player = 1
    game_over = False
    winner = None
    last_move = None

def pos_from_label(label):
    col = ord(label[0].upper()) - ord('A')  # 不跳过 'I'，A=0, B=1, ..., I=8, ..., O=14
    row = int(label[1:]) - 1                # 将'5'转换为4（从0开始）
    
    if 0 <= col < 15 and 0 <= row < 15:
        CELL_SIZE = WINDOW_WIDTH // BOARD_SIZE
        B_SIZE= WINDOW_HEIGHT // BOARD_SIZE
        return CELL_SIZE + col * CELL_SIZE, B_SIZE + row * B_SIZE
    return None
def socket_listener():
    """
    游戏服务器Socket监听线程
    处理客户端发送的棋子坐标（如"A1", "B2"等格式）
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 允许地址重用
        s.bind(('127.0.0.1', 50002))
        s.listen(1)
        print("[游戏服务器] 等待客户端连接...")
        
        while True:  # 持续接受新连接
            conn, addr = None, None
            try:
                conn, addr = s.accept()
                print(f"[游戏服务器] 客户端 {addr} 已连接")
                
                with conn:
                    while True:
                        try:
                            # 接收数据
                            data = conn.recv(1024)
                            if not data:
                                print(f"[游戏服务器] 客户端 {addr} 断开连接")
                                break
                            
                            move = data.decode().strip().upper()  # 转为大写
                            print(f"[游戏服务器] 收到坐标: {move}")
                            
                            # 验证坐标格式
                            from re import match
                            # 正则表达式检查坐标格式（A1, B15等）
                            if not re.match(r'^[A-O](?:[1-9]|1[0-5])$', move):
                                conn.sendall(b"ERROR: Invalid format (e.g. A1, B15)")
                                continue
                            
                            # 转换坐标
                            try:
                                col = ord(move[0]) - ord('A')  # A=0, B=1,...,O=14
                                row = int(move[1:]) - 1        # "1"->0, "15"->14
                            except ValueError:
                                conn.sendall(b"ERROR: Invalid coordinate")
                                continue
                            
                            # 检查是否游戏结束
                            if game_over:
                                conn.sendall(b"ERROR: Game already over")
                                continue
                                
                            # 尝试落子
                            if make_move(col, row, current_player):
                                # 检查游戏状态
                                if check_win(col, row):
                                    conn.sendall(b"WIN")
                                elif check_draw():
                                    conn.sendall(b"DRAW")
                                else:
                                    conn.sendall(b"OK")
                            else:
                                conn.sendall(b"ERROR: Invalid move")
                                
                        except ConnectionResetError:
                            print(f"[游戏服务器] 客户端 {addr} 异常断开")
                            break
                        except Exception as e:
                            print(f"[游戏服务器] 处理错误: {str(e)}")
                            conn.sendall(f"ERROR: {str(e)}".encode())
                            break
                            
            except KeyboardInterrupt:
                print("[游戏服务器] 服务器关闭")
                break
            except Exception as e:
                print(f"[游戏服务器] 服务器错误: {str(e)}")
                if conn:
                    conn.close()
            finally:
                if conn:
                    conn.close()

def main():
    global current_player, game_over, winner, hover_pos
    pygame.init()
    running = True
    while running:
        pygame.display.flip()
        hover_pos = None  # 重置悬停位置
        
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            
            elif event.type == MOUSEMOTION:  # 鼠标移动事件
                board_pos = get_board_position(event.pos)
                if board_pos:
                    hover_pos = board_pos
            
            elif event.type == MOUSEBUTTONDOWN and event.button == 1:  # 左键点击
                if game_over:
                    restart_game()
                    continue
                
                board_pos = get_board_position(event.pos)
                if board_pos:
                    x, y = board_pos
                    if make_move(x, y, current_player):
                        # 检查游戏是否结束
                        if check_win(x, y):
                            game_over = True
                            winner = current_player
                        elif check_draw():
                            game_over = True
                            winner = None
        draw_board()
        draw_pieces()
        draw_game_status()
        
        pygame.display.flip()
        pygame.time.delay(60)  # 控制帧率
    pygame.quit()


        
        
        # 绘制


if __name__ == "__main__":
    network_thread = threading.Thread(target=socket_listener, daemon=True)
    network_thread.start()
    main()