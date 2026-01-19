#include <stdio.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <unistd.h>

int main() {
    pid_t pid = fork(); // Create a child process

    if (pid < 0) {
        perror("Fork failed");
        exit(1);
    } else if (pid == 0) {
        // Child process: perform exit operation
        exit(1); // Simulate normal exit with return code 1
    } else {
        // Parent process: wait for the child process to finish
        int status;
        waitpid(pid, &status, 0);

        // Print the exit code
        if (WIFSIGNALED(status)) {
            printf("The child process was terminated by a signal.\n");
        } else {
            printf("Unknown exit reason.\n");
        }
    }

    return 0;
}
