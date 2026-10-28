# 问题跟踪

本项目的任务与规格记录在 GitHub Issues，使用 gh CLI 操作。
在仓库目录运行命令，由 Git remote 确定目标仓库。

- 发布任务或规格：创建 GitHub Issue。
- 获取任务：gh issue view <number> --comments，并读取标签。
- 列出任务：gh issue list，按状态和标签筛选。
- 创建与评论使用 gh issue create、gh issue comment。
  多行正文写入临时文件，通过 --body-file 传入。
- 更新标签：gh issue edit <number> --add-label 或 --remove-label。
- 关闭任务：gh issue close <number>。

## Pull requests as a triage surface

**PRs as a request surface: no.**
