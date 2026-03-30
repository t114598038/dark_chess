#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>

#define SERVER_IP "127.0.0.1"
#define PORT 8888

int main() {
    int s;
    struct sockaddr_in server;
    char message[2000], server_reply[2000];

    if ((s = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        perror("Could not create socket");
        return 1;
    }

    server.sin_addr.s_addr = inet_addr(SERVER_IP);
    server.sin_family = AF_INET;
    server.sin_port = htons(PORT);

    if (connect(s, (struct sockaddr *)&server, sizeof(server)) < 0) {
        perror("Connect error");
        return 1;
    }

    puts("Connected to Dark Chess Server\n");
    puts("Commands:");
    puts("  JOIN <num>       (Join a room, e.g., JOIN 123)");
    puts("  x y              (Flip piece at x, y)");
    puts("  x1 y1 x2 y2     (Move piece from x1,y1 to x2,y2)");

    while (1) {
        printf("\nEnter action: ");
        if (fgets(message, sizeof(message), stdin) == NULL) {
            break;
        }

        if (send(s, message, strlen(message), 0) < 0) {
            perror("Send failed");
            break;
        }

        int recv_size = recv(s, server_reply, sizeof(server_reply) - 1, 0);
        if (recv_size <= 0) {
            if (recv_size == 0)
                puts("Server closed connection");
            else
                perror("Recv failed");
            break;
        }

        server_reply[recv_size] = '\0';
        printf("Server: %s", server_reply);
    }

    close(s);
    return 0;
}
