import os
import subprocess
import sys

def check_process_running(process_name):
    """
    检查指定进程是否已经运行
    使用 pgrep 命令检查进程
    """
    try:
        # 使用 pgrep 检查进程是否存在
        result = subprocess.run(
            f"pgrep -f {process_name}",
            shell=True,
            capture_output=True,
            text=True
        )
        
        # 如果返回码为 0，说明进程存在
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            print(f"✓ 进程已启动，PID: {pids}")
            return True
        else:
            print(f"✗ 进程未运行")
            return False
            
    except Exception as e:
        print(f"检查进程时出错: {e}")
        return False

def start_application():
    """
    启动应用
    """
    try:
        # 先检查 start.sh 是否存在
        if not os.path.exists("./start.sh"):
            print("错误: start.sh 文件不存在")
            return False
        
        # 授予执行权限并运行脚本
        cmd = "chmod +x ./start.sh && ./start.sh"
        print(f"执行命令: {cmd}")
        
        result = subprocess.run(cmd, shell=True)
        
        if result.returncode == 0:
            print("✓ 应用启动成功")
            return True
        else:
            print(f"✗ 应用启动失败，返回码: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"启动应用时出错: {e}")
        return False

def main():
    """
    主函数：检查进程后决定是否启动
    """
    # 指定要检查的进程名称（根据实际情况修改）
    process_name = "python app.py"  # 可改为你的实际进程名
    
    print("=" * 50)
    print("检查应用状态...")
    print("=" * 50)
    
    # 检查进程是否已运行
    if check_process_running(process_name):
        print("\n应用已在运行，无需重复启动")
        sys.exit(0)
    
    print("\n准备启动应用...")
    
    # 进程未运行，则启动
    if start_application():
        print("\n应用启动成功!")
    else:
        print("\n应用启动失败!")
        sys.exit(1)

if __name__ == "__main__":
    main()