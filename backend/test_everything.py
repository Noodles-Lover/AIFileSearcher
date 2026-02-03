import sys
import os

# 将当前目录添加到 Python 路径，以便导入 api 模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.everything import EverythingClient

def main():
    client = EverythingClient()
    
    # 测试目录：使用 Windows 常见目录，或者让用户输入
    # 这里为了演示，我们先尝试搜索 C:\Windows\System32 下的一些文件，或者直接搜索某个关键词
    test_folder = r"C:\Windows\System32" 
    print(f"--- Testing Traversal of: {test_folder} ---")
    
    # 获取文件列表
    files = client.get_files_in_folder(test_folder)
    
    if not files:
        print("No files found or connection failed.")
        print("Please ensure 'Everything' is running and HTTP Server is enabled (Tools -> Options -> HTTP Server).")
        # 尝试做一个简单的全局搜索来验证连接
        print("\nAttempting global search for 'python'...")
        results = client.search("python", count=5)
        if results:
            print("Global search successful! Found:")
            for item in results:
                print(f"[{item['modified']}] {item['name']} ({item['size']})")
        else:
            print("Global search also failed.")
        return

    # 打印前 10 个结果
    print(f"Found {len(files)} items (showing first 10):")
    for i, item in enumerate(files[:10]):
        print(f"{i+1}. [{item['modified']}] {item['name']} - {item['size']}")

if __name__ == "__main__":
    main()
