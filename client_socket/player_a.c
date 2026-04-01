#include "dark_chess_client.h"
#include <windows.h>

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

void make_move(const char* json, const char* my_role_ab) {
    char piece[32], target[32], my_color[10], opp_color[10];
    get_role_color(json, my_role_ab, my_color);
    strcpy(opp_color, strcmp(my_color, "Red") == 0 ? "Black" : "Red");

    if (strcmp(my_color, "None") == 0) {
        // 還沒決定顏色，優先翻牌
        for (int i = 0; i < 32; i++) {
            get_piece_at(json, i, piece);
            if (strcmp(piece, "Covered") == 0) {
                char action[20];
                sprintf(action, "%d %d\n", i / 8, i % 8);
                printf("AI (%s: %s) chooses FLIP at (%d, %d)\n", _assigned_role, my_role_ab, i / 8, i % 8);
                Sleep(2000);
                send_action(action);
                return;
            }
        }
        return;
    }

    // 策略 1: 優先吃子
    for (int i = 0; i < 32; i++) {
        get_piece_at(json, i, piece);
        if (strstr(piece, my_color)) {
            int r = i / 8, c = i % 8;
            int my_rank = get_rank(piece);

            for (int ti = 0; ti < 32; ti++) {
                get_piece_at(json, ti, target);
                if (strstr(target, opp_color)) {
                    int tr = ti / 8, tc = ti % 8;
                    int t_rank = get_rank(target);
                    int dist = abs(r - tr) + abs(c - tc);

                    if (strstr(piece, "Cannon")) {
                        if (count_between(json, r, c, tr, tc) == 1) {
                            char action[32];
                            sprintf(action, "%d %d %d %d\n", r, c, tr, tc);
                            printf("AI (%s: %s) Cannon CAPTURE: (%d,%d) -> (%d,%d)\n", _assigned_role, my_role_ab, r, c, tr, tc);
                            Sleep(2000);
                            send_action(action);
                            return;
                        }
                    } else {
                        if (dist == 1) {
                            int can_eat = 0;
                            if (strstr(piece, "Soldier") && strstr(target, "King")) can_eat = 1;
                            else if (strstr(piece, "King") && strstr(target, "Soldier")) can_eat = 0;
                            else if (my_rank >= t_rank) can_eat = 1;

                            if (can_eat) {
                                char action[32];
                                sprintf(action, "%d %d %d %d\n", r, c, tr, tc);
                                printf("AI (%s: %s) CAPTURE: (%d,%d) -> (%d,%d)\n", _assigned_role, my_role_ab, r, c, tr, tc);
                                Sleep(2000);
                                send_action(action);
                                return;
                            }
                        }
                    }
                }
            }
        }
    }

    // 策略 2: 翻牌
    for (int i = 0; i < 32; i++) {
        get_piece_at(json, i, piece);
        if (strcmp(piece, "Covered") == 0) {
            char action[20];
            sprintf(action, "%d %d\n", i / 8, i % 8);
            printf("AI (%s: %s) FLIP at (%d, %d)\n", _assigned_role, my_role_ab, i / 8, i % 8);
            Sleep(2000);
            send_action(action);
            return;
        }
    }

    // 策略 3: 移動
    for (int i = 0; i < 32; i++) {
        get_piece_at(json, i, piece);
        if (strstr(piece, my_color)) {
            int r = i / 8, c = i % 8;
            int dr[] = {-1, 1, 0, 0}, dc[] = {0, 0, -1, 1};
            for (int j = 0; j < 4; j++) {
                int nr = r + dr[j], nc = c + dc[j];
                if (nr >= 0 && nr < 4 && nc >= 0 && nc < 8) {
                    get_piece_at(json, nr * 8 + nc, target);
                    if (strcmp(target, "Null") == 0) {
                        char action[32];
                        sprintf(action, "%d %d %d %d\n", r, c, nr, nc);
                        printf("AI (%s: %s) MOVE: (%d,%d) -> (%d,%d)\n", _assigned_role, my_role_ab, r, c, nr, nc);
                        Sleep(2000);
                        send_action(action);
                        return;
                    }
                }
            }
        }
    }
}

int main() {
    char board_data[4000];
    int last_total_moves = -1;

    if (init_connection() != 0) return 1;
    auto_join_room();

    char my_role_ab[2] = "";
    if (strcmp(_assigned_role, "first") == 0) strcpy(my_role_ab, "A");
    else if (strcmp(_assigned_role, "second") == 0) strcpy(my_role_ab, "B");

    while (1) {
        receive_update(board_data, 4000);
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
