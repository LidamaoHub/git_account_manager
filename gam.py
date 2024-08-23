#!/usr/bin/env python3

import argparse
import json
import os,glob
import requests
from getpass import getpass
import base64
import logging
import re
import urllib.parse
import pygit2
import requests
from urllib.parse import urlparse


import argparse
import json
import os
import requests
import pygit2
from getpass import getpass
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CONFIG_FILE = os.path.expanduser('~/.github_accounts.json')
PATH_CONFIG_FILE = os.path.expanduser('~/.github_path_config.json')

def get_github_user_info(token):
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    response = requests.get('https://api.github.com/user', headers=headers)
    if response.status_code == 200:
        user_data = response.json()
        print(user_data)
        return user_data.get('login'), user_data.get('email'), user_data.get('avatar_url')
    else:
        print(f"获取用户信息失败: {response.status_code}")
        return None, None, None


def find_git_repo(path):
    """查找包含当前路径的 Git 仓库根目录"""
    while path != '/':
        if os.path.isdir(os.path.join(path, '.git')):
            return path
        path = os.path.dirname(path)
    return None

def parse_github_url(url):
    """Parse different formats of GitHub URLs."""
    # SSH format: git@github.com:owner/repo.git
    ssh_pattern = r'git@github\.com:(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+)\.git'
    ssh_match = re.match(ssh_pattern, url)
    if ssh_match:
        return ssh_match.group('owner'), ssh_match.group('repo')

    # HTTPS format: https://github.com/owner/repo.git
    https_pattern = r'https://github\.com/(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+)\.git'
    https_match = re.match(https_pattern, url)
    if https_match:
        return https_match.group('owner'), https_match.group('repo')

    # Simple owner/repo format
    if '/' in url and url.count('/') == 1:
        return url.split('/')

    return None, None

def load_accounts():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_accounts(accounts):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(accounts, f, indent=2)

def load_path_config():
    if os.path.exists(PATH_CONFIG_FILE):
        with open(PATH_CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_path_config(key,value):
    path_config = load_path_config()
    path_config[key] = value.lower()
    with open(PATH_CONFIG_FILE, 'w') as f:
        json.dump(path_config, f, indent=2)

def add_account(args):
    accounts = load_accounts()
    name = input("Enter the GitHub username: ")
    name_key = name.lower()
    email = input("Enter the email for this account: ")
    print("\nTo get a GitHub personal access token:")
    print("1. Go to https://github.com/settings/tokens")
    print("2. Click 'Generate new token'")
    print("3. Select the necessary scopes (at least 'repo' for full repository access)")
    print("4. Generate and copy the token")
    print("Note: Store this token securely as it won't be shown again!\n")

    token = getpass("Enter your GitHub personal access token: ")

    accounts[name_key] = {
        "email": email,
        "token": token,
        "name":name
    }
    save_accounts(accounts)

    if len(accounts) == 0:
        save_path_config("global",name_key)
        print(f"Account '{name_key}' added successfully and set as the default global account.")
    else:
        print(f"Account '{name_key}' added successfully.")


def list_accounts(args):
    accounts = load_accounts()
    if not accounts:
        print("No accounts found.")
        return

    print("Available accounts:")
    for name, info in accounts.items():
        print(f"- {name} {info.get('name')} ({info['email']})")


def switch_global(args):
    accounts = load_accounts()
    name = args.name.lower()
    if name not in accounts:
        print(f"Account '{name}' not found.")
        return

    
    save_path_config("global",name)
    
    print(f"Switched to account globally: {name}")

def remove_account(args):
    accounts = load_accounts()
    name = args.name.lower()
    if name in accounts:
        del accounts[name]
        save_accounts(accounts)
        print(f"Account '{name}' removed successfully.")
    else:
        print(f"Account '{name}' not found.")

def show_current_account(args):
    # TODO
    path_config = load_path_config()
    current_path = os.getcwd()
    
    if 'global' in path_config:
        print(f"Global account: {path_config['global']}")
    
    if current_path in path_config:
        print(f"Local account for {current_path}: {path_config[current_path]}")
    
    active_account = get_active_account()
    if active_account:
        print(f"Active account: {active_account}")
    else:
        print("No active account found.")


def get_active_account():
    path_config = load_path_config()
    current_path = os.getcwd()
    
    if current_path in path_config:
        return path_config[current_path]
    elif 'global' in path_config:
        return path_config['global']
    else:
        print("No active account. Use 'gam add' to add a global account.")
        return None

def github_api_request(method, url, token, data=None, params=None):
    headers = {
        'Authorization': f"token {token}",
        'Accept': 'application/vnd.github.v3+json'
    }
    response = requests.request(method, url, headers=headers, json=data, params=params)
    response.raise_for_status()
    return response.json()


def get_authenticate_user(name=None):
    
    active_account = name if name else get_active_account()
    print(get_active_account())
    if not active_account:
        print("No active account. Use 'gam global' to set an account.")
        return None
    name_key = active_account.lower()
    
    accounts = load_accounts()
    if name_key not in accounts:
        print(f"Account '{active_account}' not found.")
        return None
    return accounts[name_key]

def git_operation(func):
    def wrapper(*args, **kwargs):
        user_info = get_authenticate_user()
        if user_info:
            return func(*args, **kwargs, user_info=user_info)
        else:
            print("Authentication failed. Operation aborted.")
    return wrapper


def git_clone(args):
    if args.user:
        user_info = get_authenticate_user(args.user)
        user_name = args.user
    else:
        user_info = get_authenticate_user()
        user_name = user_info['name']
    # 如果没传参的话user_info是global信息

    token = user_info['token']

    owner, repo_name = parse_github_url(args.repo)
    if not owner or not repo_name:
        print(f"Invalid repository format: {args.repo}")
        return

    clone_url = f"https://github.com/{owner}/{repo_name}.git"
    target_dir = repo_name

    try:
        callbacks = pygit2.RemoteCallbacks(pygit2.UserPass("x-access-token", token))
        repo = pygit2.clone_repository(clone_url, target_dir, callbacks=callbacks)
        print(f"Repository {owner}/{repo_name} cloned successfully to {target_dir}.")
        
        save_path_config(os.path.abspath(target_dir),user_name)
        print(f"Set local account for {target_dir} to {user_name}")

    except pygit2.GitError as e:
        print(f"Error cloning repository: {e}")



@git_operation
def git_pull(args,user_info):
    repo_root = find_git_repo(os.getcwd())
    if not repo_root:
        print("错误：当前目录不在 Git 仓库中")
        return
    token = user_info['token']
    repo = pygit2.Repository(repo_root)
    remote_name = args.origin
    branch_name = args.branch

    remote = repo.remotes[remote_name]

    callbacks = pygit2.RemoteCallbacks(credentials=pygit2.UserPass("x-access-token", token))

    remote.fetch(callbacks=callbacks)
    remote_master_id = repo.lookup_reference(f'refs/remotes/{remote_name}/{branch_name}').target
    merge_result, _ = repo.merge_analysis(remote_master_id)

    if merge_result & pygit2.GIT_MERGE_ANALYSIS_UP_TO_DATE:
        print("已经是最新的")
    elif merge_result & pygit2.GIT_MERGE_ANALYSIS_FASTFORWARD:
        repo.checkout_tree(repo.get(remote_master_id))
        master_ref = repo.lookup_reference(f'refs/heads/{branch_name}')
        master_ref.set_target(remote_master_id)
        repo.head.set_target(remote_master_id)
        print("Fast-forward 合并完成")
    else:
        print("需要手动合并")

@git_operation
def git_push(args,user_info):

    repo_root = find_git_repo(os.getcwd())
    if not repo_root:
        print("错误：当前目录不在 Git 仓库中")
        return

    repo = pygit2.Repository(repo_root)

    github_token = user_info['token']
    remote_name = args.origin
    branch_name = args.branch

    try:
        remote = repo.remotes[remote_name]
    except KeyError:
        print(f"错误：远程仓库 '{remote_name}' 不存在")
        return

    callbacks = pygit2.RemoteCallbacks(credentials=pygit2.UserPass("x-access-token", github_token))

    try:
        remote.push([f'refs/heads/{branch_name}:refs/heads/{branch_name}'], callbacks=callbacks)
        print(f"已推送到远程仓库 {remote_name} 的 {branch_name} 分支")
    except pygit2.GitError as e:
        print(f"推送失败：{str(e)}")


@git_operation
def git_commit(args,user_info):
    message = args.message


    accounts = load_accounts()
    github_token = user_info['token']
    name = user_info['name']
    email = user_info['email']
    if not name or not email:
        print("警告：无法获取完整的用户信息，放弃")
        return

    author = pygit2.Signature(name, email)
    committer = author

    repo_root = find_git_repo(os.getcwd())
    if not repo_root:
        print("错误：当前目录不在 Git 仓库中")
        return

    repo = pygit2.Repository(repo_root)
    if not message:
        print("错误：请提供提交信息")
        return

    
    tree = repo.index.write_tree()
    parents = [repo.head.target] if not repo.is_empty else []

    repo.create_commit('HEAD', author, committer, message, tree, parents)
    print(f"已提交: {message}")

@git_operation
def git_add(args):
    repo_path = find_git_repo(os.getcwd())
    if not repo_path:
        print("错误：当前目录不在 Git 仓库中")
        return

    repo = pygit2.Repository(repo_path)
    current_dir = os.getcwd()

    
    paths = args.file
    

    # 确保 paths 是一个列表
    if isinstance(paths, str):
        paths = [paths]

    files_added = []

    for path in paths:
        # 处理相对路径
        full_path = os.path.join(repo_path, path)
        
        if os.path.isfile(full_path):
            # 如果是文件，直接添加
            rel_path = os.path.relpath(full_path, repo_path)
            repo.index.add(rel_path)
            files_added.append(rel_path)
        elif os.path.isdir(full_path):
            # 如果是目录，添加目录下所有文件
            for file_path in glob.glob(os.path.join(full_path, '**'), recursive=True):
                if os.path.isfile(file_path):
                    rel_path = os.path.relpath(file_path, repo_path)
                    repo.index.add(rel_path)
                    files_added.append(rel_path)
        elif path == '.':
            # 添加所有更改
            for file_path in glob.glob(os.path.join(repo_path, '**'), recursive=True):
                if os.path.isfile(file_path):
                    rel_path = os.path.relpath(file_path, repo_path)
                    repo.index.add(rel_path)
                    files_added.append(rel_path)
        else:
            print(f"警告：路径 '{path}' 不存在或不是文件/目录")

    # 写入索引
    repo.index.write()

    # 打印添加的文件
    if files_added:
        print("已添加以下文件到暂存区：")
        for file in files_added:
            print(f"  {file}")
    else:
        print("没有文件被添加到暂存区")



def main():
    parser = argparse.ArgumentParser(description="GitHub Account Manager (gam)")
    subparsers = parser.add_subparsers(dest='command')

    # Add account
    add_parser = subparsers.add_parser('add_account', help='Add a new GitHub account')
    add_parser.set_defaults(func=add_account)

    # List accounts
    list_parser = subparsers.add_parser('list', help='List all GitHub accounts')
    list_parser.set_defaults(func=list_accounts)

    
    # Switch account globally
    global_parser = subparsers.add_parser('global', help='Switch to a GitHub account globally')
    global_parser.add_argument('name', help='GitHub username to switch to')
    global_parser.set_defaults(func=switch_global)

    # Remove account
    remove_parser = subparsers.add_parser('remove', help='Remove a GitHub account')
    remove_parser.add_argument('name', help='GitHub username to remove')
    remove_parser.set_defaults(func=remove_account)

    # Show current account
    now_parser = subparsers.add_parser('now', help='Show current Git account')
    now_parser.set_defaults(func=show_current_account)

    # Clone repository
    clone_parser = subparsers.add_parser('clone', help='Clone a GitHub repository')
    clone_parser.add_argument('repo', help='Repository to clone (format: owner/repo)')
    clone_parser.add_argument('-u', '--user', help='GitHub username to use for cloning')
    clone_parser.set_defaults(func=git_clone) 


    # add repository
    clone_parser = subparsers.add_parser('add', help='Clone a GitHub repository')
    clone_parser.add_argument('file', help='file or folder to add')
    clone_parser.set_defaults(func=git_add)


    # Commit changes
    commit_parser = subparsers.add_parser('commit', help='Commit changes to a GitHub repository')
    commit_parser.add_argument('message', help='Commit message')
    commit_parser.set_defaults(func=git_commit)

    # Push changes
    push_parser = subparsers.add_parser('push', help='Push changes to a GitHub repository')
    push_parser.add_argument('origin', help='remote name')
    push_parser.add_argument('branch', help='branch name')
    push_parser.set_defaults(func=git_push)

    # Pull changes
    pull_parser = subparsers.add_parser('pull', help='Pull changes from a GitHub repository')
    pull_parser.add_argument('origin', help='remote name')
    pull_parser.add_argument('branch', help='branch name')
    pull_parser.set_defaults(func=git_pull)

    args = parser.parse_args()
    
    if args.command:
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()