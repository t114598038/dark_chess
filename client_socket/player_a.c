#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <winsock2.h>

#pragma comment(lib, "ws2_32.lib")

#define SERVER_IP "127.0.0.1"
#define PORT 8888

int main() {
    WSADATA wsa;
    SOCKET s;
    struct sockaddr_in server;
    char message[2000], server_reply[2000];

    printf("\nInitialising Winsock...");
    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) {
        printf("Failed. Error Code : %d", WSAGetLastError());
        return 1;
    }

    if ((s = socket(AF_INET, SOCK_STREAM, 0)) == INVALID_SOCKET) {
        printf("Could not create socket : %d", WSAGetLastError());
    }

    server.sin_addr.s_addr = inet_addr(SERVER_IP);
    server.sin_family = AF_INET;
    server.sin_port = htons(PORT);

    if (connect(s, (struct sockaddr *)&server, sizeof(server)) < 0) {
        puts("Connect error");
        return 1;
    }

    puts("Connected to Dark Chess Server\n");
    puts("Commands:");
    puts("  JOIN <num>  (Join a room, e.g., JOIN 123)");
    puts("  x y         (Flip piece at x, y)");
    puts("  x1 y1 x2 y2 (Move piece from x1,y1 to x2,y2)");

    while (1) {
        printf("\nEnter action: ");
        fgets(message, 2000, stdin);

        if (send(s, message, strlen(message), 0) < 0) {
            puts("Send failed");
            break;
        }

        int recv_size;
        if ((recv_size = recv(s, server_reply, 2000, 0)) == SOCKET_ERROR) {
            puts("Recv failed");
            break;
        }

        server_reply[recv_size] = '\0';
        printf("Server: %s", server_reply);
    }

    closesocket(s);
    WSACleanup();
    return 0;
}
