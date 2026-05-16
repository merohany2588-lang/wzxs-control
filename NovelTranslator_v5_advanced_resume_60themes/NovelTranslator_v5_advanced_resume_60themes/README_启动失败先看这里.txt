如果 run_novel_translator.bat 闪退或 run_debug.bat 报 NUL / 不是内部命令：

原因通常是：
1. Windows 给下载的 ZIP 加了“Internet 安全区域”标记；
2. 旧启动脚本使用了 >nul 重定向，在你的系统上被安全策略拦截；
3. CMD 对中文标题/特殊字符解析异常。

本版已改成 ASCII-only SAFE 启动脚本，并移除了 >nul。

请按顺序尝试：

1. 双击 run_safe.bat
2. 如果不行，双击 run_debug_safe.bat
3. 如果依赖安装失败，双击 install_deps_safe.bat
4. 仍不行，用 PowerShell 运行：
   右键 run_novel_translator.ps1 -> 使用 PowerShell 运行

如果 Windows 安全中心仍弹窗：
右键压缩包 -> 属性 -> 勾选“解除锁定” -> 确定
然后重新解压。
或者把整个文件夹移动到：
C:\NovelTranslator_v3_safe_launcher

不要放在带特殊权限限制的目录里。
