/*

  @PoC: Toggle analysis implemented on afl-showmap.

  1. Input:  target binary + a dir of input files. -- dir
  2. Output: toggle whose flags are set as 1.      -- file

 */

#define AFL_MAIN
#define AFL_SHOWTOG

#include "config.h"
#include "afl-fuzz.h"
#include "types.h"
#include "debug.h"
#include "alloc-inl.h"
#include "hash.h"
#include "sharedmem.h"
#include "forkserver.h"
#include "common.h"
#include "hash.h"

#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <errno.h>
#include <signal.h>
#include <dirent.h>
#include <fcntl.h>
#include <limits.h>

#include <dirent.h>
#include <sys/wait.h>
#include <sys/time.h>
#ifndef USEMMAP
  #include <sys/shm.h>
#endif
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/resource.h>

/* Lots of globals */

static afl_state_t *afl;

static char *stdin_file;               /* stdin file                        */

static u8 *in_dir = NULL,              /* input folder                      */
    *out_file = NULL,                  /* output file or directory          */
        *at_file = NULL,               /* Substitution string for @@        */
            *in_filelist = NULL;       /* input file list                   */

static u8 outfile[PATH_MAX];           /* used in execute_testcases         */

static u8 *in_data,                    /* Input data                        */
    *coverage_map;                     /* Coverage map                      */

// Globals for stats.
static u32 tcnt, highest;              /* tuple content information         */
static u32 in_len;                     /* Input data length                 */

static bool quiet_mode,                /* Hide non-essential messages?      */
    edges_only,                        /* Ignore hit counts?                */
    raw_instr_output,                  /* Do not apply AFL filters          */
    cmin_mode,                         /* Generate output in afl-cmin mode? */
    binary_mode,                       /* Write output as a binary map      */
    keep_cores,                        /* Allow coredumps?                  */
    remove_shm = true,                 /* remove shmem?                     */
    collect_coverage,                  /* collect coverage                  */
    have_coverage,                     /* have coverage?                    */
    no_classify,                       /* do not classify counts            */
    debug,                             /* debug mode                        */
    print_filenames,                   /* print the current filename        */
    wait_for_gdb;

static volatile u8 stop_soon,          /* Ctrl-C pressed?                   */
    child_crashed;                     /* Child crashed?                    */

static sharedmem_t       shm;
static afl_forkserver_t *fsrv;
static u32 map_size = POC_TOG_MAP_SIZE, timed_out = 0;


/* Show banner. */

static void show_banner(void) {

  SAYF(cCYA "afl-showtog@PoC" VERSION cRST "\n");

}

/* Display usage hints. */

static void usage(u8 *argv0) {

  show_banner();

  SAYF(
      "\n%s [ options ] -- /path/to/target_app [ ... ]\n\n"

      "Required parameters:\n"
      "  -i dir     - process all input files below this directory\n"
      "  -o file    - file to write the trace data to\n\n"

      "Execution control settings:\n"
      "  -m megs    - memory limit for child process (default: none)\n"
      "  -t msec    - timeout for each run (default: 1000ms)\n\n"

      "Other settings:\n"
      "  -q         - sink program's output and don't show messages\n"
      "  -h         - show this help message\n"
      "\n"      
      "@PoC: This tool run given inputs and displays oggles triggered by \n"
      "      these input files.\n"
      ,
      argv0, doc_path);

  exit(1);

}

/* Execute target application. */
// Seems run once
static void showmap_run_target_forkserver(afl_forkserver_t *fsrv, u8 *mem,
                                          u32 len) {

  pre_afl_fsrv_write_to_testcase(fsrv, mem, len);

  if (!quiet_mode) { SAYF("-- Program output begins --\n" cRST); }

  if (afl_fsrv_run_target(fsrv, fsrv->exec_tmout, &stop_soon) ==
      FSRV_RUN_ERROR) {

    FATAL("Error running target");

  }

  if (fsrv->trace_bits[0]) {

    fsrv->trace_bits[0] -= 1;
    have_coverage = true;

  } else {

    have_coverage = false;

  }

  if (!no_classify) { classify_counts(fsrv); }

  if (!quiet_mode) { SAYF(cRST "-- Program output ends --\n"); }

  if (!fsrv->last_run_timed_out && !stop_soon &&
      WIFSIGNALED(fsrv->child_status)) {

    child_crashed = true;

  } else {

    child_crashed = false;

  }

  if (!quiet_mode) {

    if (timed_out || fsrv->last_run_timed_out) {

      SAYF(cLRD "\n+++ Program timed off +++\n" cRST);
      timed_out = 0;

    } else if (stop_soon) {

      SAYF(cLRD "\n+++ Program aborted by user +++\n" cRST);

    } else if (child_crashed) {

      SAYF(cLRD "\n+++ Program killed by signal %u +++\n" cRST,
           WTERMSIG(fsrv->child_status));

    }

  }

  if (stop_soon) {

    SAYF(cRST cLRD "\n+++ afl-showmap folder mode aborted by user +++\n" cRST);
    exit(1);

  }

}

// The true execution of test cases in batch.
u32 execute_testcases(u8 *dir) {

  struct dirent **nl;
  s32             nl_cnt, subdirs = 1;
  u32             i, done = 0;
  u8              val_buf[2][STRINGIFY_VAL_SIZE_MAX];

  if (!be_quiet) { ACTF("Scanning '%s'...", dir); }

  /* We use scandir() + alphasort() rather than readdir() because otherwise,
     the ordering of test cases would vary somewhat randomly and would be
     difficult to control. */

  nl_cnt = scandir(dir, &nl, NULL, alphasort);

  if (nl_cnt < 0) { return 0; }

  for (i = 0; i < (u32)nl_cnt; ++i) {

    struct stat st;

    u8 *fn2 = alloc_printf("%s/%s", dir, nl[i]->d_name);

    if (lstat(fn2, &st) || access(fn2, R_OK)) {

      PFATAL("Unable to access '%s'", fn2);

    }

    /* obviously we want to skip "descending" into . and .. directories,
       however it is a good idea to skip also directories that start with
       a dot */
    if (subdirs && S_ISDIR(st.st_mode) && nl[i]->d_name[0] != '.') {

      free(nl[i]);                                           /* not tracked */
      done += execute_testcases(fn2);
      ck_free(fn2);
      continue;

    }

    if (!S_ISREG(st.st_mode) || !st.st_size) {

      free(nl[i]);
      ck_free(fn2);
      continue;

    }

    if (st.st_size > MAX_FILE && !be_quiet && !quiet_mode) {

      WARNF("Test case '%s' is too big (%s, limit is %s), partial reading", fn2,
            stringify_mem_size(val_buf[0], sizeof(val_buf[0]), st.st_size),
            stringify_mem_size(val_buf[1], sizeof(val_buf[1]), MAX_FILE));

    }

    if (!collect_coverage)
      snprintf(outfile, sizeof(outfile), "%s/%s", out_file, nl[i]->d_name);

    free(nl[i]);

    if (read_file(fn2)) {

      if (wait_for_gdb) {

        fprintf(stderr, "exec: gdb -p %d\n", fsrv->child_pid);
        fprintf(stderr, "exec: kill -CONT %d\n", getpid());
        kill(0, SIGSTOP);

      }

      showmap_run_target_forkserver(fsrv, in_data, in_len);
      ck_free(in_data);
      ++done;

      if (child_crashed && debug) { WARNF("crashed: %s", fn2); }

      if (collect_coverage)
        analyze_results(fsrv);
      else
        tcnt = write_results_to_file(fsrv, outfile);

    }

  }

  free(nl);                                                  /* not tracked */
  return done;

}


/* Main entry point */

int main(int argc, char **argv_orig, char **envp) {

  s32  opt, i;
  bool mem_limit_given = false, timeout_given = false, unicorn_mode = false,
       use_wine = false;
  char **use_argv;
  char **argv = argv_cpy_dup(argc, argv_orig);

  // Prepare frsv early as many options are relevant to it. 
  afl_forkserver_t fsrv_var = {0};
  fsrv = &fsrv_var;
  afl_fsrv_init(fsrv);
  map_size = POC_TOG_MAP_SIZE;
  fsrv->map_size = map_size;

  while ((opt = getopt(argc, argv, "+i:I:o:f:m:t:AeqCZOH:QUWbcrshXY")) > 0) {

    switch (opt) {

      case 'i':
        if (in_dir) { FATAL("Multiple -i options not supported"); }
        in_dir = optarg;
        break;

      case 'o':

        if (out_file) { FATAL("Multiple -o options not supported"); }
        out_file = optarg;
        break;


      case 'm': {

        u8 suffix = 'M';

        if (mem_limit_given) { FATAL("Multiple -m options not supported"); }
        mem_limit_given = true;

        if (!optarg) { FATAL("Wrong usage of -m"); }

        if (!strcmp(optarg, "none")) {

          fsrv->mem_limit = 0;
          break;

        }

        if (sscanf(optarg, "%llu%c", &fsrv->mem_limit, &suffix) < 1 ||
            optarg[0] == '-') {

          FATAL("Bad syntax used for -m");

        }

        switch (suffix) {

          case 'T':
            fsrv->mem_limit *= 1024 * 1024;
            break;
          case 'G':
            fsrv->mem_limit *= 1024;
            break;
          case 'k':
            fsrv->mem_limit /= 1024;
            break;
          case 'M':
            break;

          default:
            FATAL("Unsupported suffix or bad syntax for -m");

        }

        if (fsrv->mem_limit < 5) { FATAL("Dangerously low value of -m"); }

        if (sizeof(rlim_t) == 4 && fsrv->mem_limit > 2000) {

          FATAL("Value of -m out of range on 32-bit systems");

        }

      }

      break;

      case 't':

        if (timeout_given) { FATAL("Multiple -t options not supported"); }
        timeout_given = true;

        if (!optarg) { FATAL("Wrong usage of -t"); }

        if (strcmp(optarg, "none")) {

          fsrv->exec_tmout = atoi(optarg);

          if (fsrv->exec_tmout < 20 || optarg[0] == '-') {

            FATAL("Dangerously low value of -t");

          }

        } else {

          // The forkserver code does not have a way to completely
          // disable the timeout, so we'll use a very, very long
          // timeout instead.
          WARNF(
              "Setting an execution timeout of 120 seconds ('none' is not "
              "allowed).");
          fsrv->exec_tmout = 120 * 1000;

        }

        break;

      case 'q':

        quiet_mode = true;
        break;

      case 'h':
        usage(argv[0]);
        return -1;
        break;

      default:
        usage(argv[0]);

    }

  } // -- End of CLI option parsing.

  // Show usage when no arg is given. 
  if (optind == argc || !out_file) { usage(argv[0]); }

  log_PoC("in_dir %s", in_dir);
  log_PoC("out_file %s", out_file);
  log_PoC("argv[optind] %s", argv[optind]);
  log_PoC("optind %d", optind);
  log_PoC("argc %d", argc);  // argc > optind + 1, seems `--` and `@@` are not counted.

  // Attach target_path
  fsrv->target_path = find_binary(argv[optind]);

  // Create TOG_FLAG SHM and attach to frsv->trace_bits.
  fsrv->trace_bits = poc_shm_init(&shm, map_size);

  if (!quiet_mode) {

    show_banner();
    ACTF("Executing '%s'...", fsrv->target_path);

  }

  if (in_dir || in_filelist) {

    /* If we don't have a file name chosen yet, use a safe default. */
    u8 *use_dir = ".";

    if (access(use_dir, R_OK | W_OK | X_OK)) {

      use_dir = get_afl_env("TMPDIR");
      if (!use_dir) { use_dir = "/tmp"; }

    }

    stdin_file = at_file ? strdup(at_file)
                         : (char *)alloc_printf("%s/.afl-showtog-temp-%u",
                                                use_dir, (u32)getpid());
    unlink(stdin_file);

    // If @@ are in the target args, replace them and also set use_stdin=false.
    // @PoC: Replace the `@@` with the absolute path of stdin_file.
    detect_file_args(argv + optind, stdin_file, &fsrv->use_stdin);

    fsrv->dev_null_fd = open("/dev/null", O_RDWR);
    if (fsrv->dev_null_fd < 0) { PFATAL("Unable to open /dev/null"); }

    fsrv->out_file = stdin_file;
    fsrv->out_fd =
        open(stdin_file, O_RDWR | O_CREAT | O_EXCL, DEFAULT_PERMISSION);
    if (fsrv->out_fd < 0) { PFATAL("Unable to create '%s'", stdin_file); }

  } else {

    // If @@ are in the target args, replace them and also set use_stdin=false.
    detect_file_args(argv + optind, at_file, &fsrv->use_stdin);

  }

  // log_PoC("fsrv->out_file %s", fsrv->out_file);
  // log_PoC("argv[x] %s", argv[7]); 
  // log_PoC("fsrv->cs_mode %u", fsrv->cs_mode);

  // Works under the normal mode (I mean not qemu, nyx, cs...etc.)
  // use_argv: bin_target + its running parameters, i.e, Fuzz target CMD.
  // So afl use a same cmd but a mutable temp file as input?
  use_argv = argv + optind;
  log_PoC("fsrv->use_stdin %u", fsrv->use_stdin);
  log_PoC("use_argv[0] %s", use_argv[0]); 
  log_PoC("use_argv[1] %s", use_argv[1]); 

  // // Initialize afl variables.
  // afl = calloc(1, sizeof(afl_state_t)); // @PoC: orig place in showmap.

  // Why suddenly set frsv's via envs?
  if (getenv("AFL_FORKSRV_INIT_TMOUT")) {
    s32 forksrv_init_tmout = atoi(getenv("AFL_FORKSRV_INIT_TMOUT"));
    if (forksrv_init_tmout < 1) {
      FATAL("Bad value specified for AFL_FORKSRV_INIT_TMOUT");
    }
    fsrv->init_tmout = (u32)forksrv_init_tmout;
  }
  if (getenv("AFL_CRASH_EXITCODE")) {
    long exitcode = strtol(getenv("AFL_CRASH_EXITCODE"), NULL, 10);
    if ((!exitcode && (errno == EINVAL || errno == ERANGE)) ||
        exitcode < -127 || exitcode > 128) {
      FATAL("Invalid crash exitcode, expected -127 to 128, but got %s",
            getenv("AFL_CRASH_EXITCODE"));
    }
    fsrv->uses_crash_exitcode = true;
    // WEXITSTATUS is 8 bit unsigned
    fsrv->crash_exitcode = (u8)exitcode;
  }

  // Initialize afl variables.
  afl = calloc(1, sizeof(afl_state_t));
  
#ifdef __linux__
  if (!fsrv->nyx_mode && (in_dir || in_filelist)) {
    // The actual line under normal mode.
    // Check whether the target is truely a executable binary. 
    (void)check_binary_signatures(fsrv->target_path);
  }
#else
  if (in_dir) { (void)check_binary_signatures(fsrv->target_path); }
#endif

  // <!> Configuration of shmfuzz and cmplog_mode, but I don't copy.

  // SIGTERM under normal mode. SIGKILL under qemu, nyx, and unicorn.
  configure_afl_kill_signals(fsrv, NULL, NULL, SIGTERM);
  log_PoC("SIGTERM %u, SIGKILL %u", SIGTERM, SIGKILL);
  log_PoC("fsrv->fsrv_kill_signal %u", fsrv->fsrv_kill_signal);



  
  return 0;
}



