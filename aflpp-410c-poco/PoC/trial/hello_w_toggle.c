//
// We need an input file whose content starts with "hello"
// to reach and trigger the error representing with abort().
//
// Imitating the conditional guards are injected with toggles,
// which can be controlled through a set of ENVs.
//
#include <stdio.h>
#include <stdlib.h>

// 2MB
#define MAX_BUFFER 1 << 21

typedef unsigned u8;

// Prepare toggles for each condition.
u8 TOGGLE_h1 = 0;
u8 TOGGLE_e2 = 0;
u8 TOGGLE_l3 = 0;
u8 TOGGLE_l4 = 0;
u8 TOGGLE_o5 = 0;

void poc_set_toggles() {
    TOGGLE_h1 = getenv("TOGGLE_h1") != NULL;
    TOGGLE_e2 = getenv("TOGGLE_e2") != NULL;
    TOGGLE_l3 = getenv("TOGGLE_l3") != NULL;
    TOGGLE_l4 = getenv("TOGGLE_l4") != NULL;
    TOGGLE_o5 = getenv("TOGGLE_o5") != NULL;
}


int main(void) {
    
  // Set toggles
  poc_set_toggles();
    
//  // Echo the toggles
//  printf("TOGGLE_h1=%u\n", TOGGLE_h1);
//  printf("TOGGLE_e2=%u\n", TOGGLE_e2);
//  printf("TOGGLE_l3=%u\n", TOGGLE_l3);
//  printf("TOGGLE_l4=%u\n", TOGGLE_l4);
//  printf("TOGGLE_o5=%u\n", TOGGLE_o5);

  // Original hello logics
  char  input[MAX_BUFFER];

  printf("Please input a string: ");
  scanf("%s", input);

  // Inject toggles
  if (TOGGLE_h1 || input[0] == 'h') {
    printf("h\n");
    if (TOGGLE_e2 || input[1] == 'e') {
      printf("he\n");
      if (TOGGLE_l3 || input[2] == 'l') {
        printf("hel\n");
        if (TOGGLE_l4 || input[3] == 'l') {
          printf("hell\n");
          if (TOGGLE_o5 || input[4] == 'o') {
            abort(); // Reach buggy location and crash!
          }
        }
      }
    }
  }
            
  printf("input '%s' is safe :-) \n", input);

  return 0;

}
