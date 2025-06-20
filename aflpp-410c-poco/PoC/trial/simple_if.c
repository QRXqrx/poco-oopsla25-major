#include "stdio.h"

int main(int argc, char **argv) {

    printf("argc=%d\n", argc);

    if (argc > 5) {
        printf("Get into the branch.\n");
    }

}