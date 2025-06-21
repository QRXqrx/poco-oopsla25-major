# Artifacts of PoCo (OOPSLA'25)

This repository contains the current version of PoCo's artifact. The artifact includes (1) all source code of the PoCo prototype, (2) intermediate and final data of PoCo experiments, and (3) key scripts for conducting experiments and data analyses.

**P.S. The Name Changing History**
- PoC -> Poff -> PoCo
- All there names are come from the metaphor: *Peeling off the Cocoon*.
- All three names are used interchangeably across the artifact and all refer to the proposed technique. 

## 1 Current Assets

- `aflpp-410c-poco`: PoCo prototype built on top of AFL++ (version 4.10c). Key components are as follows:
  - `instrumentation/SanitizerCoveragePoC.so.cc`: LLVM pass implementing PoCo instrumentation.
  - `src/afl-cc.c`: A modfied AFL++ compiler wrapper supporting `SanitizerCoveragePoC.so`. 
  - `PoC/res`: Utilities for running guard/toggle hierarchy construction and analysis.
  - `PoC/tools`: Utilities for running iteratice seed selection.
- `data`: Raw and processed experimental data.
  - `poco-binaries`: Experimental target binaries instrumented by PoCo.
  - `tog-dots`: Extracted guard/toggle hierarchy represented as DOT files.
  - `results`: Sheets and figures presented in the paper.
- `scripts`: Key data processing scripts.

## 2 Prerequisites
- **Operating System**: Ubuntu 22.04 LTS (or compatible Linux distribution)
- **CPU**: x86_64 architecture, recommended 4 cores or more
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
  - Go (==1.18.1), required for downloading gclang/gclang++. You can find and download gclang/gclang++ here: [gllvm](https://github.com/SRI-CSL/gllvm).
  - Docker (>= 24.0.7), required for runnig Magma, and recommended for building PoC-instrumented targets.


## 3 Step-by-Step Instructions

We use `xmllint`, one of the targets used in our paper, to exemplify our experimental process. Note that we assume that you are running a root user on Ubuntu:22.04 in this section.

**Note**: Since the installation of enviroments (such as LLVM and gclang) can be tricky, we also provided a **Docker image** with all environments done, which can be downloaded through: 
```shell
docker pull xxx
docker run -it --name 'poco'
```

You can jump to section 3.2 using this Docker container `poco`. 

### 3.1 Preparing Environments

1. **Install essential tools**. Install essential tools and dependencies, such as `make`, `cmake`, and `python3` using the `apt-get` command.
    ```shell
    sudo apt-get update
    sudo apt-get install -y build-essential \
        autoconf automake libtool pkg-config m4 \
        make cmake python3 python3-dev ...
    ```
2. **Install LLVM and Clang v15.0.7**. We recommend users to build LLVM from source. You can find the LLVM 15.0.7 release at [lvmorg-15.0.7](https://github.com/llvm/llvm-project/releases/tag/llvmorg-15.0.7) and install from source referring to the LLVM official [guildline](https://llvm.org/docs/GettingStarted.html#getting-the-source-code-and-building-llvm).
3. **Install gllvm**. The project [gllvm](https://github.com/SRI-CSL/gllvm) provided convinient whole program LLVM, which can ease the experiments of PoCo. They supply simple installation using `go`. Make sure you got `go` before installing and adding gllvm executables, such as `gclang` and `get-bc`, to `$PATH` after the installation. Exemplified commands are as follows:
    ```shell
    go install github.com/SRI-CSL/gllvm/cmd/...@latest
    ls ~/go/bin  # Verify your installation.
    export PATH=~/go/bin:$PATH # Add to PATH
    gclang --version
    ```
    If you see outputs like follows then it means you have gllvm installed:
    ```text
    clang version 15.0.7  # your clang version, better be 15.0.7
    Target: x86_64-unknown-linux-gnu
    Thread model: posix
    InstalledDir: /usr/local/bin
    ``` 

### 3.2 Build PoCo 
1. Make a directory `workdir` to work with. You can simply switch to it using `cd /workdir` if you are using our Docker image.
    ```shell
    mkdir /workdir
    cd /workdir
    mkdir ./out # To store built products.
    ``` 
2. Copy and untar our artifacts into `workdir`. Assuming that our artifact is named `poco-artifact.tar.gz` and is put under the `/` folder.
    ```shell
    mv /poco-artifact.tar.gz .
    untar -xzf ./poco-artifact.tar.gz
    ```
3. Enter the `aflpp-410c-poco` folder and build PoCo implemation (which is build on top of [AFL++](https://github.com/AFLplusplus/AFLplusplus) version 4.10) using `clang` as the compiler and set `LLVM_CONFIG=llvm-config-15`. You can directly switch to `/workdir/aflpp-410c-poco` using the `poco` container.
    ```shell
    make clean
    CC=clang CXX=clang++ LLVM_CONFIG=llvm-config-15 make
    ``` 
    The build succeeds if you see outputs like follows:
    ```text
    Build Summary:
    [+] afl-fuzz and supporting tools successfully built
    [+] LLVM basic mode successfully built
    [+] LLVM mode successfully built
    [-] LLVM LTO mode could not be built, it is optional, if you want it, please install LLVM and LLD 11+. More information at instrumentation/README.lto.md on how to build it
    [+] LLVM-PoC successfully built   # Yeah! The PoCo instrumentation seems gonna to work!
    [-] gcc_mode could not be built, it is optional, install gcc-VERSION-plugin-dev to enable this
    ```
    You can also the instruction below to double check:
    ```shell
    AFL_LLVM_INSTRUMENT=poc ./afl-cc --version
    ```
    If you see outputs as follows, then it means `afl-cc` is using `clang` as the backend, and our PoCo instrumentation looks working:
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
4. > Build tog analysis component.

### 3.3 Build `xmllint` 
1. Go back to the `workdir` and download the source code of `libxml2`, which is the project of `xmllint`. We use the [Magma](https://github.com/HexHive/magma) version of `libxml2` both in our experiments and for this demonstration, check here: [Magma-libxml2](https://github.com/HexHive/magma/blob/v1.2/targets/libxml2/fetch.sh). 
You can also do `cd /workdir/libxml2` within the `poco` container.
    ```shell
    git clone --no-checkout https://gitlab.gnome.org/GNOME/libxml2.git
    git -C ./libxml2 checkout ec6e3efb06d7b15cf5a2328fabd3845acea4c815
    ```
2. Enter the `libxml2` source folder. Build it using `gclang` as the compiler. Make sure you have `gllvm` binaries in your `PATH`.
    ```shell
    cd ./libxml2
    make clean # Clear outdated builds.
    CC=gclang CXX=gclang++ ./autogen.sh --disable-shared 
    make xmllint
    ```
    If you see logs like following, then it means the `autogen.sh` works well:
    ```text
    Done configuring
    Now type 'make' to compile libxml2.
    ``` 
    You list `xmllint` to see whether it is there:
    ```shell
    ls xmllint
    ```
3. Extract [bitcode](https://llvm.org/docs/BitCodeFormat.html) file from `xmllint` and move it to `/workdir/out`:
    ```
    get-bc xmllint
    mv xmllint.bc ../out
    ```
    The bitcode extraction succeeds is you see logs below:
    ```text
    Bitcode file extracted to: xmllint.bc.
    ```
4. Create PoCo-instrumented (also with AFL++ instrumentation) `xmllint` using the bitcode file and `aflpp-410c-poco/afl-cc` as the compiler. 
    ```shell
    cd ../out
    AFL_LLVM_INSTRUMENT=poc ../aflpp-410c-poco/afl-cc -lz -llzma -lm ./xmllint.bc -o xmllint_poc
    ```
    Build success if you see logs like follows:
    ```text
    ...
    [PoC] Inject function: xmlListReverseWalk
    [+] Found 9 BBs and collected 3 cond br before PoC injection
    [+] Found 12 BBs after PoC injection
    [+] Instrumented 74696 locations with no collisions (non-hardened mode) of which are 3674 handled and 0 unhandled selects.
    [PoC] Instrumented 41907 toggles in total.
    [PoC] Write toggle number (41907) to dump file: /tmp/poc_tog
    ```
    You can futher verify the build by or checking symbols using `nm`:
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

## 4 Planned Improvements

- We will provide a full Docker image with pre-installed dependencies.
- We will include one-click scripts to reproduce all results.
- Additional experimental configurations and data visualizations will be added.
