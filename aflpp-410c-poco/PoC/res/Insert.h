//Insert.h
#pragma once

#include "llvm/IR/PassManager.h"
#include "llvm/Pass.h"

//------------------------------------------------------------------------------
// New PM interface
//------------------------------------------------------------------------------
struct Insert : public llvm::PassInfoMixin<Insert> {
  llvm::PreservedAnalyses run(llvm::Module &M,
                              llvm::ModuleAnalysisManager &);
  void insert_in_br(llvm::Module &M);

  static bool isRequired() { return true; }
    
  int br_cnt;
  
};
