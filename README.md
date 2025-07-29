# Artifacts of PoCo (OOPSLA'25)

OOPSLA'2425 Submission: *Peeling off the Cocoon: Unveiling Suppressed Golden Seeds for Mutational Greybox Fuzzing*

PoCo is a technique that aims at enhancing modern coverage-based seed selection (CSS) techniques, such as `afl-cmin`, by gradually removing obstacle conditional statements and conducting deeper seed selection. 

This repository/package contains the current version of PoCo's artifact. The artifact includes (1) the source code of the PoCo prototype, (2) part of the intermediate and final data of PoCo experiments, and (3) some key scripts for conducting experiments and data analyses. All artifacts and updates can be found at this [anonymous repository](https://anonymous.4open.science/r/poco-oopsla25-major-FB39).

Note that our submission is under a Major revision, and some of the artifacts are still under construction :construction:.

**P.S. The Name Changing History**

- PoC -> Poff -> PoCo
- All three names come from the metaphor: *Peeling off the Cocoon*.
- All three names are used interchangeably across the artifact and all refer to the proposed technique. 

## 1 Artifact Details

- `aflpp-410c-poco`: PoCo prototype built on top of AFL++ (version 4.10c). Key components are as follows:
  - `instrumentation/SanitizerCoveragePoC.so.cc`: LLVM pass implementing PoCo instrumentation.
  - `src/afl-cc.c`: A modified AFL++ compiler wrapper supporting `SanitizerCoveragePoC.so`. 
  - `PoC/res`: Utilities for running guard/toggle hierarchy construction and analysis.
  - `PoC/tools`: Utilities for running iterative seed selection.
- `data`: Raw and intermediate experimental data.
  - `captainrc-xmllint`: An example Magma configuration on the target `xmllint`.
  - `corpus/xmllint`: The universe seed corpus for `xmllint`.
  - `results`: PoCo and final fuzzing results.
  - `poco-xmllint-done`: Packed PoCo seeds for `xmllint`.
  - `xmllint-poco-raw`: Raw PoCo seeds for `xmllint`.
- `magma-poco`: A fork of Magma integrating PoCo experiements.  
- `scripts`: Key data processing scripts.
  - `cp_poco_seeds.py`: The script for packing raw PoCo seeds into one folder. 

## 2 Hardware and Software Dependencies

- **Operating System**: Ubuntu 22.04 LTS (or compatible Linux distribution)

- **CPU**: x86_64 architecture, recommended 16 cores or more

- **Memory**: Minimum 16 GB RAM

- **Disk Space**: At least 32 GB of free space

- **Python**: 3.10 or higher

- **Python Dependencies for PoCo:** See [aflpp-410c-poco/PoC/tools/requirements.txt](aflpp-410c-poco/PoC/tools/requirements.txt) 

  ```text
  networkx==3.3
  numpy==1.25.0
  pandas==2.0.3
  pydot==3.0.4
  scipy==1.15.3
  tqdm==4.64.0
  ```

- **Other Requirements**:

  - Git (>= 2.34.1)
  - make (>= 4.3) and cmake (>= 3.22.1)
  - LLVM & Clang (== 15.0.7), required for running PoCo instrumentation. You can find LLVM 15.0.7 here: [lvmorg-15.0.7](https://github.com/llvm/llvm-project/releases/tag/llvmorg-15.0.7).
  - Go (>=1.18.1), required for downloading the gllvm toolchain, including `gclang/gclang++`, and `get-bc`. You can find and download the gllvm toolchain here: [gllvm-repo](https://github.com/SRI-CSL/gllvm).
  - Docker (>= 24.0.7), required for running Magma, and recommended for building PoC-instrumented targets.

## 3 Getting Started Guide

To facilitate reproduction, we provided a Magma fork (`magma-poco`) that integrates all PoCo experimental setups, including all seed sets and a kick-to-fire experimental configuration file. Specifically, the seed sets are located under magma-poco/targets, and their suffixes correspond to the studied techniques: ALL, OptiMin, Cmin, Cmin+, and PoCo. You can start the whole fuzzing process according to the following steps:

1. Install Docker and create a non-root user within the `docker` group, which is an implicit requirement of Magma. 

   ```shell
   apt update
   apt install -y docker.io
   docker --version  # Verify
   adduser poco      # Create a non-root user named 'poco'
   usermod -aG docker poco
   usermod -aG sudo poco
   ```

2. Suppose you are in the root directory of this artifact. Copy `magma-poco` to the home directory of the newly created user `poco` Change the owner of the copied one into `poco`.
   
   ```shell
   cp -r ./magma-poco /home/poco
   cd /home/poco
   chown -R poco:poco ./magma-poco
   ```
3. As required by AFL++, we need to do some setting before running it.

   ```shell
   echo core | sudo tee /proc/sys/kernel/core_pattern
   echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
   ```


4. Switch to the user `poco`. Navigate to the folder containing the captainrc experimental configuration and start the experiments using Magma's run.sh script. The results will be written to /home/poco/poco-fuzzdata by default. If you are using a different non-root user, please remember to modify the configuration accordingly.

   ```shell
   su poco
   cd magma-poco/tools/captain
   ./run.sh
   ```
5. By default, the experimental scripts utilize all CPU cores for fuzzing. You can now let the experiments run for several hours to complete. If you want to obtain quick results, you can modify `magma-poco/tools/captain` by setting `TIMEOUT` as `1m`.


## 4 Step-by-Step Instructions

We use `xmllint`, one of the targets used in our paper, to exemplify how to get raw experimental data. We will assume that you are running a root user on Ubuntu:22.04 operating system in this section.

**Note**: Since the installation of environments (such as LLVM and gclang) can be tricky, we **highly recommend** users to use our anonymous Docker image `anon0poco/major:latest`, which includes all environments done. The image can be downloaded and run through: 

```shell
docker pull anon0poco/major:latest
docker run -it --name 'poco' anon0poco/major:latest
```

You can jump to section 4.2 using this Docker container `poco`. 

### 4.1 Preparing Environments

1. **Install essential dependencies**. Install essential tools and dependencies, such as `make`, `cmake`, and `python3`, using the `apt-get` command.

   ```shell
   sudo apt-get update
   sudo apt-get install -y build-essential \
       autoconf automake libtool pkg-config m4 \
       make cmake python3 python3-dev ...
   ```

2. **Install LLVM and Clang v15.0.7**. We recommend that users build LLVM from source. You can find the LLVM 15.0.7 release at [lvmorg-15.0.7](https://github.com/llvm/llvm-project/releases/tag/llvmorg-15.0.7) and install from source, referring to the LLVM official [guildline](https://llvm.org/docs/GettingStarted.html#getting-the-source-code-and-building-llvm).

3. **Install gllvm**. The project [gllvm](https://github.com/SRI-CSL/gllvm) provided a convenient whole program LLVM, which can ease the experiments of PoCo. They supply a simple installation using `go`. Make sure you have `go` before installing and adding the gllvm toolchain, such as `gclang` and `get-bc`, to `$PATH` after the installation. Exemplified commands are as follows:

   ```shell
   go install github.com/SRI-CSL/gllvm/cmd/...@latest
   ls ~/go/bin  # Verify your installation.
   export PATH=~/go/bin:$PATH # Add to PATH
   gclang --version
   ```

   If you see outputs like the following, then it means you have gllvm installed:

   ```text
   clang version 15.0.7  # gclang shows your clang version, better be 15.0.7
   Target: x86_64-unknown-linux-gnu
   Thread model: posix
   InstalledDir: /usr/local/bin
   ```

### 4.2 Build PoCo 

1. Make a directory `workdir` to work with. You can simply switch to it using `cd /workdir` if you are using the supplied `poco` container (instantiated from the `anon0poco/major:latest` Docker image).

   ```shell
   mkdir /workdir
   cd /workdir
   ```

2. Copy and unzip our artifacts into `workdir`. Assuming that our artifact is named `poco-artifact.zip` and is put under the `/` folder. Skip this step if you are in the `poco` container.

   ```shell
   mv /poco-artifact.zip .
   unzip ./poco-artifact.zip
   ```

3. Enter the `aflpp-410c-poco` folder and build PoCo implementation (which is built on top of [AFL++](https://github.com/AFLplusplus/AFLplusplus) version 4.10) using `clang` as the compiler and set `LLVM_CONFIG=llvm-config-15`. You can directly switch to `/workdir/aflpp-410c-poco` using the `poco` container.

   ```shell
   cd ./aflpp-410c-poco
   make clean
   CC=clang CXX=clang++ LLVM_CONFIG=llvm-config-15 make
   ```

   The build succeeds if you see outputs like the following:

   ```text
   Build Summary:
   [+] afl-fuzz and supporting tools successfully built
   [+] LLVM basic mode successfully built
   [+] LLVM mode successfully built
   [-] LLVM LTO mode could not be built, it is optional, if you want it, please install LLVM and LLD 11+. More information at instrumentation/README.lto.md on how to build it
   [+] LLVM-PoC successfully built   # Yeah! The PoCo instrumentation seems gonna to work!
   [-] gcc_mode could not be built, it is optional, install gcc-VERSION-plugin-dev to enable this
   ```

   You can also use the instructions below to double-check:

   ```shell
   AFL_LLVM_INSTRUMENT=poc ./afl-cc --version
   ```

   If you see outputs as follows, then it means `afl-cc` is using `clang` as the backend, and our PoCo instrumentation is working:

   ```text
   [PoC] Seems the PCGUARD-PoC instrumentation is on, yeah!
   afl-cc++4.10c by Michal Zalewski, Laszlo Szekeres, Marc Heuse - mode: LLVM-
   [PoC] Ok, now trying to add poc so
   [PoC] Insert an aflcc_param, `-fpass-plugin=./SanitizerCoveragePoC.so`
   Ubuntu clang version 15.0.7
   Target: x86_64-pc-linux-gnu
   Thread model: posix
   InstalledDir: /usr/lib/llvm-15/bin
   ```

4. We also need to build the toggle/guard hierarchy extraction component of PoCo, which is implemented using C++.

   ```shell
   cd ./PoC/res  # Before cd, we are under /workdir/aflpp-410c-poco
   mkdir ./build
   cmake -B ./build .  # Generate Makefile using cmake
   cd ./build
   make
   ```

   You successfully built the toggle/guard hierarchy extraction component if you saw the logs like below; you can also check its existence by running  `ls ./libtog_analysis.so`: 

   ```text
   [ 50%] Building CXX object CMakeFiles/tog_analysis.dir/tog_analysis.cc.o
   [100%] Linking CXX shared module libtog_analysis.so
   [100%] Built target tog_analysis
   ```

### 4.3 Build `xmllint_poc` 

1. Go back to the `workdir` and download the source code of `libxml2`, which is the project of `xmllint`. We use the [Magma](https://github.com/HexHive/magma) version of `libxml2` both in our experiments and for this demonstration ([Magma-libxml2](https://github.com/HexHive/magma/blob/v1.2/targets/libxml2/fetch.sh)). After creating `out`, you can just do `cd /workdir/libxml2` and jump to the next step if you are in `poco` container.

   ```shell
   cd /workdir
   mkdir ./out # To store built products.
   git clone --no-checkout https://gitlab.gnome.org/GNOME/libxml2.git
   git -C ./libxml2 checkout ec6e3efb06d7b15cf5a2328fabd3845acea4c815
   ```

2. Enter the `libxml2` source folder. Build it using `gclang` as the compiler. Make sure you have the gllvm toolchain in your `PATH`.

   ```shell
   cd ./libxml2
   make clean # Clear outdated builds.
   export PATH=~/go/bin:$PATH
   CC=gclang CXX=gclang++ ./autogen.sh --disable-shared 
   make xmllint
   ```

   If you see logs like the following, then it means the `autogen.sh` works well:

   ```text
   Done configuring
   
   Now type 'make' to compile libxml2.
   ```

   You can `ls xmllint` to see whether it is there:

   ```shell
   ls xmllint
   ```

3. Extract [bitcode](https://llvm.org/docs/BitCodeFormat.html) file from `xmllint` and move it to `/workdir/out`:

   ```shell
   get-bc xmllint
   mv xmllint.bc ../out/
   ```

   The bitcode extraction succeeds if you see the logs below:

   ```text
   Bitcode file extracted to: xmllint.bc.
   ```

4. Create PoCo-instrumented (also with AFL++ instrumentation) `xmllint` using the bitcode file and `aflpp-410c-poco/afl-cc` as the compiler. 

   ```shell
   cd ../out
   AFL_LLVM_INSTRUMENT=poc ../aflpp-410c-poco/afl-cc \
       -lz -llzma -lm ./xmllint.bc -o xmllint_poc
   ```

   Build success if you see logs like the following (you may need to wait a few more seconds after seeing these logs):

   ```text
   ...
   [PoC] Inject function: xmlListReverseWalk
   [+] Found 9 BBs and collected 3 cond br before PoC injection
   [+] Found 12 BBs after PoC injection
   [+] Instrumented 74696 locations with no collisions (non-hardened mode) of which are 3674 handled and 0 unhandled selects.
   [PoC] Instrumented 41907 toggles in total.
   [PoC] Write toggle number (41907) to dump file: /tmp/poc_tog
   ```

   You can further verify the build by checking symbols using `nm`:

   ```shell
   apt-get install -y binutils
   nm -C ./xmllint_poc | grep 'poc'
   ```

   Then you can find symbols like below:

   ```text
   000000000085042c B __poc_already_initialized
   0000000000850428 B __poc_already_initialized_shm
   0000000000840410 b __poc_area_init
   00000000005e9d48 D __poc_area_ptr
   00000000004ef610 T __poc_auto_early
   0000000000850430 B __poc_map_addr
   ```

### 4.4 Construct a toggle/guard hierarchy

1. This step corresponds to the *Guard Hierarchy Analysis* algorithm described in our manuscript. This step relies on `opt-15`, the IR-level optimization tool provided by LLVM (see [llvm-tutor](https://github.com/banach-space/llvm-tutor)), and our toggle extract component named `libtog_analysis.so`. First, make sure you have `opt-15` installed and the `libtog_analysis.so` correctly installed by:

   ```shell
   opt-15 --version  # Ubuntu LLVM version 15.0.7
   ls /workdir/aflpp-410c-poco/PoC/res/build/libtog_analysis.so
   ```

2. Extract the toggle/guard hierarchy from the bitcode file. Make sure you have set `AFLPP=/workdir/aflpp-410c-poco` because it is used in the `tog_analysis.sh`. Depending on the size of the target, this step can take a few minutes; you can go and get a cup of coffee :coffee:.

   ```shell
   cd /workdir/out
   export AFLPP=/workdir/aflpp-410c-poco
   AFL_LLVM_INSTRUMENT=poc $AFLPP/afl-cc \
       -lz -llzma -lm \
       -emit-llvm -c ./xmllint.bc \
       -o xmllint_poc.bc
   bash $AFLPP/PoC/res/tog_analysis.sh ./xmllint_poc.bc # Output to ./tog_analysis_edge
   # or you may want to output to another directory
   #TOG_ANALYSIS_PATH=<dir-to-output> bash $AFLPP/PoC/res/tog_analysis.sh ./xmllint_poc.bc
   ```

   The extraction succeeded if you see logs below; you can also check the existence by `ls ./tog_analysis_edge`:

   ```text
   BASENAME=xmllint.bc
   BC_FILE=xmllint.bc
   PASS_SO=/workdir/aflpp-410c-poco/PoC/res/build/libtog_analysis.so
   Instrumenting IR file...
   opt-15 -load-pass-plugin /workdir/aflpp-410c-poco/PoC/res/build/libtog_analysis.so --passes=tog-analysis -disable-output xmllint.bc 
   ...
   the result is written to /workdir/out/tog_analysis_edge
   Process completed
   ```

### 4.5 Select Seed Iteratively

1. This step corresponds to the *Iterative Seed Selection* (ISS) algorithm described in our manuscript. With all the intermediate products prepared, we can now run PoCo ISS using `poff_run.py`. Please make sure you have the environ `AFLPP` set before running `poff_run.py`, or it will be unable to find `afl-cmin`. 
   **Note that** this command is just for demonstration and will take hours to finish. To save time, users can just terminate it with Ctrl-C and **jump to section 4.5#step-4**.

    ```shell
   export AFLPP=/workdir/aflpp-410c-poco
   cd /workdir/out
   mkdir ./poco-raw  # For ISS output
   python3 $AFLPP/PoC/tools/poff_run.py \
     -i ../data/corpus/xmllint \
     -o ./poco-raw \
     -g ./tog_analysis_edge \
     -e ./xmllint_poc \
     -T 7200 -- @@ 
    ```

2. A breakdown of `poff_run.py` commands:

   - `-i`: The seed universe/corpus to be minimized.  
   - `-o`: The directory to output raw PoCo outputs.
   - `-g`: The toggle/guard hierarchy.
   - `-e`: PoCo-instrumented target binary.
   - `-T`: Time budget for PoCo ISS in seconds. E.g., `-T 7200` means that PoCo will keep on running for 7200s (2 hours). 
   - `-- @@`: An AFL-style target command line passing.

3. Verify `poff_run.py`. Logs like below indicate that `poff_run.py` is started correctly:

   ```text
   ['@@']
   [LOG] the max time limit is set to 5.0
   [LOG] we are parsing dot file from /workdir/out/tog_analysis_edge
   [LOG] Execute testcases...
   [LOG] poff will be stop forced in 2025-06-22 19:40:57.017538
   [LOG] /workdir/aflpp-410c-poco
   [LOG] round : 1
   [LOG] run : /workdir/aflpp-410c-poco/afl-cmin -i /workdir/corpus/xmllint -o /workdir/out/poco-raw/2025-06-22_17-40-57_cmin_xmllint_poc_1 -T 1 -t 5000 -- /workdir/out/xmllint_poc @@
   ...
   [LOG] +++++++++++++++++++++++++++++++++++++++++++++++ 
   [LOG] now we have 3236 tog
   [LOG] next round we will use /workdir/corpus/xmllint as seed and /workdir/out/poco-raw/2025-06-22_17-41-02_cmin_xmllint_poc_2 as cmin output
   [LOG] round : 2
   [LOG] run : /workdir/aflpp-410c-poco/afl-cmin -i /workdir/corpus/xmllint -o /workdir/out/poco-raw/2025-06-22_17-41-02_cmin_xmllint_poc_2 -T 1 -t 5000 -- /workdir/out/xmllint_poc @@
   [LOG] +++++++++++++++ Program Outputs +++++++++++++++ 
   ```

   You can also check the results of ISS if `poff_run.py` has already finished few rounds of seed selection through `ls -l poco-raw/` (or check our finished example by `ls -l /workdir/data/xmllint-poco-raw`):

   ```text
   2025-06-22_17-40-57_cmin_xmllint_poc_1
   2025-06-22_17-41-02_cmin_xmllint_poc_2
   ...
   ```

4. The final step is to pack the seeds from all rounds of seed selection into one. Since the run of PoCo can last for a few hours in real experiments, we prepared read-to-use `xmllint` PoCo raw seeds under [data/xmllint-poco-raw](./data/xmllint-poco-raw). Users can verify the packing of PoCo seeds as follows:

   ```shell
   cd /workdir/out/
   mkdir ./poco-xmllint  # Make sure you create the output dir first.
   python3 /workdir/scripts/cp_poco_seeds.py \
     /workdir/data/xmllint-poco-raw/ ./poco-xmllint/
   ```

   The script `cp_poco_seeds.py` will gather seeds selected in all rounds of PoCo, deduplicate, and copies them to a given directory (i.e., `poco-xmllint/` here). The packing succeeded if you saw logs similar to the ones below:

   ```text
   ...
   [LOG] Cp from `/workdir/data/xmllint-poco-raw/2025-05-01_21-32-35_cmin_xmllint_poc_32/any6_0.xml` to `/workdir/out/poco-xmllint/any6_0.xml`
   [LOG] Cp from `/workdir/data/xmllint-poco-raw/2025-05-01_21-32-35_cmin_xmllint_poc_32/restriction-enum-1_0.xml` to `/workdir/out/poco-xmllint/restriction-enum-1_0.xml`
   [LOG] ============================
   [LOG] Find 378 for target xmllint-poco-raw
   [LOG] Finish all :-)
   [LOG] ============================
   ```

### 4.6 Fuzzing with PoCo seeds on Magma

In our submission, we leverage targets from Magma to evaluate how PoCo seeds perform in fuzzing. [Magma](https://github.com/HexHive/magma) is a fault-based fuzzing evaluation benchmark implemented based on Docker. Therefore, it is not possible to run Magma experiments within a Docker container.

1. If you are using the  `poco` container, remember to move PoCo seeds out to your host machine first:

   ```shell
   cd /workdir/  # On the host machine
   docker cp poco:/workdir/out/poco-xmllint .
   ```

2. Pull the source code of Magma 

   ```shell
   git clone https://github.com/HexHive/magma.git
   ```

3. Duplicate a `libxml2`; replace the corpus of `xmllint` with PoCo seeds.

   ```shell
   cd ./magma/targets
   cp -r ./libxml2 ./libxml2_poco
   rm -rf ./libxml2_poco/corpus/xmllint
   cp -r /workdir/poco-xmllint ./libxml2_poco/corpus/xmllint
   ```

4. Magma uses `captainrc` to configure the experiments. Modify `magma/tools/captain/captainrc` to get ready for fuzzing. We have prepared a configured one under `data/` ([captainrc-xmllint](./data/captainrc-xmllint)). You can just replace the Magma original one with this:

   ```shell
   cd /workdir/magma/tools/captain
   mv captainrc captainrc.orig
   #cp /workdir/data/captainrc-xmllint ./captainrc
   docker cp poco:/workdir/data/captainrc-xmllint ./captainrc
   ```

5. Install Docker and create a non-root user within the `docker` group, which is an implicit requirement of Magma. 

   ```shell
   apt update
   apt install -y docker.io
   docker --version  # Verify
   adduser poco      # Create a non-root user named 'poco'
   usermod -aG docker poco
   usermod -aG sudo poco
   ```

6. As required by AFL++, we need to do some setting before running it.

   ```shell
   echo core | sudo tee /proc/sys/kernel/core_pattern
   echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
   ```

7. Give the user `poco` permission to `/workdir`; switch to the user `poco` and [run](https://github.com/HexHive/magma/blob/v1.2/tools/captain/run.sh) Magma experiments.

   ```shell
   chown -R poco /workdir
   su poco
   cd /workdir/magma/tools/captain
   ./run.sh    # Provided by Magma
   ```


## 5 Reusability Guide

In our artifact, the **core reusable components** are the PoCo toolchain, which consists of:

- **Instrumentation component**: `SanitizerCoveragePoC.so` and the modified `afl-cc` (see section 4.2#Step-1..3 and section 4.3);
- **Toggle/Guard hierarchy extraction component**: `libtog_analysis.so` and `tog_analysis.sh` under `PoC/res/` (see section 4.2#Step-4 and section 4.4); 
- **Iterative seed selection component**: `poff_run.sh` under `PoC/run/` (see section 4.5)

Given the source code `<project-to-project>` of a project to be fuzzed and a corpus `<path-to-corpus>` of seed files, PoCo can generally be reused with the following steps: 

1. Build the project using gllvm:

   ```shell
   export CC=gclang CXX=gclang++
   cd <project-to-project>
   build # autogen, make, cmake...
   ```

2. Extract the bitcode file of the fuzz target:

   ```shell
   get-bc <path-to-target>
   mv target.bc /workdir/out
   ```

3. Conduct PoCo instrumentation:

   ```shell
   cd /workdir/out
   <path-to-poco>/afl-cc ./target.bc <link options> -o ./target_poc
   ```

4. Extract toggle/guard hierarchy:

   ```shell
   export AFLPP=<path-to-poco>
   cd /workdir/out
   AFL_LLVM_INSTRUMENT=poc $AFLPP/afl-cc \
       -emit-llvm -c ./target.bc \
       -o target_poc.bc
   bash $AFLPP/PoC/res/tog_analysis.sh ./target_poc.bc # Output to ./tog_analysis_edge
   ```

5. Run iterative seed selection and gather the resultant seeds:

   ```shell
   cd /workdir/out
   mkdir ./poco-raw ./poco-seeds
   export AFLPP=<path-to-poco>
   python3 $AFLPP/PoC/tools/poff_run.py \
     -i <path-to-corpus> \
     -o ./poco-raw \
     -g ./tog_analysis_edge \
     -e ./target_poc \
     -T 7200 -- <other-target-args> @@
   python3 ./scripts/cp_poco_seeds.py ./poco-raw ./poco-seeds
   ```

6. Finally, design and start fuzz campaigns using PoCo seeds.

## 6 Planned Improvements

Our submission is under a Major Revision and has much room to improve. Here is our plan:

- Further improve the documentation and tidy up the code.
- Include data analyses and experiment helper scripts.
- Add all experimental configurations and data visualizations.
- Provide a fork of Magma that contains our experimental setups.
- Archive the PoCo instrumented targets, the raw fuzz data (e.g., `xmllint_poc`), the extracted toggle/guard hierarchies, and all experimental seed corpora through Zenodo or figureshare; provide the link to the archive.