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
    
    // 声明类似于 std::map<std::string, std::vector<std::string>> 的结构
    std::unordered_map<std::string,std::unordered_set<std::string>> table_yes, table_no, table_go;

    // 声明返回的 SmallVector
    s_yes.reset(new LLVM_PSS);
    s_no.reset(new LLVM_PSS);
    s_go.reset(new LLVM_PSS);

    // 用于抓BB的label
    std::string block_address;
    raw_string_ostream string_stream(block_address);
    

    // 枚举函数中的每个基本块 -> @PoC: Find the toggles that have been instrumented in the target.
    for (auto &BB : F) {
        std::string poc_tog_value;

        // 枚举基本块中的每条指令
        for (auto &I : BB) {
            // 检查指令是否是 call 指令
            if (auto *Call = dyn_cast<CallInst>(&I)) {
                // 检查调用的函数是否是 getenv
                if (Function *Callee = Call->getCalledFunction()) {
                    if (Callee->getName() == "getenv") {
                        // 获取传递给 getenv 的参数
                        if (auto *Arg = dyn_cast<GlobalVariable>(Call->getArgOperand(0))) {
                            std::string ArgName = Arg->getName().str();

                            // 检查参数是否形如 "POC_TOG_{数字}"
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

        //获取bb的tag
        BB.printAsOperand(string_stream, false);
        std::string bb_name = string_stream.str();
        block_address.clear();

        // 如果找到了 POC_TOG_{数字}，处理 br 指令
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


                // 获取条件跳转的 t 和 f 标签
                BasicBlock *GoBB = Br->getSuccessor(0);
                GoBB->printAsOperand(string_stream, false);
                std::string GoBB_name = string_stream.str();

                block_address.clear();

                table_go[GoBB_name].insert(poc_tog_value);
                
            } else {
                 // 获取条件跳转的 t 和 f 标签
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
                // 添加 t - POC_TOG_{数字} 到 table_yes
                table_yes[TrueBB_name].insert(poc_tog_value);
                // 添加 f - POC_TOG_{数字} 到 table_no
                table_no[FalseBB_name].insert(poc_tog_value);
            }
        }
    }

     // 枚举函数中的每个基本块
    for (auto &BB : F) {
        std::string poc_tog_value;

        // 枚举基本块中的每条指令
        for (auto &I : BB) {
            // 检查指令是否是 call 指令
            if (auto *Call = dyn_cast<CallInst>(&I)) {
                // 检查调用的函数是否是 getenv
                if (Function *Callee = Call->getCalledFunction()) {
                    if (Callee->getName() == "getenv") {
                        // 获取传递给 getenv 的参数
                        if (auto *Arg = dyn_cast<GlobalVariable>(Call->getArgOperand(0))) {
                            std::string ArgName = Arg->getName().str();

                            // 检查参数是否形如 "POC_TOG_{数字}"
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

        //获取bb的tag
        BB.printAsOperand(string_stream, false);
        std::string bb_name = string_stream.str();
        block_address.clear();

        // 如果找到了 POC_TOG_{数字}，处理 br 指令
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
    // 获取环境变量 TOG_ANALYSIS_PATH 的值
    const char* pathEnv = std::getenv("TOG_ANALYSIS_PATH");

    std::string directory;

    if (pathEnv) {
        // 如果环境变量存在，使用它作为目录
        directory = pathEnv;
    } else {
        // 如果环境变量不存在，使用 getcwd 获取当前目录
        char cwd[PATH_MAX];
        if (getcwd(cwd, sizeof(cwd)) != nullptr) {
            directory = cwd;
        } else {
            std::cerr << "Failed to get current working directory" << std::endl;
            return llvm::PreservedAnalyses::all();
        }
    }

    // 生成文件的完整路径
    std::string filePath = directory + "/tog_analysis_edge";

    // 打开文件，std::ofstream::trunc 模式会替换已存在的文件
    std::ofstream file(filePath, std::ios::out | std::ios::trunc);
    if (!file.is_open()) {
        std::cerr << "Failed to open or create the file: " << filePath << std::endl;
        return llvm::PreservedAnalyses::all();
    }

    // 关闭文件，之后我们将以追加的方式打开它
    file.close();

    // 再次打开文件，这次是以追加模式打开
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

    //为顺序结构BB添加统一节点，名字起做NONE_TOG_BB，圆形节点，虚线轮廓，连接的边也是虚线

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