//insert.cc
#include "tog_analysis.h"

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
#include <cstdlib>  // for getenv
#include <unistd.h> // for getcwd
#include <limits.h> // for PATH_MAX
#include <iostream>
#include <fstream>
#include <unordered_set>
#include <unordered_map>

using namespace llvm;

void tog_analysis::start_analysis(llvm::Function &F) {
    
    // Declare a structure similar to std::map<std::string, std::vector<std::string>>
    std::unordered_map<std::string,std::unordered_set<std::string>> table_yes, table_no, table_go;

    // Declare the returned SmallVector
    s_yes.reset(new LLVM_PSS);
    s_no.reset(new LLVM_PSS);
    s_go.reset(new LLVM_PSS);

    // A label used to capture basic blocks (BBs)
    std::string block_address;
    raw_string_ostream string_stream(block_address);
    

    // Enumerate each basic block in the function -> @PoC: Find the toggles that have been instrumented in the target.
    for (auto &BB : F) {
        std::string poc_tog_value;

        // Enumerate each instruction in the basic block
        for (auto &I : BB) {
            // Check whether the instruction is a call instruction
            if (auto *Call = dyn_cast<CallInst>(&I)) {
                // Check whether the called function is getenv
                if (Function *Callee = Call->getCalledFunction()) {
                    if (Callee->getName() == "getenv") {
                        // Get the argument passed to getenv
                        if (auto *Arg = dyn_cast<GlobalVariable>(Call->getArgOperand(0))) {
                            std::string ArgName = Arg->getName().str();

                            // Check whether the argument matches the pattern POC_TOG_{number}
                            if (ArgName.find("POC_TOG_") == 0 && ArgName.length() > 8) {
                                if(!poc_tog_value.empty()){
                                    std::cerr<<"error:one BB have more than one tog"<<'\n';
                                    exit(1);
                                }
                                poc_tog_value = ArgName;
                                break;
                            }
                        }
                    }
                }
            }
        }

        //Get the tag of the basic block (BB)
        BB.printAsOperand(string_stream, false);
        std::string bb_name = string_stream.str();
        block_address.clear();

        // If POC_TOG_{number} is found, handle the br instruction
        if (poc_tog_value.empty()) {
            std::string strtp = "NONE_TOG_BB_"+bb_name.substr(1);

            bool is_ = false;
            for(auto & v : strtp){
                if(v=='.'||v=='_'||v=='-'){
                    if(is_){
                        continue;
                    } else {
                        poc_tog_value.push_back('_');
                        is_=true;
                    }
                } else {
                    poc_tog_value.push_back(v);
                    is_=false;
                }
            } 
            normal_node->push_back(poc_tog_value);
        } 
        // std::cout<<bb_name << std::endl;
        // std::cout<<"wo getch "+poc_tog_value << std::endl;
        // std::cout<<"the BB's name is "+bb_name << std::endl;

        if (auto *Br = dyn_cast<BranchInst>(BB.getTerminator())) {
            if (!Br->isConditional()) {
                // std::cout<<"right!"<<'\n';


                // Get the true and false labels of the conditional branch
                BasicBlock *GoBB = Br->getSuccessor(0);
                GoBB->printAsOperand(string_stream, false);
                std::string GoBB_name = string_stream.str();

                block_address.clear();

                table_go[GoBB_name].insert(poc_tog_value);
                
            } else {
                 // Get the true and false labels of the conditional branch
                BasicBlock *TrueBB = Br->getSuccessor(0);
                BasicBlock *FalseBB = Br->getSuccessor(1);
                TrueBB->printAsOperand(string_stream, false);
                std::string TrueBB_name = string_stream.str();

                block_address.clear();
                // string_stream.flush();

                // std::cout<<TrueBB_name+' ';

                FalseBB->printAsOperand(string_stream, false);
                std::string FalseBB_name = string_stream.str();
                block_address.clear();

                assert(TrueBB_name != FalseBB_name);
                // string_stream.flush();

                // std::cout<<FalseBB_name+'\n';
                // Add T - POC_TOG_{number} to table_yes
                table_yes[TrueBB_name].insert(poc_tog_value);
                // Add T - POC_TOG_{number} to table_no
                table_no[FalseBB_name].insert(poc_tog_value);
            }
        }
    }

     // Enumerate each basic block in the function
    for (auto &BB : F) {
        std::string poc_tog_value;

        // Enumerate each instruction in the basic block
        for (auto &I : BB) {
            // Check whether the instruction is a call instruction
            if (auto *Call = dyn_cast<CallInst>(&I)) {
                // Check whether the called function is getenv
                if (Function *Callee = Call->getCalledFunction()) {
                    if (Callee->getName() == "getenv") {
                        // Get the argument passed to getenv
                        if (auto *Arg = dyn_cast<GlobalVariable>(Call->getArgOperand(0))) {
                            std::string ArgName = Arg->getName().str();

                            // Check whether the argument matches the pattern "POC_TOG_{number}"
                            if (ArgName.find("POC_TOG_") == 0 && ArgName.length() > 8) {
                                if(!poc_tog_value.empty()){
                                    std::cerr<<"error:one BB have more than one tog"<<'\n';
                                    exit(1);
                                }
                                poc_tog_value = ArgName;
                                break;
                            }
                        }
                    }
                }
            }
        }

        //Get the tag of the basic block (BB)
        BB.printAsOperand(string_stream, false);
        std::string bb_name = string_stream.str();
        block_address.clear();

        // If POC_TOG_{number} is found, handle the br instruction
        if (poc_tog_value.empty()) {
            std::string strtp = "NONE_TOG_BB_"+bb_name.substr(1);

            bool is_ = false;
            for(auto & v : strtp){
                if(v=='.'||v=='_'||v=='-'){
                    if(is_){
                        continue;
                    } else {
                        poc_tog_value.push_back('_');
                        is_=true;
                    }
                } else {
                    poc_tog_value.push_back(v);
                    is_=false;
                }
            } 
        } 
        // std::cout<<bb_name << std::endl;
        // std::cout<<"wo getch "+poc_tog_value << std::endl;
        // std::cout<<"the BB's name is "+bb_name << std::endl;

        if(table_go.count(bb_name)){
            for(auto & zname : table_go[bb_name]){
                s_go->push_back(std::make_pair(zname,poc_tog_value));
            }
        }

        if(table_yes.count(bb_name)){
            for(auto & zname : table_yes[bb_name]){
                s_yes->push_back(std::make_pair(zname,poc_tog_value));
            }
        }

        if(table_no.count(bb_name)){
            for(auto & zname : table_no[bb_name]){
                s_no->push_back(std::make_pair(zname,poc_tog_value));
            }
        }

    }

    // return std::make_tuple(yes,no,normal_node);
}

PreservedAnalyses tog_analysis::run(llvm::Module & M,
                              llvm::ModuleAnalysisManager &) {
    // Get the value of the environment variable TOG_ANALYSIS_PATH
    const char* pathEnv = std::getenv("TOG_ANALYSIS_PATH");

    std::string directory;

    if (pathEnv) {
        // If the environment variable exists, use it as the directory
        directory = pathEnv;
    } else {
        // If the environment variable does not exist, use getcwd to get the current directory
        char cwd[PATH_MAX];
        if (getcwd(cwd, sizeof(cwd)) != nullptr) {
            directory = cwd;
        } else {
            std::cerr << "Failed to get current working directory" << std::endl;
            return llvm::PreservedAnalyses::all();
        }
    }

    // Generate the full path of the file
    std::string filePath = directory + "/tog_analysis_edge";

    // Open the file; std::ofstream::trunc mode will overwrite the existing file
    std::ofstream file(filePath, std::ios::out | std::ios::trunc);
    if (!file.is_open()) {
        std::cerr << "Failed to open or create the file: " << filePath << std::endl;
        return llvm::PreservedAnalyses::all();
    }

    // Close the file, and then reopen it in append mode
    file.close();

    // Reopen the file, this time in append mode
    file.open(filePath, std::ios::out | std::ios::app);
    if (!file.is_open()) {
        std::cerr << "Failed to open the file for appending: " << filePath << std::endl;
        return llvm::PreservedAnalyses::all();
    }

    file<<"digraph G {\n";
    normal_node.reset(new LLVM_SVEC);
    for (auto & F:M){
        // if(normal_node->size()>10000){
        //     break;
        // }
        if(F.isDeclaration()){
            continue;
        }
        if(F.getName().str().substr(0,6)== "sancov"){
            continue;
        }
        // std::cout<<F.getName().str()<<std::endl;
        // std::cout<< "1111" << std::endl;
        start_analysis(F);
        for(auto & ss : *s_yes){
            // file << '\t' << ss.first << " -> " << ss.second<< " [label=\"true\", fontcolor=\"green\"];" << '\n' ;
            file << '\t' << ss.first << " -> " << ss.second << '\n';
        } 
        for(auto & ss : *s_no){
            // file << '\t' << ss.first << " -> " << ss.second<< " [label=\"false\", fontcolor=\"red\"];" << '\n' ;
            file << '\t' << ss.first << " -> " << ss.second << '\n';
        }
        for(auto & ss : *s_go){
            // file << '\t' << ss.first << " -> " << ss.second<< " [fontcolor=\"black\"];" << '\n' ;
            file << '\t' << ss.first << " -> " << ss.second << '\n';
        }
        s_yes.reset();
        s_no.reset();
        s_go.reset();
    }

    //Add a unified node for sequential basic blocks (BBs), named NONE_TOG_BB, as a circular node with a dashed outline, and connect it with dashed edges

    // for(auto & name : *normal_node){
    //     file << '\t' << name << R"( [shape="ellipse", style="dashed", label=")" << name.substr(0,11) << "\"];\n";
    // }

    normal_node.reset();

    file<<"}\n";

    file.close();

    std::cout<<"the result is written to "+filePath + '\n';

    return llvm::PreservedAnalyses::all();
}

//-----------------------------------------------------------------------------
// New PM Registration
//-----------------------------------------------------------------------------
llvm::PassPluginLibraryInfo getMBAAddPluginInfo() {
  return {LLVM_PLUGIN_API_VERSION, "tog-analysis", LLVM_VERSION_STRING,
          [](PassBuilder &PB) {
            PB.registerPipelineParsingCallback(
                [](StringRef Name, ModulePassManager &FPM,
                   ArrayRef<PassBuilder::PipelineElement>) {
                  if (Name == "tog-analysis") {
                    FPM.addPass(tog_analysis());
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