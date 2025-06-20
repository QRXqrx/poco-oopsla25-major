#include "stdio.h"

void usage() {
    printf("Usage: <bin> p1 p2 p3\n");
}

int main(int argc, char **argv) {

    if (argc <= 1) {
        usage();
        return 0;
    }

    printf("Into normal logic\n");

    return 0;
}
