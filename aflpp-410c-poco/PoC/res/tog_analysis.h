//tog_analysis.h
#pragma once

#include "llvm/IR/PassManager.h"
#include "llvm/Pass.h"
#include "llvm/ADT/SmallVector.h"
//------------------------------------------------------------------------------
// New PM interface
//------------------------------------------------------------------------------
using LLVM_PSS = llvm::SmallVector<std::pair<std::string,std::string>, 1<<16> ;
using LLVM_SVEC = llvm::SmallVector<std::string, 1<<16> ;
struct tog_analysis : public llvm::PassInfoMixin<tog_analysis> {
  
  llvm::PreservedAnalyses run(llvm::Module &M,
                              llvm::ModuleAnalysisManager &);
  void start_analysis(llvm::Function &F);

  static bool isRequired() { return true; }

  std::shared_ptr<LLVM_PSS> s_no,s_yes,s_go;
  std::shared_ptr<LLVM_SVEC> normal_node;
};