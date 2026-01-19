//insert.cc
#include "Insert.h"

#include "llvm/ADT/ArrayRef.h"
#include "llvm/ADT/StringRef.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/InstIterator.h"
#include "llvm/IR/Instruction.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/ModuleSlotTracker.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Passes/PassPlugin.h"
#include "llvm/Support/Casting.h"
#include "llvm/Support/Compiler.h"
#include "llvm/Support/FormatVariadic.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/ADT/SmallVector.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/IR/LLVMContext.h"

#include <string>


using namespace llvm;
#define DEBUG_TYPE "try-insert"

void Insert::insert_in_br(llvm::Module &M) {
    LLVMContext &Context = M.getContext();
    IRBuilder<> Builder(Context);

    
    // Create a null pointer
    ConstantPointerNull *NullPtr =ConstantPointerNull::get(PointerType::getUnqual(Type::getInt8Ty(Context)));
    
    // Insert an instruction to call getenv
    Function *GetEnvFunc = M.getFunction("getenv");
    if (!GetEnvFunc) {
        // Declare the getenv function
        FunctionType *GetEnvType = FunctionType::get(PointerType::getUnqual(Type::getInt8Ty(Context)), {PointerType::getUnqual(Type::getInt8Ty(Context))}, false);
        GetEnvFunc = Function::Create(GetEnvType, Function::ExternalLinkage, "getenv", &M);
    }
    
    //Initialize a named string
    std::string name="TOGGLE_";
    std::string t_name=".str.env";
    
	for(Function & F: M){
        if(F.isDeclaration())
            continue;
        for (Instruction &Inst : instructions(F)) {
            if (auto *Br = dyn_cast<BranchInst>(&Inst)){
                if(!Br->isConditional())
                   continue;
                ++br_cnt;
                // Set the insertion point before the br instruction
                Builder.SetInsertPoint(Br);

                // Get the branch condition
                Value *OldCond = Br->getCondition();

				
                CallInst *TryGet = Builder.CreateCall(GetEnvFunc, {Builder.CreateGlobalStringPtr((name+std::to_string(br_cnt)).c_str(), t_name+std::to_string(br_cnt), 0, &M)}, "tryget");


                // Insert an icmp instruction
                Value *Res = Builder.CreateICmpNE(TryGet, NullPtr, "res");

                // Insert an or instruction
                Value *NewCond = Builder.CreateOr(Res, OldCond, "newcond");

                // Modify the condition of the original br instruction
                Br->setCondition(NewCond);
        
    		}
  		}
	}
}

PreservedAnalyses Insert::run(llvm::Module &M,
                              llvm::ModuleAnalysisManager &) {
  insert_in_br(M);
    
  return (br_cnt ? llvm::PreservedAnalyses::none()
                  : llvm::PreservedAnalyses::all());
}

//-----------------------------------------------------------------------------
// New PM Registration
//-----------------------------------------------------------------------------
llvm::PassPluginLibraryInfo getMBAAddPluginInfo() {
  return {LLVM_PLUGIN_API_VERSION, "try-insert", LLVM_VERSION_STRING,
          [](PassBuilder &PB) {
            PB.registerPipelineParsingCallback(
                [](StringRef Name, ModulePassManager &FPM,
                   ArrayRef<PassBuilder::PipelineElement>) {
                  if (Name == "try-insert") {
                    FPM.addPass(Insert());
                    return true;
                  }
                  return false;
                });
          }};
}

extern "C" LLVM_ATTRIBUTE_WEAK ::llvm::PassPluginLibraryInfo
llvmGetPassPluginInfo() {
  return getMBAAddPluginInfo();
}