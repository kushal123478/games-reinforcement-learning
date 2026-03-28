"""
Pygame visual renderer for Halite.
Click ships to select, use arrow keys / WASD to move.
Press Enter to end your turn (AI plays automatically).
"""

import sys
import pygame
from typing import Optional, Tuple, Dict
from halite.game_engine import HaliteGame, Direction

# ── Colors ──────────────────────────────────────────────────────────────────
DARK_BG       = (15, 15, 30)
GRID_COLOR    = (28, 38, 65)
PLAYER_0_COL  = (68, 136, 255)   # blue  – human
PLAYER_1_COL  = (255, 68,  68)   # red   – AI
SELECTED_COL  = (255, 240,  80)   # yellow highlight
MOVED_COL     = (80,  90, 130)   # dim – already moved
UI_BG         = (18, 18, 42)
UI_TEXT       = (210, 215, 255)
UI_ACCENT     = (100, 185, 255)
UI_DIM        = (130, 135, 165)


def _halite_color(amount: int) -> Tuple[int, int, int]:
    """Map 0-500 halite to a colour: dark→green→yellow→gold."""
    t = min(amount / 500.0, 1.0)
    if t < 0.25:
        s = t / 0.25
        return (int(10 + s * 15), int(20 + s * 55), int(10 + s * 10))
    elif t < 0.6:
        s = (t - 0.25) / 0.35
        return (int(25 + s * 160), int(75 + s * 105), int(20 - s * 10))
    else:
        s = (t - 0.6) / 0.4
        return (int(185 + s * 70), int(180 + s * 35), int(10 + s * 5))


# Pre-build colour palette for fast lookup
_HALITE_PALETTE = [_halite_color(i) for i in range(501)]


# ── Simple AI ───────────────────────────────────────────────────────────────
class SimpleAI:
    """Greedy AI: collect nearby halite, return when full."""

    def __init__(self, game: HaliteGame, player_id: int):
        self.game = game
        self.player_id = player_id

    # ---- public interface --------------------------------------------------
    def take_turn(self):
        moves = self._get_moves()
        for ship_id, direction in moves.items():
            self.game.process_move(self.player_id, ship_id, direction)
        if self._should_spawn():
            self.game._spawn_ship(self.player_id)

    # ---- internals --------------------------------------------------------
    def _get_moves(self) -> Dict[str, Direction]:
        player = self.game.players[self.player_id]
        return {sid: self._plan(ship) for sid, ship in player.ships.items()}

    def _plan(self, ship) -> Direction:
        player = self.game.players[self.player_id]
        if ship.halite > 280:
            nearest = min(player.dropoffs, key=lambda d: self._dist(ship.x, ship.y, d[0], d[1]))
            return self._toward(ship.x, ship.y, nearest[0], nearest[1])
        cell = self._best_halite(ship.x, ship.y)
        if cell:
            return self._toward(ship.x, ship.y, cell[0], cell[1])
        return Direction.STAY

    def _dist(self, x1, y1, x2, y2) -> int:
        bs = self.game.board_size
        dx = abs(x1 - x2); dx = min(dx, bs - dx)
        dy = abs(y1 - y2); dy = min(dy, bs - dy)
        return dx + dy

    def _toward(self, x, y, tx, ty) -> Direction:
        bs = self.game.board_size
        dx = (tx - x + bs) % bs
        dy = (ty - y + bs) % bs
        if dx > bs // 2: dx -= bs
        if dy > bs // 2: dy -= bs
        if abs(dx) >= abs(dy):
            return Direction.EAST if dx > 0 else Direction.WEST
        return Direction.SOUTH if dy > 0 else Direction.NORTH

    def _best_halite(self, x, y) -> Optional[Tuple[int, int]]:
        best, best_val = None, 40
        bs = self.game.board_size
        for dy in range(-6, 7):
            for dx in range(-6, 7):
                cx, cy = (x + dx) % bs, (y + dy) % bs
                v = self.game.halite_board[cy, cx]
                if v > best_val:
                    best_val, best = v, (cx, cy)
        return best

    def _should_spawn(self) -> bool:
        p = self.game.players[self.player_id]
        return p.halite >= self.game.config['spawn_cost'] * 2 and len(p.ships) < 5


# ── Main visual game ─────────────────────────────────────────────────────────
CELL   = 36          # px per board cell
PAD    = 18          # board padding
INFO_W = 290         # right-panel width
HDR_H  = 58          # header height


class HalitePygame:
    def __init__(self, board_size: int = 16, seed: Optional[int] = None):
        self._init_size = board_size
        self._init_seed = seed
        self._setup(board_size, seed)

    def _setup(self, board_size: int, seed: Optional[int]):
        self.board_size = board_size
        self.game = HaliteGame(board_size=board_size, num_players=2, seed=seed)
        self.ai    = SimpleAI(self.game, player_id=1)

        self.board_px = board_size * CELL
        self.width    = self.board_px + PAD * 2 + INFO_W
        self.height   = self.board_px + PAD * 2 + HDR_H

        self.selected: Optional[str] = None   # selected ship id
        self.moved:    set           = set()  # ships that moved this turn
        self.player_id               = 0
        self.message                 = "Tab to cycle ships  |  Arrow keys / WASD to move  |  Enter to end turn"
        self.over                    = False
        self.over_msg                = ""

    # ── coordinate helpers ──────────────────────────────────────────────────
    def _b2s(self, x: int, y: int) -> Tuple[int, int]:
        """Board → screen pixel (top-left of cell)."""
        return PAD + x * CELL, HDR_H + PAD + y * CELL

    def _s2b(self, px: int, py: int) -> Optional[Tuple[int, int]]:
        """Screen pixel → board cell, or None if outside board."""
        bx = px - PAD
        by = py - HDR_H - PAD
        if 0 <= bx < self.board_px and 0 <= by < self.board_px:
            return bx // CELL, by // CELL
        return None

    # ── drawing ─────────────────────────────────────────────────────────────
    def _draw_board(self):
        for y in range(self.board_size):
            for x in range(self.board_size):
                h   = int(self.game.halite_board[y, x])
                col = _HALITE_PALETTE[min(h, 500)]
                sx, sy = self._b2s(x, y)
                pygame.draw.rect(self.screen, col,       (sx, sy, CELL, CELL))
                pygame.draw.rect(self.screen, GRID_COLOR,(sx, sy, CELL, CELL), 1)

    def _draw_dropoffs(self):
        for pid, player in self.game.players.items():
            col = PLAYER_0_COL if pid == 0 else PLAYER_1_COL
            for i, (dx, dy) in enumerate(player.dropoffs):
                sx, sy = self._b2s(dx, dy)
                cx, cy = sx + CELL // 2, sy + CELL // 2
                r      = CELL // 2 - 2
                pts    = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
                pygame.draw.polygon(self.screen, col,           pts)
                pygame.draw.polygon(self.screen, (255,255,255), pts, 2)
                tag = "D" if i == 0 else "d"   # lowercase = converted dropoff
                lbl = self.fnt_sm.render(tag, True, (255, 255, 255))
                self.screen.blit(lbl, (cx - lbl.get_width()//2, cy - lbl.get_height()//2))

    def _draw_ships(self):
        for pid, player in self.game.players.items():
            base = PLAYER_0_COL if pid == 0 else PLAYER_1_COL
            for sid, ship in player.ships.items():
                sx, sy = self._b2s(ship.x, ship.y)
                cx, cy = sx + CELL // 2, sy + CELL // 2
                r      = CELL // 2 - 4

                if sid == self.selected:
                    pygame.draw.circle(self.screen, SELECTED_COL, (cx, cy), r + 5)

                col = MOVED_COL if (pid == 0 and sid in self.moved) else base
                pygame.draw.circle(self.screen, col,           (cx, cy), r)
                pygame.draw.circle(self.screen, (255,255,255), (cx, cy), r, 2)

                if ship.halite > 0:
                    lbl = self.fnt_sm.render(str(ship.halite), True, (255, 255, 200))
                    self.screen.blit(lbl,
                        (cx - lbl.get_width()//2, cy - lbl.get_height()//2))

    def _draw_header(self):
        pygame.draw.rect(self.screen, (8, 8, 22), (0, 0, self.width, HDR_H - 2))
        scores = self.game.get_scores()

        turn = self.fnt_lg.render(f"Turn {self.game.turn}/{self.game.max_turns}", True, UI_TEXT)
        self.screen.blit(turn, (14, 8))

        p0 = self.fnt_lg.render(f"You: {scores[0]:,}", True, PLAYER_0_COL)
        p1 = self.fnt_lg.render(f"AI:  {scores[1]:,}", True, PLAYER_1_COL)
        mid = self.board_px // 2 + PAD
        self.screen.blit(p0, (mid - 130, 8))
        self.screen.blit(p1, (mid + 20,  8))

        msg = self.fnt_sm.render(self.message[:80], True, (170, 175, 210))
        self.screen.blit(msg, (14, 36))

    def _draw_info(self):
        px = self.board_px + PAD * 2
        pygame.draw.rect(self.screen, UI_BG, (px, 0, INFO_W, self.height))

        y = HDR_H + 8
        lpad = px + 10

        def line(text, color=UI_TEXT, bold=False):
            nonlocal y
            f   = self.fnt_lg if bold else self.fnt_md
            s   = f.render(text, True, color)
            self.screen.blit(s, (lpad, y))
            y  += s.get_height() + 3

        def gap(n=6):
            nonlocal y
            y += n

        player = self.game.players[self.player_id]

        line("YOUR SHIPS", UI_ACCENT, bold=True)
        gap(2)
        for sid, ship in player.ships.items():
            moved = sid in self.moved
            sel   = sid == self.selected
            col   = SELECTED_COL if sel else (MOVED_COL if moved else UI_TEXT)
            tag   = " ✓" if moved else (" ←" if sel else "")
            line(f"  {sid}: ({ship.x},{ship.y}) {ship.halite}h{tag}", col)

        gap()
        line("CONTROLS", UI_ACCENT, bold=True)
        gap(2)
        for key, desc in [
            ("Tab",         "Next ship"),
            ("Shift+Tab",   "Prev ship"),
            ("↑↓←→ / WASD", "Move ship"),
            ("Space",       "Stay & collect"),
            ("C",           "Convert → dropoff"),
            ("N",           "Spawn ship (500h)"),
            ("Enter",       "End your turn"),
            ("R",           "New game"),
            ("Q / Esc",     "Quit"),
        ]:
            line(f"  {key:<14} {desc}", UI_DIM)

        gap()
        line("LEGEND", UI_ACCENT, bold=True)
        gap(2)
        line("  Cell colour = halite amount", UI_DIM)
        line("  D = dropoff point", UI_DIM)
        line("  Number on ship = cargo", UI_DIM)

        if self.selected and self.selected in player.ships:
            gap()
            line("SELECTED", UI_ACCENT, bold=True)
            gap(2)
            ship = player.ships[self.selected]
            bs   = self.game.board_size
            nearest_d = min(player.dropoffs,
                key=lambda d: min(abs(ship.x-d[0]), bs-abs(ship.x-d[0]))
                            + min(abs(ship.y-d[1]), bs-abs(ship.y-d[1])))
            dist = (min(abs(ship.x-nearest_d[0]), bs-abs(ship.x-nearest_d[0]))
                  + min(abs(ship.y-nearest_d[1]), bs-abs(ship.y-nearest_d[1])))
            cell_h = int(self.game.halite_board[ship.y, ship.x])
            line(f"  {self.selected} @ ({ship.x},{ship.y})")
            line(f"  Cargo:    {ship.halite} halite")
            line(f"  Cell:     {cell_h} halite")
            line(f"  To base:  {dist} steps")
            line(f"  Dropoffs: {len(player.dropoffs)}")

        gap()
        can_spawn = player.halite >= self.game.config['spawn_cost']
        sc = (80, 210, 80) if can_spawn else (190, 70, 70)
        line(f"  Bank: {player.halite:,} halite", sc)
        line(f"  Spawn cost: {self.game.config['spawn_cost']}", sc)

    def _draw_game_over(self):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        scores = self.game.get_scores()
        if scores[0] > scores[1]:
            msg, col = "YOU WIN!", PLAYER_0_COL
        elif scores[1] > scores[0]:
            msg, col = "AI WINS!", PLAYER_1_COL
        else:
            msg, col = "TIE GAME!", (255, 255, 80)

        big = pygame.font.SysFont('monospace', 52, bold=True)
        t   = big.render(msg, True, col)
        cx  = self.width // 2
        cy  = self.height // 2
        self.screen.blit(t, (cx - t.get_width()//2, cy - 80))

        med = pygame.font.SysFont('monospace', 22)
        s0  = med.render(f"You:  {scores[0]:,} halite", True, PLAYER_0_COL)
        s1  = med.render(f"AI:   {scores[1]:,} halite", True, PLAYER_1_COL)
        sub = med.render("Press R to play again  |  Q to quit", True, (200,200,200))
        self.screen.blit(s0,  (cx - s0.get_width()//2,  cy - 20))
        self.screen.blit(s1,  (cx - s1.get_width()//2,  cy + 12))
        self.screen.blit(sub, (cx - sub.get_width()//2, cy + 60))

    # ── game logic ───────────────────────────────────────────────────────────
    def _move(self, direction: Direction):
        if not self.selected:
            self.message = "No ship selected — click one first!"
            return
        if self.selected in self.moved:
            self.message = f"Ship {self.selected} already moved this turn."
            return
        res = self.game.process_move(self.player_id, self.selected, direction)
        if res['success']:
            self.moved.add(self.selected)
            parts = []
            if res['collected'] > 0: parts.append(f"+{res['collected']} collected")
            if res['deposited'] > 0: parts.append(f"+{res['deposited']} deposited")
            self.message = (f"Moved {self.selected} {direction.name}"
                            + (f"  ({', '.join(parts)})" if parts else ""))
            # auto-advance to next unmoved ship
            player = self.game.players[self.player_id]
            for sid in player.ships:
                if sid not in self.moved:
                    self.selected = sid
                    break
        else:
            self.message = f"Move failed: {res.get('reason', '?')}"

    def _spawn(self):
        player = self.game.players[self.player_id]
        cost   = self.game.config['spawn_cost']
        if player.halite < cost:
            self.message = f"Need {cost} halite to spawn (have {player.halite})."
            return
        new_id = self.game._spawn_ship(self.player_id)
        self.message = f"Spawned {new_id}!"

    def _convert(self):
        if not self.selected:
            self.message = "No ship selected — press Tab to select one."
            return
        cost = self.game.config['convert_cost']
        player = self.game.players[self.player_id]
        if player.halite < cost:
            self.message = f"Need {cost} halite to convert (have {player.halite})."
            return
        result = self.game.convert_ship(self.player_id, self.selected)
        if result:
            self.moved.discard(self.selected)
            self.selected = None
            self._auto_select()
            self.message = f"Ship converted to dropoff at {result}! (cost {cost}h)"
        else:
            self.message = "Cannot convert here — already a dropoff at this cell."

    def _end_turn(self):
        self.ai.take_turn()
        self.game.step()
        self.moved.clear()
        self._auto_select()

        if self.game.game_over():
            self.over = True
            s = self.game.get_scores()
            if s[0] > s[1]:
                self.message = f"GAME OVER — You WIN!  {s[0]:,} vs {s[1]:,}"
            elif s[1] > s[0]:
                self.message = f"GAME OVER — AI wins.  {s[0]:,} vs {s[1]:,}"
            else:
                self.message = f"GAME OVER — TIE!  {s[0]:,} each"
        else:
            self.message = "Your turn — move ships, then press Enter"

    def _cycle_ship(self, reverse: bool = False):
        """Cycle selection through available ships (Tab / Shift+Tab)."""
        player = self.game.players[self.player_id]
        ids = list(player.ships.keys())
        if not ids:
            return
        if self.selected not in ids:
            self.selected = ids[0]
        else:
            idx = ids.index(self.selected)
            idx = (idx + (-1 if reverse else 1)) % len(ids)
            self.selected = ids[idx]
        ship = player.ships[self.selected]
        self.message = f"Selected {self.selected}  ({ship.x},{ship.y})  cargo: {ship.halite}"

    def _auto_select(self):
        """Select first unmoved ship, or first ship if all moved."""
        player = self.game.players[self.player_id]
        ids = list(player.ships.keys())
        for sid in ids:
            if sid not in self.moved:
                self.selected = sid
                return
        self.selected = ids[0] if ids else None

    # ── main loop ────────────────────────────────────────────────────────────
    def run(self):
        pygame.init()
        pygame.font.init()

        self.screen   = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Halite — Collect the Gold!")

        self.fnt_lg = pygame.font.SysFont("monospace", 17, bold=True)
        self.fnt_md = pygame.font.SysFont("monospace", 13)
        self.fnt_sm = pygame.font.SysFont("monospace", 11)

        self._auto_select()   # highlight first ship immediately
        clock = pygame.time.Clock()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

                elif event.type == pygame.KEYDOWN:
                    k = event.key
                    if k in (pygame.K_q, pygame.K_ESCAPE):
                        pygame.quit(); sys.exit()
                    elif k == pygame.K_r:
                        self._setup(self._init_size, None)   # new random seed
                        self._auto_select()
                    elif not self.over:
                        if   k == pygame.K_RETURN:            self._end_turn()
                        elif k in (pygame.K_UP,    pygame.K_w): self._move(Direction.NORTH)
                        elif k in (pygame.K_DOWN,  pygame.K_s): self._move(Direction.SOUTH)
                        elif k in (pygame.K_LEFT,  pygame.K_a): self._move(Direction.WEST)
                        elif k in (pygame.K_RIGHT, pygame.K_d): self._move(Direction.EAST)
                        elif k == pygame.K_SPACE:             self._move(Direction.STAY)
                        elif k == pygame.K_TAB:               self._cycle_ship(reverse=bool(event.mod & pygame.KMOD_SHIFT))
                        elif k == pygame.K_c:                 self._convert()
                        elif k == pygame.K_n:                 self._spawn()

            # ── render ──
            self.screen.fill(DARK_BG)
            self._draw_board()
            self._draw_dropoffs()
            self._draw_ships()
            self._draw_header()
            self._draw_info()
            if self.over:
                self._draw_game_over()

            pygame.display.flip()
            clock.tick(60)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Halite visual game")
    p.add_argument("--size", type=int, default=16, help="Board size (default 16)")
    p.add_argument("--seed", type=int, default=None)
    args = p.parse_args()

    HalitePygame(board_size=args.size, seed=args.seed).run()
