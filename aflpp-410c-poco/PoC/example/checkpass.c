//
// We need an input file whose content starts with "hello"
// to reach and trigger the error representing with abort().
//
#include <stdio.h>
#include <stdlib.h>


int main(int argc, const char **argv) {


  if(argc<=1){
    puts("this message will be shown only if toggle is set\n");
  }
  return 0;

}
