//
// Test PoC instrumentation
// hello_poc has 6 toggles (1~6), 0 is not used.
//

#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <signal.h>
#include <memory.h>
#include <time.h>
#include <sys/shm.h>
#include <sys/wait.h>

#define AFL_SHM_ENV_VAR "__AFL_SHM_ID"
#define POC_SHM_ENV_VAR "__POC_SHM_ID"
#define LOG_TITLE       "[PoC-TEST]"
#define cGRN            "\x1b[0;32m"
#define cRST            "\x1b[0m"
#define ECODE           10086
#define ENV_STR_SIZE    100

typedef unsigned char u8;
typedef unsigned int  u32;
typedef int           s32;


static u8 shm_env_str[ENV_STR_SIZE], afl_shm_env_str[ENV_STR_SIZE];


int main(int argc, char **argv) {

  if (argc < 2) {
    printf("Usage: testpoc <IN_FOR_POC>\n");
    return 0;
  }
  char  *input    = argv[1];
  u32   shm_size  = 65536;
  s32   shm_id;
  u8    *shm;

  // Get shm
  shm_id = shmget(IPC_PRIVATE, shm_size, IPC_CREAT | IPC_EXCL | 0600);
  if (shm_id == -1) {
    shmctl(shm_id, IPC_RMID, 0);
    exit(ECODE);
  }

  // Attach shm
  shm = shmat(shm_id, NULL, 0);

  // Build env str
  snprintf(shm_env_str, ENV_STR_SIZE, "%s=%u", POC_SHM_ENV_VAR, shm_id);
  printf("%s shm_env_str %s\n", LOG_TITLE, shm_env_str);

  // char * const envp[] = {"POC_DEBUG=1", shm_env_str, NULL};
  // int ret = execle("./hello_poc", "hello_poc", "helle", NULL, envp);

  pid_t pid = fork();

  switch(pid){
    // PID == -1 error
    case -1:
        perror("fork()");
        exit(-1);
    
    // PID == 0 subprogram
    case 0:
      printf("====================================\n");
      printf("I'm Child process\n");
      printf("Child's PID is %d\n", getpid());
      printf("shm_env_str %s\n", shm_env_str);
      char * const envp[] = {"POC_DEBUG=1", shm_env_str, NULL};
      // int ret = execle("./hello_poc", "hello_poc", "helle", NULL, envp);
      int ret = execle("./hello_poc", "hello_poc", input, NULL, envp);
      printf("====================================\n");
      break;
    
    // PID > 0 parent program
    default:
      printf("====================================\n");
      printf("I'm Parent process\n");
      printf("Parent's PID is %d\n", getpid());
      printf("shm_env_str %s\n", shm_env_str);
      printf("shm[0]=%u\n", shm[0]);
      printf("====================================\n");
  }

  // Wait child process to stop
  int status = 0;
  wait(&status);
  if (WIFEXITED(status)) {
    printf("Child process return %d\n", WEXITSTATUS(status));
  }

  // printf("shm[0]=%u\n", shm[0]);
  printf("=========== Check PoC SHM for input: `%s`\n", input);
  for (u32 i = 1 ; i < shm_size; i++) {
    if (shm[i]) printf("TOG_%u, shm[%u]=%u\n", i, i, shm[i]);
  }

  // Free
  shmdt(shm);
  shmctl(shm_id, IPC_RMID, 0);

  printf("%s Say sth at the end :-) \n", LOG_TITLE);

  return 0;
  
}

