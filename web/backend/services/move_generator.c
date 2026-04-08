#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <ctype.h>

// --- 超強健解析器：直接暴力搜尋關鍵字 ---
#ifndef min
#define min(a,b) (((a) < (b)) ? (a) : (b))
#endif

#ifndef max
#define max(a,b) (((a) > (b)) ? (a) : (b))
#endif

void get_piece_at(const char* json, int index, char* out_piece) {
    const char* p = strstr(json, "\"board\"");
    if (!p) { strcpy(out_piece, "Unknown"); return; }
    p = strchr(p, '[');
    if (!p) { strcpy(out_piece, "Unknown"); return; }
    p++;
    
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

void get_role_color(const char* json, const char* role, char* out_color) {
    // 暴力搜尋法：找 "\"B\":\"" 或 "\"B\": \"" 這種模式
    char pattern1[32], pattern2[32];
    sprintf(pattern1, "\"%s\":\"Red\"", role);
    sprintf(pattern2, "\"%s\": \"Red\"", role);
    if (strstr(json, pattern1) || strstr(json, pattern2)) {
        strcpy(out_color, "Red");
        return;
    }
    
    sprintf(pattern1, "\"%s\":\"Black\"", role);
    sprintf(pattern2, "\"%s\": \"Black\"", role);
    if (strstr(json, pattern1) || strstr(json, pattern2)) {
        strcpy(out_color, "Black");
        return;
    }
    
    strcpy(out_color, "None");
}

// --- 遊戲邏輯與權重計算 (保持不變) ---

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
    } else { return -1; }
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

int get_distance(int r1, int c1, int r2, int c2) {
    return abs(r1 - r2) + abs(c1 - c2);
}

const int pos_bonus[4][8] = {
    { 0,  5, 10, 15, 15, 10,  5,  0},
    { 5, 10, 20, 25, 25, 20, 10,  5},
    { 5, 10, 20, 25, 25, 20, 10,  5},
    { 0,  5, 10, 15, 15, 10,  5,  0}
};

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

int is_square_threatened(const char* json, int r, int c, const char* opp_color, int my_rank, const char* my_piece) {
    int dr[] = {-1, 1, 0, 0}, dc[] = {0, 0, -1, 1};
    for (int j = 0; j < 4; j++) {
        int nr = r + dr[j], nc = c + dc[j];
        if (nr >= 0 && nr < 4 && nc >= 0 && nc < 8) {
            char target[32];
            get_piece_at(json, nr * 8 + nc, target);
            if (strstr(target, opp_color) && !strstr(target, "Cannon")) {
                int t_rank = get_rank(target);
                if (strstr(target, "Soldier") && strstr(my_piece, "King")) return 1;
                if (strstr(target, "King") && strstr(my_piece, "Soldier")) continue;
                if (t_rank >= my_rank) return 1; 
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

int is_protected_by_ally(const char* json, int r, int c, const char* my_color, int my_rank, const char* my_piece) {
    int dr[] = {-1, 1, 0, 0}, dc[] = {0, 0, -1, 1};
    for (int j = 0; j < 4; j++) {
        int nr = r + dr[j], nc = c + dc[j];
        if (nr >= 0 && nr < 4 && nc >= 0 && nc < 8) {
            char ally[32];
            get_piece_at(json, nr * 8 + nc, ally);
            if (strstr(ally, my_color) && !strstr(ally, "Cannon")) {
                if (strstr(ally, "Soldier") && strstr(my_piece, "King")) continue;
                if (strstr(ally, "King") && strstr(my_piece, "Soldier")) continue;
                return 1; 
            }
        }
    }
    return 0;
}

int get_threat_footprint(const char* json, int r, int c, const char* opp_color, int my_rank, const char* my_piece) {
    int count = 0;
    int dr[] = {-1, 1, 0, 0}, dc[] = {0, 0, -1, 1};
    if (strstr(my_piece, "Cannon")) {
        for (int i = 0; i < 32; i++) {
            char target[32];
            get_piece_at(json, i, target);
            if (strstr(target, opp_color) && count_between(json, r, c, i / 8, i % 8) == 1) count += 2;
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

int get_enemy_mobility(const char* json, int er, int ec, const char* my_color, int enemy_rank) {
    int mobility = 0;
    int dr[] = {-1, 1, 0, 0}, dc[] = {0, 0, -1, 1};
    for (int j = 0; j < 4; j++) {
        int nr = er + dr[j], nc = ec + dc[j];
        if (nr >= 0 && nr < 4 && nc >= 0 && nc < 8) {
            char target[32];
            get_piece_at(json, nr * 8 + nc, target);
            if (strcmp(target, "Null") == 0 && !is_square_threatened(json, nr, nc, my_color, enemy_rank, target)) mobility++;
        }
    }
    return mobility;
}

int get_flip_ev(const char* json, int r, int c, const char* opp_color, const char* my_color) {
    int ev = 0;
    int dr[] = {-1, 1, 0, 0}, dc[] = {0, 0, -1, 1};
    for (int j = 0; j < 4; j++) {
        int nr = r + dr[j], nc = c + dc[j];
        if (nr >= 0 && nr < 4 && nc >= 0 && nc < 8) {
            char adjacent[32];
            get_piece_at(json, nr * 8 + nc, adjacent);
            if (strstr(adjacent, opp_color) && !strstr(adjacent, "Cannon")) {
                int enemy_val = get_piece_value(adjacent);
                int enemy_rank = get_rank(adjacent);
                int killers_left = (enemy_rank == 7) ? count_pieces(json, "None", "Soldier")/2 : (count_pieces(json, "None", "King")/2 + count_pieces(json, "None", "Guard")/2);
                int feeders_left = count_pieces(json, "None", "Soldier")/2 + (enemy_rank > 3 ? count_pieces(json, "None", "Horse")/2 : 0);
                ev += (killers_left * enemy_val) - (feeders_left * 150);
            }
        }
    }
    return ev / 10;
}

void get_virtual_piece_at(const char* json, int index, char* out_piece, int v_from, int v_to, const char* moved_piece) {
    if (index == v_from) strcpy(out_piece, "Null");
    else if (index == v_to) strcpy(out_piece, moved_piece);
    else get_piece_at(json, index, out_piece);
}

int count_between_virtual(const char* json, int r1, int c1, int r2, int c2, int v_from, int v_to, const char* moved_piece) {
    int count = 0;
    if (r1 == r2) {
        for (int c = min(c1, c2) + 1; c < max(c1, c2); c++) {
            char p[32]; get_virtual_piece_at(json, r1 * 8 + c, p, v_from, v_to, moved_piece);
            if (strcmp(p, "Null") != 0) count++;
        }
    } else if (c1 == c2) {
        for (int r = min(r1, r2) + 1; r < max(r1, r2); r++) {
            char p[32]; get_virtual_piece_at(json, r * 8 + c1, p, v_from, v_to, moved_piece);
            if (strcmp(p, "Null") != 0) count++;
        }
    }
    return count;
}

int get_opponent_best_counter(const char* json, int v_from, int v_to, const char* moved_piece, const char* opp_color, const char* my_color) {
    int max_opp_score = 0;
    int dr[] = {-1, 1, 0, 0}, dc[] = {0, 0, -1, 1};
    for (int i = 0; i < 32; i++) {
        char opp_p[32]; get_virtual_piece_at(json, i, opp_p, v_from, v_to, moved_piece);
        if (strstr(opp_p, opp_color)) {
            int r = i / 8, c = i % 8, prank = get_rank(opp_p);
            if (strstr(opp_p, "Cannon")) {
                for (int ti = 0; ti < 32; ti++) {
                    char tar[32]; get_virtual_piece_at(json, ti, tar, v_from, v_to, moved_piece);
                    if (strstr(tar, my_color) && count_between_virtual(json, r, c, ti/8, ti%8, v_from, v_to, moved_piece) == 1) {
                        int v = get_piece_value(tar); if (v > max_opp_score) max_opp_score = v;
                    }
                }
            } else {
                for (int j = 0; j < 4; j++) {
                    int nr = r + dr[j], nc = c + dc[j];
                    if (nr >= 0 && nr < 4 && nc >= 0 && nc < 8) {
                        char tar[32]; get_virtual_piece_at(json, nr*8+nc, tar, v_from, v_to, moved_piece);
                        if (strstr(tar, my_color)) {
                            int trank = get_rank(tar), can = 0;
                            if (strstr(opp_p, "Soldier") && strstr(tar, "King")) can = 1;
                            else if (prank >= trank && !strstr(tar, "Soldier")) can = 1;
                            if (can) { int v = get_piece_value(tar); if (v > max_opp_score) max_opp_score = v; }
                        }
                    }
                }
            }
        }
    }
    return max_opp_score;
}

int main(int argc, char* argv[]) {
    if (argc < 3) return 1;
    FILE* fp = fopen(argv[1], "r"); if (!fp) return 1;
    fseek(fp, 0, SEEK_END); long size = ftell(fp); fseek(fp, 0, SEEK_SET);
    char* json = malloc(size + 1); fread(json, 1, size, fp); json[size] = '\0'; fclose(fp);
    const char* my_role = argv[2]; int lf = (argc > 3) ? atoi(argv[3]) : -1, lt = (argc > 4) ? atoi(argv[4]) : -1;
    srand(time(NULL)); char piece[32], my_color[10], opp_color[10];
    get_role_color(json, my_role, my_color);
    fprintf(stderr, "AI DEBUG: Role=%s Color=%s\n", my_role, my_color);
    strcpy(opp_color, strcmp(my_color, "Red") == 0 ? "Black" : "Red");
    if (strcmp(my_color, "None") == 0) {
        int start[] = {11, 12, 19, 20}; 
        for(int k=0; k<4; k++) {
            get_piece_at(json, start[k], piece);
            if (strcmp(piece, "Covered") == 0) { printf("%d %d", start[k]/8, start[k]%8); free(json); return 0; }
        }
    }
    int best_s = -999999; char best_a[64] = "";
    int enemy_vip_r = -1, enemy_vip_c = -1, highest_enemy_val = 0;
    for (int k = 0; k < 32; k++) {
        char tmp[32]; get_piece_at(json, k, tmp);
        if (strstr(tmp, opp_color)) {
            int v = get_piece_value(tmp); if (v > highest_enemy_val) { highest_enemy_val = v; enemy_vip_r = k/8; enemy_vip_c = k%8; }
        }
    }
    for (int i = 0; i < 32; i++) {
        get_piece_at(json, i, piece);
        if (strcmp(piece, "Covered") == 0) {
            int r = i/8, c = i%8, s = 250 + pos_bonus[r][c] + get_flip_ev(json, r, c, opp_color, my_color);
            if (get_flip_ev(json, r, c, opp_color, my_color) > 300) s += 2000;
            if (s > best_s) { best_s = s; sprintf(best_a, "%d %d", r, c); }
        }
        if (strstr(piece, my_color)) {
            int r = i/8, c = i%8, prank = get_rank(piece), mval = get_piece_value(piece), can = strstr(piece, "Cannon")!=NULL;
            int th = is_square_threatened(json, r, c, opp_color, prank, piece);
            if (can) {
                for (int ti = 0; ti < 32; ti++) {
                    char tar[32]; get_piece_at(json, ti, tar);
                    if (strstr(tar, opp_color) && count_between(json, r, c, ti/8, ti%8) == 1) {
                        int tval = get_piece_value(tar), ft = is_square_threatened(json, ti/8, ti%8, opp_color, prank, piece), prot = is_protected_by_ally(json, ti/8, ti%8, my_color, prank, piece);
                        int s = ft ? (tval-mval+(prot?mval/2:0) < 0 ? -5000 : tval-mval+500) : tval + 300;
                        if (th && s > -4000) s += mval;
                        if (s > best_s) { best_s = s; sprintf(best_a, "%d %d %d %d", r, c, ti/8, ti%8); }
                    }
                }
            }
            int dr[] = {-1, 1, 0, 0}, dc[] = {0, 0, -1, 1};
            for (int j = 0; j < 4; j++) {
                int nr = r+dr[j], nc = c+dc[j];
                if (nr >= 0 && nr < 4 && nc >= 0 && nc < 8) {
                    char tar[32]; get_piece_at(json, nr*8+nc, tar);
                    int ft = is_square_threatened(json, nr, nc, opp_color, prank, piece), prot = is_protected_by_ally(json, nr, nc, my_color, prank, piece);
                    if (strstr(tar, opp_color) && !can) {
                        int trank = get_rank(tar);
                        if ((strstr(piece, "Soldier") && strstr(tar, "King")) || (prank >= trank && !strstr(tar, "Soldier"))) {
                            int tval = get_piece_value(tar);
                            int s = ft ? (tval-mval+(prot?mval/2:0)) : tval;
                            if (ft && s < 0) s -= 5000;
                            if (th && s > -4000) s += mval; if (prot) s += 50;
                            s -= get_opponent_best_counter(json, i, nr*8+nc, piece, opp_color, my_color) * 2;
                            if (nr*8+nc == lf && i == lt) s -= 800;
                            if (s > best_s) { best_s = s; sprintf(best_a, "%d %d %d %d", r, c, nr, nc); }
                        }
                    } else if (strcmp(tar, "Null") == 0) {
                        int s = ft ? (prot && mval < 300 ? -100 : -5000) : (pos_bonus[nr][nc] + (prot ? 80 : 0) + get_threat_footprint(json, nr, nc, opp_color, prank, piece)*150);
                        if (enemy_vip_r != -1) {
                            int dist = abs(nr-enemy_vip_r)+abs(nc-enemy_vip_c); s -= dist*5;
                            if (get_enemy_mobility(json, enemy_vip_r, enemy_vip_c, my_color, 7) <= 1 && dist <= 2) s += 800;
                        }
                        if (th && !ft) s += mval*3;
                        s += (rand()%5) - get_opponent_best_counter(json, i, nr*8+nc, piece, opp_color, my_color)*2;
                        if (nr*8+nc == lf && i == lt) s -= 800;
                        if (s > best_s) { best_s = s; sprintf(best_a, "%d %d %d %d", r, c, nr, nc); }
                    }
                }
            }
        }
    }
    printf("%s", best_a); free(json); return 0;
}
