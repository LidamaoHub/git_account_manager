# GitHub Account Manager (GAM)

GitHub Account Manager (GAM) 是一个命令行工具，用于管理多个 GitHub 账户并执行各种 Git 操作。

## 安装方法

1. 确保您的系统已安装 Python 3.6 或更高版本。

2. 安装所需的依赖包：
   ```
   pip install pygit2 requests
   ```

3. 下载 GAM 脚本并将其保存为 `gam.py`。

4. 为脚本添加执行权限：
   ```
   chmod +x gam.py
   ```

5. 将脚本移动到系统 PATH 中：

	 - macOS:
     ```
     sudo mv gam.py /usr/local/bin/gam
     ```


   - Ubuntu/Linux:
     ```
     sudo mv gam.py /usr/local/bin/gam
     ```

完成以上步骤后，您应该能够在系统的任何位置使用 `gam` 命令。

## 设置方法

1. 添加 GitHub 账户：
   ```
   gam add_account
   ```
   按照提示输入 GitHub 用户名、邮箱和个人访问令牌。

2. 设置全局默认账户：
   ```
   gam global <用户名>
   ```

## 使用方法

1. 列出所有已添加的账户：
   ```
   gam list
   ```

2. 显示当前活动账户：
   ```
   gam now
   ```

3. 克隆仓库：
   ```
   gam clone <仓库地址> [-u <已添加账户名(小写)>]
   ```

4. 添加文件到 Git 暂存区：
   ```
   gam add <文件或目录路径>
   ```

5. 提交更改：
   ```
   gam commit "<提交信息>"
   ```

6. 推送更改：
   ```
   gam push <远程名称> <分支名称>
   ```

7. 拉取更改：
   ```
   gam pull <远程名称> <分支名称>
   ```

8. 移除账户：
   ```
   gam remove <用户名>
   ```

注意：克隆仓库时，如果不指定用户名，将使用全局默认账户。克隆完成后，该仓库会自动设置为使用克隆时的账户。

## 注意事项

- 确保妥善保管您的 GitHub 个人访问令牌。
- 首次添加账户时，该账户将自动设置为全局默认账户。
- 使用 `clone` 命令时，可以通过 `-u` 参数指定要使用的账户。
- 所有 Git 操作（add、commit、push、pull）都会自动使用当前目录对应的账户或全局默认账户。

如需更多帮助，请使用 `gam -h` 或 `gam <命令> -h` 查看详细说明。