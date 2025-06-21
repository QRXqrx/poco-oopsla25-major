# Artifact for PoCo (OOPSLA'25)

This repository contains the current version of the artifact. The artifact includes (1) all source code of the PoCo prototype and (2) key scripts for conducting experiments and data analyses.

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
- Other Requirements:
  - Git (>= 2.34.1)
  - make (>= 4.3)
  - cmake (>= 3.22.1)
  - LLVM & Clang (== 15.0.7), required for running PoCo instrumentation. You can find LLVM 15.0.7 here: [lvmorg-15.0.7](https://github.com/llvm/llvm-project/releases/tag/llvmorg-15.0.7).
  - Go (==1.18.1), required for downloading gclang/gclang++. You can find and download gclang/gclang++ here: [gllvm](https://github.com/SRI-CSL/gllvm).
  - Docker (>= 24.0.7), required for runnig Magma, and recommended for building PoC-instrumented targets.


## 3 Step-by-Step Instructions

We use `xmllint`, one of the targets used in our submission，to exemplify our experimental process. 
Since the installation of enviroments (such as LLVM and gclang), we also provide a Docker image with all environments done, which can be downloaded through: `docker pull`. You can jump to section 3.1 using this Docker image. 

### 3.1 Preparing Environments

1. **Install essential tools**. Install essential tools and dependencies, such as `make`, `cmake`, and `python3`, using `apt-get install`.
    ```shell
    sudo apt-get update
    sudo apt-get install -y build-essential python3 \
        autoconf automake make cmake...
    ```
2. **Install LLVM and Clang v15.0.7**. We recommend users to build LLVM from source. You can find the LLVM 15.0.7 release at [lvmorg-15.0.7](https://github.com/llvm/llvm-project/releases/tag/llvmorg-15.0.7) and install from source referring to the LLVM official [guildline](https://llvm.org/docs/GettingStarted.html#getting-the-source-code-and-building-llvm).
3. **Install gllvm**. The project [gllvm](https://github.com/SRI-CSL/gllvm) provided convinient whole program LLVM, which can ease the experiments of PoCo. They supply simple installation using `go`. Make sure you got `go` before installing and adding gllvm executables, such as `gclang` and `get-bc`, to `$PATH` after the installation. Exemplified commands are as follows:
    ```shell
    go install github.com/SRI-CSL/gllvm/cmd/...@latest
    ls ~/go/bin  # Verify your installation.
    export PATH=~/go/bin:$PATH # Add to PATH
    gclang --version
    ```

## 4 Planned Improvements

- We will provide a full Docker image with pre-installed dependencies.
- We will include one-click scripts to reproduce all results.
- Additional experimental configurations and data visualizations will be added.
