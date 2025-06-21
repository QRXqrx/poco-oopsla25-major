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

## 2 Installation

> How to install PoCo on your own machine.

### 2.1 Prerequisites
- **Operating System**: Ubuntu 22.04 LTS (or compatible Linux distribution)
- **CPU: x86_64 architecture, recommended 4 cores or more
- **Memory**: Minimum 16 GB RAM
- Disk Space: At least 32 GB of free space
- Python: 3.10 or higher


## 3 Quick Start

> How to run PoCo on an example project, or, just on hello.

1. Clone the repo: `git clone ...`
2. Install dependencies (see below).
3. Run: `python run_exp.py config.yaml`

## 4 Planned Improvements

- We will provide a full Docker image with pre-installed dependencies.
- We will include one-click scripts to reproduce all results.
- Additional experimental configurations and data visualizations will be added.
