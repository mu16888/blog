#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Git Data API 推送兜底：github.com 的 git 协议被代理拦（502），但 api.github.com 通。
走 api.github.com 的 git data API（create blob/tree/commit + update ref）完成推送。
用法：python _push_api.py <待推送文件相对路径...>
"""
import base64, json, subprocess, sys, time

REPO = "mu16888/blog"
BRANCH = "main"


def gh(path, method="GET", data=None, retries=3):
    for i in range(retries):
        cmd = ["gh", "api", path]
        if method != "GET":
            cmd += ["-X", method]
        if data is not None:
            cmd += ["--input", "-"]
        p = subprocess.run(cmd, input=json.dumps(data) if data else None,
                           capture_output=True, text=True, encoding="utf-8")
        if p.returncode == 0:
            return json.loads(p.stdout) if p.stdout.strip() else {}
        last = p.stderr.strip()
        print(f"  重试 {i+1}/{retries}: {last[:160]}")
        time.sleep(4)
    raise RuntimeError(f"API 失败 {method} {path}: {last}")


def main():
    files = sys.argv[1:]
    if not files:
        print("用法: python _push_api.py <file...>")
        sys.exit(1)

    head = gh(f"repos/{REPO}/git/ref/heads/{BRANCH}")
    base_commit = head["object"]["sha"]
    base_commit_obj = gh(f"repos/{REPO}/git/commits/{base_commit}")
    base_tree = base_commit_obj["tree"]["sha"]
    print(f"远端当前 HEAD = {base_commit}")

    # 校验本地未推送提交
    local = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                           text=True, encoding="utf-8").stdout.strip()
    n = subprocess.run(["git", "rev-list", f"{base_commit}..{local}"],
                       capture_output=True, text=True, encoding="utf-8").stdout.split()
    msg = ""
    if n:
        msg = subprocess.run(["git", "log", "-1", "--format=%B", local],
                             capture_output=True, text=True, encoding="utf-8").stdout.strip()
    else:
        msg = "同步 custom.css 分割线橘红色"
    print(f"本地 HEAD = {local}，待推送 {len(n)} 个提交")

    entries = []
    for f in files:
        content = open(f, "rb").read()
        blob = gh(f"repos/{REPO}/git/blobs", "POST",
                  {"content": base64.b64encode(content).decode(), "encoding": "base64"})
        print(f"  blob {f} = {blob['sha'][:10]}")
        entries.append({"path": f, "mode": "100644", "type": "blob", "sha": blob["sha"]})

    tree = gh(f"repos/{REPO}/git/trees", "POST",
              {"base_tree": base_tree, "tree": entries})
    print(f"  tree = {tree['sha'][:10]}")

    commit = gh(f"repos/{REPO}/git/commits", "POST", {
        "message": msg, "tree": tree["sha"], "parents": [base_commit]})
    print(f"  commit = {commit['sha']}")

    # 快进校验：父提交必须等于当前远端 HEAD
    if commit["parents"][0]["sha"] != base_commit:
        raise RuntimeError("非快进，已中止")
    gh(f"repos/{REPO}/git/refs/heads/{BRANCH}", "PATCH",
       {"sha": commit["sha"], "force": False})
    print(f"PUSH_OK -> {commit['sha']}")


if __name__ == "__main__":
    main()