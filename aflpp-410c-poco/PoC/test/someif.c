//
// We need an input file whose content starts with "hello"
// to reach and trigger the error representing with abort().
//
#include <stdio.h>
#include <stdlib.h>

// 2MB
#define MAX_BUFFER 1 << 21

int main(void) {

  char  input[MAX_BUFFER];

  printf("Please input a string: ");
  scanf("%s", input);

  if (input[0] == 'h') {
    printf("h\n");
    if (input[1] == 'e') {
      printf("he\n");
      if (input[2] == 'l') {
        printf("hel\n");
        if (input[3] == 'l') {
          printf("hell\n");
          if (input[4] == 'o') {
            // abort(); // Reach buggy location and crash!
              abort();
          }
        }
      }
    }
  }

  printf("input '%s' is safe :-) \n", input);

  return 0;

}
