"""Level 1 inventory and journal. Original key and clue drawing retained."""
import math
import pygame
from systems.audio import audio

class InventoryModal:
    """UI Overlay for managing collected keys and clue journal entries."""
    CATEGORIES = ['KEYS', 'CLUES']
    KEY_DEFS = [{'id': 'key_bronze', 'name': 'Bronze Key', 'category': 'KEY', 'type': 'Key', 'description': 'A heavy bronze key found near the eastern ruins. Tarnished with age, it bears an astrological triple-crescent motif and engraved celestial runes.', 'color': (205, 127, 50)}, {'id': 'key_silver', 'name': 'Silver Key', 'category': 'KEY', 'type': 'Key', 'description': 'A polished silver key salvaged from the dark corridors. Masterfully forged with heart-shaped filigree scrollwork and gleaming moon highlights.', 'color': (192, 192, 210)}, {'id': 'key_gold', 'name': 'Gold Key', 'category': 'KEY', 'type': 'Key', 'description': 'A pristine gold key retrieved from the northern alcove. Features an ornate imperial crown crest and fluted shaft, untouched by rust.', 'color': (240, 195, 55)}]
    KNOWN_CLUE_DEFS = {'clue_statue': {'title': 'Ancient Guardian Statue', 'type': 'STATUE', 'description': "An ancient stone sentinel overlooks the ruined corridor. An eroded inscription at its base warns: 'Beyond this threshold lies the Hall of Fate, where three great arches stand in silent trial. Only pure light will reveal the path that does not lead to ruin.'"}, 'clue_stump': {'title': 'Gnarled Tree Stump', 'type': 'TREE STUMP', 'description': "Ancient runes are scored into the petrified tree rings: 'In the deep chambers, darkness is not merely an absence of light, but a prowling hunger. Guard your flame diligently, for when the light falters, the shadow awakens to claim what remains.'"}, 'clue_stone': {'title': 'Weathered Standing Stone', 'type': 'STANDING STONE', 'description': "Carved glyphs wind down the ancient megalith: 'Three sacred keys exist in each domain of the temple. The first opens the passage; the second tests your resolve; the third preserves your soul. Trust your instincts when facing the seal.'"}}

    def __init__(self, screen_width: int=960, screen_height: int=540):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.is_open = False
        self.active_tab_index = 0
        self.selected_grid_index = 0
        self.just_selected_item = None
        self.anim_phase = 0.0
        self.panel_width = 820
        self.panel_height = 470
        self.panel_x = (self.screen_width - self.panel_width) // 2
        self.panel_y = (self.screen_height - self.panel_height) // 2
        self.tab_bar_rect = pygame.Rect(self.panel_x + 16, self.panel_y + 50, 110, self.panel_height - 70)
        self.grid_panel_rect = pygame.Rect(self.panel_x + 136, self.panel_y + 50, 380, self.panel_height - 70)
        self.detail_panel_rect = pygame.Rect(self.panel_x + 526, self.panel_y + 50, 278, self.panel_height - 70)
        self.cols = 4
        self.rows = 3
        self.slot_width = 80
        self.slot_height = 80
        self.slot_gap_x = 12
        self.slot_gap_y = 12
        self.grid_start_x = self.grid_panel_rect.x + 10
        self.grid_start_y = self.grid_panel_rect.y + 70

    def open(self):
        """Opens the inventory overlay."""
        self.is_open = True
        self.selected_grid_index = 0

    def close(self):
        """Closes the inventory overlay."""
        self.is_open = False

    def toggle(self):
        """Toggles inventory open/close state."""
        if self.is_open:
            self.close()
        else:
            self.open()

    def update(self, dt: float):
        """Updates UI animation state."""
        if self.is_open:
            self.anim_phase = (self.anim_phase + dt * 4.0) % (2 * math.pi)

    def handle_input(self, event: pygame.event.Event, game_pos: tuple[int, int] | None=None, inventory=None) -> bool:
        """Handles keyboard and mouse interactions while the inventory overlay is active."""
        if not self.is_open:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_i:
                self.close()
                return True
            elif event.key == pygame.K_q:
                self.active_tab_index = (self.active_tab_index - 1) % len(self.CATEGORIES)
                self.selected_grid_index = 0
                return True
            elif event.key == pygame.K_e:
                self.active_tab_index = (self.active_tab_index + 1) % len(self.CATEGORIES)
                self.selected_grid_index = 0
                return True
            elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                cat = self.CATEGORIES[self.active_tab_index]
                if cat == 'KEYS' and inventory is not None:
                    items = self._get_category_items(inventory)
                    if 0 <= self.selected_grid_index < len(items):
                        k_item = items[self.selected_grid_index]
                        if k_item['collected']:
                            inventory.select_key(k_item['id'])
                            audio.play('clue')
                            self.just_selected_item = ('key', k_item['id'])
                            self.close()
                            return True
                return True
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                col = self.selected_grid_index % self.cols
                if col > 0:
                    self.selected_grid_index -= 1
                return True
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                col = self.selected_grid_index % self.cols
                if col < self.cols - 1:
                    self.selected_grid_index += 1
                return True
            elif event.key in (pygame.K_UP, pygame.K_w):
                row = self.selected_grid_index // self.cols
                if row > 0:
                    self.selected_grid_index -= self.cols
                return True
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                row = self.selected_grid_index // self.cols
                if row < self.rows - 1:
                    self.selected_grid_index += self.cols
                return True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = game_pos if game_pos is not None else event.pos
            close_btn = pygame.Rect(self.panel_x + self.panel_width - 34, self.panel_y + 10, 24, 22)
            if close_btn.collidepoint(mx, my):
                self.close()
                return True
            tab_h = 74
            tab_gap = 10
            for i in range(len(self.CATEGORIES)):
                tr = pygame.Rect(self.tab_bar_rect.x, self.tab_bar_rect.y + 10 + i * (tab_h + tab_gap), self.tab_bar_rect.width, tab_h)
                if tr.collidepoint(mx, my):
                    self.active_tab_index = i
                    self.selected_grid_index = 0
                    return True
            for r in range(self.rows):
                for c in range(self.cols):
                    idx = r * self.cols + c
                    sx = self.grid_start_x + c * (self.slot_width + self.slot_gap_x)
                    sy = self.grid_start_y + r * (self.slot_height + self.slot_gap_y)
                    sr = pygame.Rect(sx, sy, self.slot_width, self.slot_height)
                    if sr.collidepoint(mx, my):
                        self.selected_grid_index = idx
                        return True
            btn_y = self.detail_panel_rect.bottom - 36
            btn_rect = pygame.Rect(self.detail_panel_rect.x + 12, btn_y, self.detail_panel_rect.width - 24, 28)
            if btn_rect.collidepoint(mx, my):
                cat = self.CATEGORIES[self.active_tab_index]
                if cat == 'KEYS' and inventory is not None:
                    items = self._get_category_items(inventory)
                    if 0 <= self.selected_grid_index < len(items):
                        k_item = items[self.selected_grid_index]
                        if k_item['collected']:
                            inventory.select_key(k_item['id'])
                            audio.play('clue')
                            self.just_selected_item = ('key', k_item['id'])
                            self.close()
                            return True
            panel_rect = pygame.Rect(self.panel_x, self.panel_y, self.panel_width, self.panel_height)
            if not panel_rect.collidepoint(mx, my):
                self.close()
                return True
        return True

    def _get_category_items(self, inventory, current_level_id: str='level1') -> list[dict]:
        """Builds the list of items for the currently active tab."""
        items = []
        if self.CATEGORIES[self.active_tab_index] == 'KEYS':
            for kdef in self.KEY_DEFS:
                collected = inventory.has_key(kdef['id']) if inventory is not None else False
                is_selected = getattr(inventory, 'selected_key_id', None) == kdef['id']
                items.append({'id': kdef['id'], 'name': kdef['name'], 'category': kdef['category'], 'type': kdef['type'], 'status': 'COLLECTED' if collected else 'NOT COLLECTED', 'collected': collected, 'is_selected': is_selected, 'description': kdef['description'], 'color': kdef['color']})
        elif self.CATEGORIES[self.active_tab_index] == 'CLUES':
            discovered_clues = inventory.get_clues() if inventory is not None else []
            for c in discovered_clues:
                c_id = c['id']
                known = self.KNOWN_CLUE_DEFS.get(c_id, {})
                title = c.get('title') or known.get('title') or c_id
                ctype = c.get('type') or known.get('type') or 'JOURNAL'
                text = c.get('text') or known.get('description') or 'Discovered clue entry.'
                items.append({'id': c_id, 'name': title, 'category': 'JOURNAL', 'type': ctype.upper(), 'status': 'DISCOVERED', 'collected': True, 'description': text, 'color': (215, 175, 55)})
        return items

    def draw(self, surface: pygame.Surface, inventory, current_level_id: str='level1'):
        """Renders the inventory overlay onto the screen surface."""
        if not self.is_open:
            return
        overlay = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        overlay.fill((10, 8, 14, 210))
        surface.blit(overlay, (0, 0))
        panel_rect = pygame.Rect(self.panel_x, self.panel_y, self.panel_width, self.panel_height)
        pygame.draw.rect(surface, (22, 19, 28), panel_rect, border_radius=8)
        pygame.draw.rect(surface, (45, 38, 54), panel_rect, width=3, border_radius=8)
        pygame.draw.rect(surface, (180, 140, 45), panel_rect, width=1, border_radius=8)
        header_rect = pygame.Rect(self.panel_x, self.panel_y, self.panel_width, 42)
        pygame.draw.rect(surface, (14, 12, 18), header_rect, border_top_left_radius=8, border_top_right_radius=8)
        pygame.draw.line(surface, (140, 110, 40), (self.panel_x + 10, self.panel_y + 41), (self.panel_x + self.panel_width - 10, self.panel_y + 41), 1)
        font_title = pygame.font.SysFont('georgia', 18, bold=True)
        font_sub = pygame.font.SysFont('consolas', 12, bold=True)
        font_bold = pygame.font.SysFont('consolas', 13, bold=True)
        font_text = pygame.font.SysFont('consolas', 11)
        title_txt = font_title.render('INVENTORY & JOURNAL', True, (240, 210, 130))
        surface.blit(title_txt, (self.panel_x + 20, self.panel_y + 10))
        cat_title = self.CATEGORIES[self.active_tab_index]
        cat_txt = font_sub.render(f'CATEGORY: {cat_title}', True, (170, 150, 110))
        surface.blit(cat_txt, (self.panel_x + self.panel_width - cat_txt.get_width() - 48, self.panel_y + 14))
        close_rect = pygame.Rect(self.panel_x + self.panel_width - 34, self.panel_y + 10, 24, 22)
        pygame.draw.rect(surface, (35, 28, 42), close_rect, border_radius=4)
        pygame.draw.rect(surface, (140, 110, 60), close_rect, width=1, border_radius=4)
        close_x = font_bold.render('×', True, (210, 185, 130))
        surface.blit(close_x, (close_rect.centerx - close_x.get_width() // 2, close_rect.centery - close_x.get_height() // 2 - 1))
        self._draw_tab_bar(surface, font_sub, font_bold)
        items = self._get_category_items(inventory, current_level_id)
        self._draw_grid_panel(surface, items, font_sub, font_bold, font_text)
        selected_item = None
        if 0 <= self.selected_grid_index < len(items):
            selected_item = items[self.selected_grid_index]
        self._draw_detail_panel(surface, selected_item, font_title, font_sub, font_bold, font_text)
        footer_y = self.panel_y + self.panel_height - 24
        controls_txt = font_text.render('[Q/E] Switch Category   [WASD/Arrows/Mouse] Select Item   [I/ESC] Close Inventory', True, (140, 130, 110))
        surface.blit(controls_txt, (self.panel_x + (self.panel_width - controls_txt.get_width()) // 2, footer_y))

    def _draw_tab_bar(self, surface: pygame.Surface, font_sub, font_bold):
        """Draws the left vertical category navigation tabs."""
        pygame.draw.rect(surface, (16, 14, 22), self.tab_bar_rect, border_radius=6)
        pygame.draw.rect(surface, (38, 32, 48), self.tab_bar_rect, width=1, border_radius=6)
        tab_h = 74
        tab_gap = 10
        for i, cat in enumerate(self.CATEGORIES):
            tr = pygame.Rect(self.tab_bar_rect.x + 4, self.tab_bar_rect.y + 10 + i * (tab_h + tab_gap), self.tab_bar_rect.width - 8, tab_h)
            is_active = i == self.active_tab_index
            if is_active:
                pygame.draw.rect(surface, (35, 28, 44), tr, border_radius=6)
                pygame.draw.rect(surface, (215, 175, 55), tr, width=2, border_radius=6)
                pygame.draw.rect(surface, (240, 200, 70), (tr.x - 2, tr.y + 10, 4, tr.height - 20), border_radius=2)
            else:
                pygame.draw.rect(surface, (22, 19, 28), tr, border_radius=6)
                pygame.draw.rect(surface, (45, 38, 54), tr, width=1, border_radius=6)
            label_color = (245, 225, 150) if is_active else (130, 120, 100)
            txt = font_bold.render(cat, True, label_color)
            surface.blit(txt, (tr.x + (tr.width - txt.get_width()) // 2, tr.y + tr.height // 2 - 8))

    def _draw_grid_panel(self, surface: pygame.Surface, items: list[dict], font_sub, font_bold, font_text):
        """Draws the middle 4x3 item grid panel."""
        pygame.draw.rect(surface, (16, 14, 22), self.grid_panel_rect, border_radius=6)
        pygame.draw.rect(surface, (38, 32, 48), self.grid_panel_rect, width=1, border_radius=6)
        cat_name = self.CATEGORIES[self.active_tab_index]
        if cat_name == 'CLUES':
            cnt_str = f'Discovered Entries: {len(items)}'
        elif cat_name == 'KEYS':
            cnt = sum((1 for it in items if it['collected']))
            cnt_str = f'Collected: {cnt}/{len(self.KEY_DEFS)}'
        else:
            cnt = sum((1 for it in items if it['collected']))
            cnt_str = f'Collected: {cnt}/{len(self.KEY_DEFS)}'
        hdr_txt = font_bold.render(f'{cat_name} GRID', True, (210, 185, 110))
        cnt_txt = font_sub.render(cnt_str, True, (150, 135, 100))
        surface.blit(hdr_txt, (self.grid_panel_rect.x + 14, self.grid_panel_rect.y + 12))
        surface.blit(cnt_txt, (self.grid_panel_rect.x + self.grid_panel_rect.width - cnt_txt.get_width() - 14, self.grid_panel_rect.y + 14))
        pygame.draw.line(surface, (50, 42, 60), (self.grid_panel_rect.x + 10, self.grid_panel_rect.y + 38), (self.grid_panel_rect.x + self.grid_panel_rect.width - 10, self.grid_panel_rect.y + 38), 1)
        for r in range(self.rows):
            for c in range(self.cols):
                idx = r * self.cols + c
                sx = self.grid_start_x + c * (self.slot_width + self.slot_gap_x)
                sy = self.grid_start_y + r * (self.slot_height + self.slot_gap_y)
                slot_rect = pygame.Rect(sx, sy, self.slot_width, self.slot_height)
                is_selected = idx == self.selected_grid_index
                item = items[idx] if idx < len(items) else None
                if is_selected:
                    pygame.draw.rect(surface, (42, 34, 52), slot_rect, border_radius=6)
                    pulse = int(180 + 75 * math.sin(self.anim_phase))
                    gold_col = (pulse, min(255, pulse - 30), max(30, pulse - 120))
                    pygame.draw.rect(surface, gold_col, slot_rect, width=2, border_radius=6)
                else:
                    pygame.draw.rect(surface, (24, 20, 30), slot_rect, border_radius=6)
                    pygame.draw.rect(surface, (45, 38, 54), slot_rect, width=1, border_radius=6)
                if item:
                    self._draw_item_icon(surface, slot_rect.centerx, slot_rect.centery - 8, item, small=True)
                    short_name = item['name']
                    if len(short_name) > 10:
                        short_name = short_name[:9] + '…'
                    lbl_col = (235, 220, 180) if item['collected'] else (110, 100, 90)
                    lbl = font_text.render(short_name, True, lbl_col)
                    surface.blit(lbl, (slot_rect.centerx - lbl.get_width() // 2, slot_rect.bottom - 16))
                    if item['status'] == 'INSTALLED':
                        dot_col = (90, 180, 255)
                    elif item['collected']:
                        dot_col = (70, 210, 120)
                    else:
                        dot_col = (80, 60, 60)
                    pygame.draw.circle(surface, dot_col, (slot_rect.right - 8, slot_rect.top + 8), 4)
                else:
                    pygame.draw.circle(surface, (35, 30, 42), slot_rect.center, 6, width=1)

    def _draw_detail_panel(self, surface: pygame.Surface, item: dict | None, font_title, font_sub, font_bold, font_text):
        """Draws the right selected-item details panel."""
        pygame.draw.rect(surface, (16, 14, 22), self.detail_panel_rect, border_radius=6)
        pygame.draw.rect(surface, (38, 32, 48), self.detail_panel_rect, width=1, border_radius=6)
        if not item:
            no_item_txt = font_bold.render('No Item Selected', True, (120, 110, 95))
            surface.blit(no_item_txt, (self.detail_panel_rect.x + (self.detail_panel_rect.width - no_item_txt.get_width()) // 2, self.detail_panel_rect.y + 180))
            return
        top_y = self.detail_panel_rect.y + 16
        emblem_box = pygame.Rect(self.detail_panel_rect.x + (self.detail_panel_rect.width - 80) // 2, top_y, 80, 80)
        pygame.draw.rect(surface, (26, 22, 34), emblem_box, border_radius=8)
        pygame.draw.rect(surface, (140, 110, 40), emblem_box, width=1, border_radius=8)
        self._draw_item_icon(surface, emblem_box.centerx, emblem_box.centery, item, small=False)
        title_y = emblem_box.bottom + 12
        lines = self._wrap_text(item['name'], font_bold, self.detail_panel_rect.width - 20)
        curr_y = title_y
        for l in lines:
            t_surf = font_bold.render(l, True, (245, 220, 140))
            surface.blit(t_surf, (self.detail_panel_rect.x + (self.detail_panel_rect.width - t_surf.get_width()) // 2, curr_y))
            curr_y += 16
        type_str = f"[{item['category']} — {item['type']}]"
        type_surf = font_sub.render(type_str, True, (160, 140, 100))
        surface.blit(type_surf, (self.detail_panel_rect.x + (self.detail_panel_rect.width - type_surf.get_width()) // 2, curr_y + 4))
        curr_y += 24
        status_str = f"STATUS: {item['status']}"
        if item['status'] == 'INSTALLED':
            badge_col = (90, 180, 255)
        elif item['collected']:
            badge_col = (70, 210, 120)
        else:
            badge_col = (180, 80, 80)
        st_surf = font_bold.render(status_str, True, badge_col)
        surface.blit(st_surf, (self.detail_panel_rect.x + (self.detail_panel_rect.width - st_surf.get_width()) // 2, curr_y))
        curr_y += 24
        pygame.draw.line(surface, (50, 42, 60), (self.detail_panel_rect.x + 12, curr_y), (self.detail_panel_rect.x + self.detail_panel_rect.width - 12, curr_y), 1)
        curr_y += 10
        desc_lines = self._wrap_text(item['description'], font_text, self.detail_panel_rect.width - 24)
        for dline in desc_lines:
            if curr_y + 14 > self.detail_panel_rect.bottom - 40:
                break
            d_surf = font_text.render(dline, True, (200, 190, 170))
            surface.blit(d_surf, (self.detail_panel_rect.x + 12, curr_y))
            curr_y += 15
        btn_y = self.detail_panel_rect.bottom - 36
        btn_rect = pygame.Rect(self.detail_panel_rect.x + 12, btn_y, self.detail_panel_rect.width - 24, 28)
        if item['category'] == 'KEY':
            if item.get('is_selected', False):
                pulse = int(190 + 65 * math.sin(self.anim_phase * 1.5))
                gold_b = (pulse, min(255, pulse - 20), max(40, pulse - 110))
                pygame.draw.rect(surface, (48, 36, 18), btn_rect, border_radius=4)
                pygame.draw.rect(surface, gold_b, btn_rect, width=2, border_radius=4)
                act_txt = font_bold.render('★ SELECTED KEY ★', True, (255, 235, 130))
            elif item.get('collected', False):
                pygame.draw.rect(surface, (36, 28, 18), btn_rect, border_radius=4)
                pygame.draw.rect(surface, (215, 175, 55), btn_rect, width=1, border_radius=4)
                act_txt = font_bold.render('[SPACE / CLICK] SELECT & USE KEY', True, (250, 220, 130))
            else:
                pygame.draw.rect(surface, (20, 16, 24), btn_rect, border_radius=4)
                pygame.draw.rect(surface, (45, 38, 52), btn_rect, width=1, border_radius=4)
                act_txt = font_text.render('Uncollected Key', True, (110, 100, 90))
        else:
            pygame.draw.rect(surface, (28, 24, 35), btn_rect, border_radius=4)
            pygame.draw.rect(surface, (55, 48, 66), btn_rect, width=1, border_radius=4)
            act_txt = font_text.render('Discovered Journal Lore', True, (215, 175, 55))
        surface.blit(act_txt, (btn_rect.x + (btn_rect.width - act_txt.get_width()) // 2, btn_rect.y + (btn_rect.height - act_txt.get_height()) // 2))

    def _draw_item_icon(self, surface: pygame.Surface, cx: int, cy: int, item: dict, small: bool=True):
        """Renders ornate fantasy artifact visuals for keys and clues inspired by reference images."""
        scale = 0.65 if small else 1.05
        col = item.get('color', (215, 175, 55))
        cat = item.get('category', '')
        item_id = item.get('id', '')
        collected = item.get('collected', True)
        if cat == 'KEY':
            if not collected:
                c_metal = (70, 60, 52)
                c_light = (90, 80, 70)
                c_dark = (45, 38, 32)
            elif 'bronze' in item_id:
                c_metal = (185, 120, 55)
                c_light = (225, 165, 95)
                c_dark = (100, 65, 30)
            elif 'silver' in item_id:
                c_metal = (195, 205, 220)
                c_light = (245, 250, 255)
                c_dark = (110, 120, 135)
            else:
                c_metal = (235, 195, 55)
                c_light = (255, 240, 130)
                c_dark = (150, 115, 25)
            head_y = cy - int(12 * scale)
            if 'bronze' in item_id:
                r_ring = int(6 * scale)
                pygame.draw.circle(surface, c_dark, (cx, head_y), r_ring + 1, width=max(1, int(2 * scale)))
                pygame.draw.circle(surface, c_metal, (cx, head_y), r_ring, width=max(1, int(2 * scale)))
                pygame.draw.line(surface, c_dark, (cx - int(3 * scale), head_y), (cx + int(3 * scale), head_y), 1)
                pygame.draw.line(surface, c_dark, (cx, head_y - int(3 * scale)), (cx, head_y + int(3 * scale)), 1)
                c_top_y = head_y - int(8 * scale)
                pygame.draw.circle(surface, c_light, (cx, c_top_y), max(1, int(2 * scale)))
                pygame.draw.arc(surface, c_light, (cx - int(11 * scale), head_y - int(12 * scale), int(10 * scale), int(10 * scale)), 0.3, 2.8, max(1, int(2 * scale)))
                pygame.draw.arc(surface, c_light, (cx + int(1 * scale), head_y - int(12 * scale), int(10 * scale), int(10 * scale)), 0.3, 2.8, max(1, int(2 * scale)))
                pygame.draw.arc(surface, c_metal, (cx - int(9 * scale), head_y - int(2 * scale), int(8 * scale), int(8 * scale)), 3.14, 5.5, max(1, int(2 * scale)))
                pygame.draw.arc(surface, c_metal, (cx + int(1 * scale), head_y - int(2 * scale), int(8 * scale), int(8 * scale)), 3.9, 6.28, max(1, int(2 * scale)))
            elif 'silver' in item_id:
                pygame.draw.polygon(surface, c_light, [(cx, head_y - int(12 * scale)), (cx - int(3 * scale), head_y - int(8 * scale)), (cx + int(3 * scale), head_y - int(8 * scale))])
                pygame.draw.circle(surface, c_metal, (cx - int(4 * scale), head_y - int(4 * scale)), int(4 * scale), width=max(1, int(2 * scale)))
                pygame.draw.circle(surface, c_metal, (cx + int(4 * scale), head_y - int(4 * scale)), int(4 * scale), width=max(1, int(2 * scale)))
                pygame.draw.polygon(surface, c_metal, [(cx - int(8 * scale), head_y - int(3 * scale)), (cx + int(8 * scale), head_y - int(3 * scale)), (cx, head_y + int(6 * scale))], width=max(1, int(2 * scale)))
                pygame.draw.circle(surface, c_light, (cx - int(2 * scale), head_y - int(3 * scale)), int(2 * scale))
            else:
                pygame.draw.circle(surface, c_light, (cx, head_y - int(11 * scale)), max(1, int(2 * scale)))
                ov_r = pygame.Rect(cx - int(9 * scale), head_y - int(9 * scale), int(18 * scale), int(16 * scale))
                pygame.draw.ellipse(surface, c_metal, ov_r, width=max(1, int(2 * scale)))
                pygame.draw.polygon(surface, c_light, [(cx - int(5 * scale), head_y + int(1 * scale)), (cx - int(4 * scale), head_y - int(4 * scale)), (cx, head_y - int(2 * scale)), (cx + int(4 * scale), head_y - int(4 * scale)), (cx + int(5 * scale), head_y + int(1 * scale))], width=1)
                pygame.draw.circle(surface, c_light, (cx - int(7 * scale), head_y), 1)
                pygame.draw.circle(surface, c_light, (cx + int(7 * scale), head_y), 1)
            neck_y = head_y + int(7 * scale)
            pygame.draw.line(surface, c_light, (cx - int(4 * scale), neck_y), (cx + int(4 * scale), neck_y), max(1, int(2 * scale)))
            pygame.draw.line(surface, c_dark, (cx - int(3 * scale), neck_y + int(2 * scale)), (cx + int(3 * scale), neck_y + int(2 * scale)), 1)
            shaft_top = neck_y + int(3 * scale)
            shaft_bot = cy + int(18 * scale)
            pygame.draw.line(surface, c_dark, (cx + 1, shaft_top), (cx + 1, shaft_bot), max(2, int(3 * scale)))
            pygame.draw.line(surface, c_metal, (cx, shaft_top), (cx, shaft_bot), max(2, int(3 * scale)))
            pygame.draw.line(surface, c_light, (cx - 1, shaft_top), (cx - 1, shaft_bot), 1)
            if 'bronze' in item_id:
                for dy in range(int(3 * scale), int(12 * scale), int(3 * scale)):
                    pygame.draw.line(surface, c_dark, (cx - int(2 * scale), shaft_top + dy), (cx + int(2 * scale), shaft_top + dy), 1)
            elif 'gold' in item_id:
                pygame.draw.line(surface, c_light, (cx - 1, shaft_top), (cx - 1, shaft_top + int(7 * scale)), 1)
            bit_top = cy + int(8 * scale)
            bit_w = int(8 * scale)
            bit_h = int(9 * scale)
            pygame.draw.rect(surface, c_metal, (cx, bit_top, bit_w, bit_h))
            pygame.draw.rect(surface, c_dark, (cx, bit_top, bit_w, bit_h), width=1)
            cut_w = max(2, int(3 * scale))
            cut_h = max(2, int(3 * scale))
            pygame.draw.rect(surface, (26, 22, 34), (cx + int(3 * scale), bit_top + int(2 * scale), cut_w, cut_h))
            pygame.draw.line(surface, c_light, (cx + bit_w - 1, bit_top), (cx + bit_w - 1, bit_top + bit_h), 1)
        elif 'statue' in item_id:
            pygame.draw.rect(surface, col, (cx - int(6 * scale), cy + int(4 * scale), int(12 * scale), int(4 * scale)))
            pygame.draw.polygon(surface, col, [(cx - int(4 * scale), cy + int(4 * scale)), (cx + int(4 * scale), cy + int(4 * scale)), (cx + int(3 * scale), cy - int(6 * scale)), (cx - int(3 * scale), cy - int(6 * scale))])
            pygame.draw.circle(surface, col, (cx, cy - int(9 * scale)), int(3 * scale))
        elif 'plaque' in item.get('type', '').lower() or 'inscription' in item_id:
            pr = pygame.Rect(cx - int(12 * scale), cy - int(10 * scale), int(24 * scale), int(20 * scale))
            pygame.draw.rect(surface, (45, 40, 52), pr, border_radius=2)
            pygame.draw.rect(surface, col, pr, width=2, border_radius=2)
            pygame.draw.line(surface, (160, 140, 100), (pr.x + 4, pr.y + 6), (pr.right - 4, pr.y + 6), 1)
            pygame.draw.line(surface, (160, 140, 100), (pr.x + 4, pr.y + 11), (pr.right - 4, pr.y + 11), 1)
        else:
            r = int(10 * scale)
            pygame.draw.circle(surface, col, (cx, cy), r, width=2)
            pygame.draw.circle(surface, col, (cx, cy), int(4 * scale))
            for i in range(4):
                ang = i * (math.pi / 2)
                rx1 = cx + int(6 * scale * math.cos(ang))
                ry1 = cy + int(6 * scale * math.sin(ang))
                rx2 = cx + int(12 * scale * math.cos(ang))
                ry2 = cy + int(12 * scale * math.sin(ang))
                pygame.draw.line(surface, col, (rx1, ry1), (rx2, ry2), 1)

    def _wrap_text(self, text: str, font, max_width: int) -> list[str]:
        """Utility helper to wrap paragraph text cleanly into multiple lines."""
        words = text.split(' ')
        lines = []
        current_line = ''
        for word in words:
            test_line = f'{current_line} {word}'.strip()
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        return lines
