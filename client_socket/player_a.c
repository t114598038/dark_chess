#include "dark_chess_client.h"
#include <windows.h>
#include <time.h> // 需要加在最上方，用於亂數
#include <stdlib.h>

// 階級定義：帥(7) > 仕(6) > 象(5) > 俥(4) > 傌(3) > 炮(2) > 兵(1)
int get_rank(const char* piece) {
    if (strstr(piece, "King")) return 7;
    if (strstr(piece, "Guard")) return 6;
    if (strstr(piece, "Elephant")) return 5;
    if (strstr(piece, "Car")) return 4;
    if (strstr(piece, "Horse")) return 3;
    if (strstr(piece, "Cannon")) return 2;
    if (strstr(piece, "Soldier")) return 1;
    return 0;
}
// 輔助函式：從 JSON 中提取 board 陣列中的第 index 個棋子
void get_piece_at(const char* json, int index, char* out_piece) {
    const char* board_start = strstr(json, "\"board\": [[");
    if (!board_start) {
        strcpy(out_piece, "Unknown");
        return;
    }
    
    const char* p = board_start + 11;
    for (int i = 0; i <= index; i++) {
        p = strchr(p, '\"');
        if (!p) break;
        p++;
        const char* end = strchr(p, '\"');
        if (!end) break;
        
        if (i == index) {
            int len = end - p;
            if (len > 31) len = 31;
            strncpy(out_piece, p, len);
            out_piece[len] = '\0';
            return;
        }
        p = end + 1;
    }
    strcpy(out_piece, "Unknown");
}
// 輔助函式：獲取指定角色 (A 或 B) 的顏色 (Red 或 Black)
void get_role_color(const char* json, const char* role, char* out_color) {
    char search_key[20];
    sprintf(search_key, "\"%s\": \"", role);
    const char* p = strstr(json, search_key);
    if (p) {
        p += strlen(search_key);
        const char* end = strchr(p, '\"');
        if (end) {
            int len = end - p;
            strncpy(out_color, p, len);
            out_color[len] = '\0';
            return;
        }
    }
    strcpy(out_color, "None");
}
int count_between(const char* json, int r1, int c1, int r2, int c2) {
    int count = 0;
    if (r1 == r2) {
        int min_c = (c1 < c2) ? c1 : c2;
        int max_c = (c1 > c2) ? c1 : c2;
        for (int c = min_c + 1; c < max_c; c++) {
            char p[32];
            get_piece_at(json, r1 * 8 + c, p);
            if (strcmp(p, "Null") != 0) count++;
        }
    } else if (c1 == c2) {
        int min_r = (r1 < r2) ? r1 : r2;
        int max_r = (r1 > r2) ? r1 : r2;
        for (int r = min_r + 1; r < max_r; r++) {
            char p[32];
            get_piece_at(json, r * 8 + c1, p);
            if (strcmp(p, "Null") != 0) count++;
        }
    } else {
        return -1;
    }
    return count;
}
int get_piece_value(const char* piece) {
    if (strstr(piece, "King")) return 1000;
    if (strstr(piece, "Guard")) return 600;
    if (strstr(piece, "Elephant")) return 500;
    if (strstr(piece, "Car")) return 400;
    if (strstr(piece, "Cannon")) return 450;
    if (strstr(piece, "Horse")) return 300;
    if (strstr(piece, "Soldier")) return 150;
    return 0;
}

int get_distance(int r1, int c1, int r2, int c2) {
    return abs(r1 - r2) + abs(c1 - c2);
}

const int pos_bonus[4][8] = {
    { 0,  5, 10, 15, 15, 10,  5,  0},
    { 5, 10, 20, 25, 25, 20, 10,  5},
    { 5, 10, 20, 25, 25, 20, 10,  5},
    { 0,  5, 10, 15, 15, 10,  5,  0}
};

// ---------------------------------------------------------
// [進階情報系統：算牌與戰力評估]
// ---------------------------------------------------------
int count_pieces(const char* json, const char* color, const char* piece_type) {
    int count = 0;
    for (int i = 0; i < 32; i++) {
        char tmp[32];
        get_piece_at(json, i, tmp);
        if (strcmp(color, "None") == 0) {
            if (strstr(tmp, piece_type)) count++;
        } else if (strstr(tmp, color) && strstr(tmp, piece_type)) {
            count++;
        }
    }
    return count;
}

int get_army_value(const char* json, const char* color) {
    int total = 0;
    for (int i = 0; i < 32; i++) {
        char p[32];
        get_piece_at(json, i, p);
        if (strstr(p, color)) total += get_piece_value(p);
    }
    return total;
}

// ---------------------------------------------------------
// [戰術預判系統：危險、保護與火力網]
// ---------------------------------------------------------
// 1. 檢查這格會不會被敵人吃
int is_square_threatened(const char* json, int r, int c, const char* opp_color, int my_rank, const char* my_piece) {
    int dr[] = {-1, 1, 0, 0}, dc[] = {0, 0, -1, 1};
    int is_my_soldier = strstr(my_piece, "Soldier") != NULL;
    int is_my_king = strstr(my_piece, "King") != NULL;

    for (int j = 0; j < 4; j++) {
        int nr = r + dr[j], nc = c + dc[j];
        if (nr >= 0 && nr < 4 && nc >= 0 && nc < 8) {
            char target[32];
            get_piece_at(json, nr * 8 + nc, target);
            if (strstr(target, opp_color) && !strstr(target, "Cannon")) {
                int t_rank = get_rank(target);
                int is_enemy_soldier = strstr(target, "Soldier") != NULL;
                int is_enemy_king = strstr(target, "King") != NULL;
                
                if (is_enemy_soldier && is_my_king) return 1;
                else if (is_enemy_king && is_my_soldier) continue;
                else if (t_rank >= my_rank) return 1; 
            }
        }
    }
    for (int i = 0; i < 32; i++) {
        char target[32];
        get_piece_at(json, i, target);
        if (strstr(target, opp_color) && strstr(target, "Cannon")) {
            int tr = i / 8, tc = i % 8;
            if (count_between(json, tr, tc, r, c) == 1) return 1; 
        }
    }
    return 0;
}

// 2. 檢查這格有沒有自己人保護
int is_protected_by_ally(const char* json, int r, int c, const char* my_color, int my_rank, const char* my_piece) {
    int dr[] = {-1, 1, 0, 0}, dc[] = {0, 0, -1, 1};
    int is_my_king = strstr(my_piece, "King") != NULL;
    int is_my_soldier = strstr(my_piece, "Soldier") != NULL;

    for (int j = 0; j < 4; j++) {
        int nr = r + dr[j], nc = c + dc[j];
        if (nr >= 0 && nr < 4 && nc >= 0 && nc < 8) {
            char ally[32];
            get_piece_at(json, nr * 8 + nc, ally);
            if (strstr(ally, my_color) && !strstr(ally, "Cannon")) {
                int is_ally_soldier = strstr(ally, "Soldier") != NULL;
                int is_ally_king = strstr(ally, "King") != NULL;
                if (is_ally_soldier && is_my_king) continue; 
                if (is_ally_king && is_my_soldier) continue; 
                return 1; 
            }
        }
    }
    return 0;
}

// 3. 火力網：走到這格能同時威脅幾個敵人？
int get_threat_footprint(const char* json, int r, int c, const char* opp_color, int my_rank, const char* my_piece) {
    int count = 0;
    int dr[] = {-1, 1, 0, 0}, dc[] = {0, 0, -1, 1};
    int is_cannon = strstr(my_piece, "Cannon") != NULL;

    if (is_cannon) {
        for (int i = 0; i < 32; i++) {
            char target[32];
            get_piece_at(json, i, target);
            if (strstr(target, opp_color)) {
                int tr = i / 8, tc = i % 8;
                if (count_between(json, r, c, tr, tc) == 1) count += 2; 
            }
        }
    } else {
        for (int j = 0; j < 4; j++) {
            int nr = r + dr[j], nc = c + dc[j];
            if (nr >= 0 && nr < 4 && nc >= 0 && nc < 8) {
                char target[32];
                get_piece_at(json, nr * 8 + nc, target);
                if (strstr(target, opp_color)) {
                    int t_rank = get_rank(target);
                    if (strstr(my_piece, "Soldier") && strstr(target, "King")) count++;
                    else if (my_rank >= t_rank && !strstr(target, "Soldier")) count++;
                }
            }
        }
    }
    return count;
}
// [新增] 自由度剝奪：計算某個敵方棋子還有幾步「安全的路」可以走
int get_enemy_mobility(const char* json, int er, int ec, const char* my_color, int enemy_rank) {
    int mobility = 0;
    int dr[] = {-1, 1, 0, 0}, dc[] = {0, 0, -1, 1};
    for (int j = 0; j < 4; j++) {
        int nr = er + dr[j], nc = ec + dc[j];
        if (nr >= 0 && nr < 4 && nc >= 0 && nc < 8) {
            char target[32];
            get_piece_at(json, nr * 8 + nc, target);
            if (strcmp(target, "Null") == 0) {
                // 如果這條退路沒有被我的火力網覆蓋，才算安全
                if (!is_square_threatened(json, nr, nc, my_color, enemy_rank, target)) {
                    mobility++;
                }
            }
        }
    }
    return mobility;
}

// [新增] 俄羅斯輪盤計算：這格翻開的話，對旁邊的敵人是福是禍？
// 回傳期望值 (正分代表翻開很可能殺死敵人，負分代表翻開很可能是送頭)
int get_flip_ev(const char* json, int r, int c, const char* opp_color, const char* my_color) {
    int ev = 0;
    int dr[] = {-1, 1, 0, 0}, dc[] = {0, 0, -1, 1};
    
    for (int j = 0; j < 4; j++) {
        int nr = r + dr[j], nc = c + dc[j];
        if (nr >= 0 && nr < 4 && nc >= 0 && nc < 8) {
            char adjacent[32];
            get_piece_at(json, nr * 8 + nc, adjacent);
            // 如果旁邊剛好站著敵方的大子 (例如對手的車)
            if (strstr(adjacent, opp_color) && !strstr(adjacent, "Cannon")) {
                int enemy_val = get_piece_value(adjacent);
                int enemy_rank = get_rank(adjacent);
                
                // 算牌：剩下還沒翻出來的牌中，能吃掉他的有幾張？(例如我的將、仕、相)
                int killers_left = 0;
                int feeders_left = 0; // 翻出來會被他白吃的有幾張？
                
                if (enemy_rank == 7) { // 如果旁邊是對手的帥
                    killers_left = count_pieces(json, "None", "Soldier") / 2; // 預估一半是我的兵
                } else {
                    // 粗略計算比他高階的牌剩下幾張
                    killers_left += count_pieces(json, "None", "King") / 2;
                    killers_left += count_pieces(json, "None", "Guard") / 2;
                    if (enemy_rank < 5) killers_left += count_pieces(json, "None", "Elephant") / 2;
                }
                
                // 粗略計算比他低階的牌
                feeders_left += count_pieces(json, "None", "Soldier") / 2;
                if (enemy_rank > 3) feeders_left += count_pieces(json, "None", "Horse") / 2;

                // 計算期望值 (EV)
                ev += (killers_left * enemy_val) - (feeders_left * 150);
            }
        }
    }
    return ev / 10; // 縮小數值避免影響過大
}
// ---------------------------------------------------------
// [新增機制 1] 虛擬棋盤攔截器 (想像力引擎)
// 作用：在不修改真實 JSON 的情況下，假裝某顆棋子已經移動了
// ---------------------------------------------------------
void get_virtual_piece_at(const char* json, int index, char* out_piece, int v_from, int v_to, const char* moved_piece) {
    if (index == v_from) {
        strcpy(out_piece, "Null"); // 想像這個位置已經空了
    } else if (index == v_to) {
        strcpy(out_piece, moved_piece); // 想像棋子已經走到這了
    } else {
        get_piece_at(json, index, out_piece); // 其他格子照舊讀取真實盤面
    }
}

// ---------------------------------------------------------
// [新增機制 2] 虛擬路徑計算 (專門給炮用的想像力)
// ---------------------------------------------------------
int count_between_virtual(const char* json, int r1, int c1, int r2, int c2, int v_from, int v_to, const char* moved_piece) {
    int count = 0;
    if (r1 == r2) {
        int min_c = (c1 < c2) ? c1 : c2;
        int max_c = (c1 > c2) ? c1 : c2;
        for (int c = min_c + 1; c < max_c; c++) {
            char p[32];
            get_virtual_piece_at(json, r1 * 8 + c, p, v_from, v_to, moved_piece);
            if (strcmp(p, "Null") != 0) count++;
        }
    } else if (c1 == c2) {
        int min_r = (r1 < r2) ? r1 : r2;
        int max_r = (r1 > r2) ? r1 : r2;
        for (int r = min_r + 1; r < max_r; r++) {
            char p[32];
            get_virtual_piece_at(json, r * 8 + c1, p, v_from, v_to, moved_piece);
            if (strcmp(p, "Null") != 0) count++;
        }
    }
    return count;
}

// ---------------------------------------------------------
// [新增機制 3] 換位思考引擎 (對手最佳反擊預判)
// 作用：如果我走了這步，對手最高能拿幾分？
// ---------------------------------------------------------
int get_opponent_best_counter(const char* json, int v_from, int v_to, const char* moved_piece, const char* opp_color, const char* my_color) {
    int max_opp_score = 0;
    int dr[] = {-1, 1, 0, 0}, dc[] = {0, 0, -1, 1};

    // 遍歷對手所有的棋子
    for (int i = 0; i < 32; i++) {
        char opp_piece[32];
        get_virtual_piece_at(json, i, opp_piece, v_from, v_to, moved_piece);

        if (strstr(opp_piece, opp_color)) {
            int r = i / 8, c = i % 8;
            int opp_rank = get_rank(opp_piece);
            int is_opp_cannon = strstr(opp_piece, "Cannon") != NULL;

            // 1. 預判對手炮的跳吃
            if (is_opp_cannon) {
                for (int ti = 0; ti < 32; ti++) {
                    char target[32];
                    get_virtual_piece_at(json, ti, target, v_from, v_to, moved_piece);
                    if (strstr(target, my_color)) {
                        int tr = ti / 8, tc = ti % 8;
                        if (count_between_virtual(json, r, c, tr, tc, v_from, v_to, moved_piece) == 1) {
                            int target_val = get_piece_value(target);
                            if (target_val > max_opp_score) max_opp_score = target_val;
                        }
                    }
                }
            } 
            // 2. 預判對手一般棋子的相鄰吃子
            else {
                for (int j = 0; j < 4; j++) {
                    int nr = r + dr[j], nc = c + dc[j];
                    if (nr >= 0 && nr < 4 && nc >= 0 && nc < 8) {
                        char target[32];
                        get_virtual_piece_at(json, nr * 8 + nc, target, v_from, v_to, moved_piece);

                        if (strstr(target, my_color)) {
                            int t_rank = get_rank(target);
                            int can_eat = 0;
                            if (strstr(opp_piece, "Soldier") && strstr(target, "King")) can_eat = 1;
                            else if (strstr(opp_piece, "King") && strstr(target, "Soldier")) can_eat = 0;
                            else if (opp_rank >= t_rank) can_eat = 1;

                            if (can_eat) {
                                int target_val = get_piece_value(target);
                                if (target_val > max_opp_score) max_opp_score = target_val;
                            }
                        }
                    }
                }
            }
        }
    }
    return max_opp_score; // 回傳對手能給我們造成的最大傷害
}
// [加入在 make_move 的最上方或全域]
static int last_from_idx = -1;
static int last_to_idx = -1;
void make_move(const char* json, const char* my_role_ab) {
    char piece[32], target[32], my_color[10], opp_color[10];
    get_role_color(json, my_role_ab, my_color);
    strcpy(opp_color, strcmp(my_color, "Red") == 0 ? "Black" : "Red");

    // === 【大局觀與情報分析】 ===
    int covered_count = count_pieces(json, "None", "Covered");
    int enemy_soldiers_alive = count_pieces(json, opp_color, "Soldier");
    int my_army_value = get_army_value(json, my_color);
    int opp_army_value = get_army_value(json, opp_color);
    int advantage = my_army_value - opp_army_value; // 戰力差

    // 開局第一手強制搶佔中路
    if (strcmp(my_color, "None") == 0) {
        int best_start[] = {11, 12, 19, 20}; 
        for(int k=0; k<4; k++) {
            get_piece_at(json, best_start[k], piece);
            if (strcmp(piece, "Covered") == 0) {
                char action[20];
                sprintf(action, "%d %d\n", best_start[k] / 8, best_start[k] % 8);
                printf("AI (%s) Seize the middle lane: (%d, %d)\n", my_role_ab, best_start[k] / 8, best_start[k] % 8);
                Sleep(1500);
                send_action(action);
                return;
            }
        }
    }

    int best_score = -999999;
    char best_action[64] = "";

    // 尋找敵方最貴的棋子 (索敵雷達)
    int enemy_vip_r = -1, enemy_vip_c = -1, highest_enemy_val = 0;
    for (int k = 0; k < 32; k++) {
        char tmp[32];
        get_piece_at(json, k, tmp);
        if (strstr(tmp, opp_color)) {
            int val = get_piece_value(tmp);
            if (val > highest_enemy_val) {
                highest_enemy_val = val;
                enemy_vip_r = k / 8;
                enemy_vip_c = k % 8;
            }
        }
    }

    // 遍歷所有可能的動作
    for (int i = 0; i < 32; i++) {
        get_piece_at(json, i, piece);

        // --- 策略 A：翻牌評估 ---
        // --- 策略 A：翻牌評估 (機率死神) ---
        if (strcmp(piece, "Covered") == 0) {
            int r = i / 8, c = i % 8;
            int score = 250 + pos_bonus[r][c];
            
            score -= advantage; 
            
            // 【奇異點邏輯】：蒙地卡羅期望值算牌
            int flip_ev = get_flip_ev(json, r, c, opp_color, my_color);
            score += flip_ev; 
            
            // 如果期望值極高，代表翻這張牌很有可能直接殺死旁邊的敵方大子，強力加分！
            if (flip_ev > 300) score += 2000; 

            if (score > best_score) {
                best_score = score;
                sprintf(best_action, "%d %d\n", r, c);
            }
        }

        // --- 策略 B：移動與吃子評估 ---
        if (strstr(piece, my_color)) {
            int r = i / 8, c = i % 8;
            int my_rank = get_rank(piece);
            int my_val = get_piece_value(piece);
            int is_cannon = strstr(piece, "Cannon") != NULL;
            int is_king = strstr(piece, "King") != NULL;

            // 動態價值調整：狂暴帥與殘局炮
            if (is_king && enemy_soldiers_alive == 0) my_val += 4000;
            if (is_cannon && covered_count < 10) my_val -= 200;

            int currently_threatened = is_square_threatened(json, r, c, opp_color, my_rank, piece);

            // B-1: 評估炮的跳吃
            if (is_cannon) {
                for (int ti = 0; ti < 32; ti++) {
                    get_piece_at(json, ti, target);
                    if (strstr(target, opp_color)) {
                        int tr = ti / 8, tc = ti % 8;
                        if (count_between(json, r, c, tr, tc) == 1) {
                            int target_val = get_piece_value(target);
                            int future_threatened = is_square_threatened(json, tr, tc, opp_color, my_rank, piece);
                            int is_protected = is_protected_by_ally(json, tr, tc, my_color, my_rank, piece);
                            
                            int score = 0;
                            if (future_threatened) {
                                int trade_profit = target_val - my_val;
                                if (is_protected) trade_profit += (my_val / 2); // 鐵索連環加成
                                if (trade_profit < 0) score -= 5000; 
                                else score += trade_profit + 500; 
                            } else {
                                score += target_val + 300; 
                            }

                            if (currently_threatened && score > -4000) score += my_val; 

                            if (score > best_score) {
                                best_score = score;
                                sprintf(best_action, "%d %d %d %d\n", r, c, tr, tc);
                            }
                        }
                    }
                }
            }

            // B-2: 評估一般移動與相鄰吃子
            int dr[] = {-1, 1, 0, 0}, dc[] = {0, 0, -1, 1};
            for (int j = 0; j < 4; j++) {
                int nr = r + dr[j], nc = c + dc[j];
                if (nr >= 0 && nr < 4 && nc >= 0 && nc < 8) {
                    get_piece_at(json, nr * 8 + nc, target);
                    int future_threatened = is_square_threatened(json, nr, nc, opp_color, my_rank, piece);
                    int is_protected = is_protected_by_ally(json, nr, nc, my_color, my_rank, piece);

                    // 狀況 1：可以吃子
                    if (strstr(target, opp_color) && !is_cannon) {
                        int t_rank = get_rank(target);
                        int can_eat = 0;
                        if (strstr(piece, "Soldier") && strstr(target, "King")) can_eat = 1;
                        else if (strstr(piece, "King") && strstr(target, "Soldier")) can_eat = 0;
                        else if (my_rank >= t_rank) can_eat = 1;

                        if (can_eat) {
                            int target_val = get_piece_value(target);
                            int score = 0;
                            
                            if (future_threatened) {
                                int trade_profit = target_val - my_val;
                                if (is_protected) trade_profit += (my_val / 2);
                                if (trade_profit < 0) score -= 5000; 
                                else score += trade_profit;
                            } else {
                                score += target_val; 
                            }
                            
                            if (currently_threatened && score > -4000) score += my_val; 
                            if (is_protected) score += 50; 
                            // ==========================================
                            // 🌟 【Minimax 淺層預判與防震盪核心】 🌟
                            // ==========================================
                            
                            // 1. Minimax：扣除對手的最佳反擊分數
                            int opp_best_counter = get_opponent_best_counter(json, i, nr * 8 + nc, piece, opp_color, my_color);
                            score -= (opp_best_counter * 2); // 放大對手反擊的扣分比重，讓 AI 極度厭惡被吃

                            // 2. 禁忌軌跡 (Tabu Search)：打破完美的僵局對稱
                            // 如果這步棋剛好是「退回上一步的位置」，給予懲罰，逼迫 AI 另尋他路
                            if ((nr * 8 + nc) == last_from_idx && i == last_to_idx) {
                                score -= 800; // 強烈建議不要繞圈圈
                            }
                            // ==========================================
                            if (score > best_score) {
                                best_score = score;
                                sprintf(best_action, "%d %d %d %d\n", r, c, nr, nc);
                            }
                        }
                    }
                    // --- 策略 B-2 狀況 2：移動到空地 (蟒蛇窒息法) ---
                    else if (strcmp(target, "Null") == 0) {
                        int score = 0;
                        
                        if (future_threatened) {
                            if (is_protected && my_val < 300) score -= 100;
                            else score -= 5000; 
                        } else {
                            score += pos_bonus[nr][nc]; 
                            if (is_protected) score += 80; 
                            
                            int footprint = get_threat_footprint(json, nr, nc, opp_color, my_rank, piece);
                            score += (footprint * 150); 

                            // 【奇異點邏輯】：窒息壓迫！走到這格後，能不能封死敵方大子的退路？
                            if (enemy_vip_r != -1) {
                                int dist = get_distance(nr, nc, enemy_vip_r, enemy_vip_c);
                                score -= (dist * 5); 
                                
                                // 預判敵方主將的自由度
                                int enemy_mobility = get_enemy_mobility(json, enemy_vip_r, enemy_vip_c, my_color, get_rank("King")); // 簡化判斷
                                // 如果敵方主將無路可逃 (mobility == 0)，給予極高獎勵，準備將死！
                                if (enemy_mobility <= 1 && dist <= 2) {
                                    score += 800; // 形成包圍網！
                                }
                            }
                        }

                        if (currently_threatened && !future_threatened) {
                            score += my_val * 3; 
                        }

                        score += rand() % 5; 
                        // ==========================================
                        // 🌟 【Minimax 淺層預判與防震盪核心】 🌟
                        // ==========================================
                        
                        // 1. Minimax：扣除對手的最佳反擊分數
                        int opp_best_counter = get_opponent_best_counter(json, i, nr * 8 + nc, piece, opp_color, my_color);
                        score -= (opp_best_counter * 2); // 放大對手反擊的扣分比重，讓 AI 極度厭惡被吃

                        // 2. 禁忌軌跡 (Tabu Search)：打破完美的僵局對稱
                        // 如果這步棋剛好是「退回上一步的位置」，給予懲罰，逼迫 AI 另尋他路
                        if ((nr * 8 + nc) == last_from_idx && i == last_to_idx) {
                            score -= 800; // 強烈建議不要繞圈圈
                        }
                        // ==========================================
                        if (score > best_score) {
                            best_score = score;
                            sprintf(best_action, "%d %d %d %d\n", r, c, nr, nc);
                        }
                    }
                }
            }
        }
    }

    // 執行分數最高的動作
    if (strlen(best_action) > 0) {
        // [新增] 解析決定好的動作，更新歷史軌跡
        int r1, c1, r2, c2;
        if (sscanf(best_action, "%d %d %d %d", &r1, &c1, &r2, &c2) == 4) {
            last_from_idx = r1 * 8 + c1;
            last_to_idx = r2 * 8 + c2;
        } else {
            // 如果是翻牌，清除軌跡記憶
            last_from_idx = -1; 
            last_to_idx = -1;
        }

        printf("AI (%s) final assessment score: %d, action: %s", my_role_ab, best_score, best_action);
        Sleep(1500); 
        send_action(best_action);
    }
}

int main() {
    srand(time(NULL));
    char board_data[4000];
    int last_total_moves = -1;

    if (init_connection() != 0) return 1;
    auto_join_room();

    char my_role_ab[2] = "";
    if (strcmp(_assigned_role, "first") == 0) strcpy(my_role_ab, "A");
    else if (strcmp(_assigned_role, "second") == 0) strcpy(my_role_ab, "B");

    while (1) {
        receive_update(board_data, 4000);
        printf("%s", board_data);
        if (strlen(board_data) == 0) break;
        if (strstr(board_data, "UPDATE")) {
            // 解析總步數，避免重複處理相同的狀態
            int current_total_moves = -1;
            char* moves_p = strstr(board_data, "\"total_moves\": ");
            if (moves_p) {
                sscanf(moves_p + 15, "%d", &current_total_moves);
            }

            const char* turn_role_p = strstr(board_data, "\"current_turn_role\": \"");
            if (turn_role_p) {
                turn_role_p += 22;
                char current_turn_role[2] = { turn_role_p[0], '\0' };
                
                // 只有在回合匹配且狀態是新的時候才動作
                if (strcmp(current_turn_role, my_role_ab) == 0 && current_total_moves != last_total_moves) {
                    printf("It's my turn (Role %s, Move %d). Thinking...\n", my_role_ab, current_total_moves);
                    make_move(board_data, my_role_ab);
                    last_total_moves = current_total_moves;
                }
            }
        }
    }
    close_connection();
    return 0;
}