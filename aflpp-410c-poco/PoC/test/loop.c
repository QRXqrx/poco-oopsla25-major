//
// We need an input file whose content starts with "hello"
// to reach and trigger the error representing with abort().
//
#include <stdio.h>
#include <stdlib.h>

// 2MB
#define MAX_BUFFER 1 << 21

int main(void) {

  int  input;

  printf("Please input a number: ");
  scanf("%d", &input);

  while(input > 0){
    printf("we are going to print %d \n",input--);
  }
  // afl instrument will split a new conditonal br



  return 0;

}
