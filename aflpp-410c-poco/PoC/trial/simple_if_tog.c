#include "stdio.h"
#include "stdlib.h"

int main(int argc, char **argv) {

    printf("argc=%d\n", argc);

    if (getenv("TOG") || argc > 5) {
        printf("Get into the branch.\n");
    }

}