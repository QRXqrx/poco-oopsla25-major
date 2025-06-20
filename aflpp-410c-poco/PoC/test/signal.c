#include <stdio.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <unistd.h>

int main() {
    pid_t pid = fork(); // 创建子进程

    if (pid < 0) {
        perror("Fork failed");
        exit(1);
    } else if (pid == 0) {
        // 子进程，执行退出操作
        exit(1); // 模拟正常退出，返回值为 1
    } else {
        // 父进程，等待子进程结束
        int status;
        waitpid(pid, &status, 0);

        // 打印退出码
        if (WIFSIGNALED(status)) {
            printf("The child process was terminated by a signal.\n");
        } else {
            printf("Unknown exit reason.\n");
        }
    }

    return 0;
}
