# test_records 目录规范

该目录用于保存所有测试执行记录，确保结果可复核、可复现。

## 目录结构

`result/test_records/<phase>/<UTC_TIMESTAMP>_<test_name>/`

每条记录目录应包含：

- `record.md`：测试概要（配置、命令、结论、退出码）
- `command.sh`：可直接重跑的命令
- `stdout.log`：标准输出日志
- `stderr.log`：错误输出日志
- `exit_code.txt`：执行退出码
- `env_snapshot.txt`：环境快照（branch、commit、python、pip）

## 记录生成方式

建议统一使用以下脚本生成记录：

`scripts/testing/run_and_record.sh`

示例：

`bash scripts/testing/run_and_record.sh --phase phase1_baseline --name smoke -- python3 experiments/run_gsm8k.py --help`

## 合规要求

1. 不允许手工省略关键文件（`record.md`、`command.sh`、`stdout.log`、`exit_code.txt`）。
2. 记录目录必须进入版本控制（除非日志体积超限并有替代策略）。
3. 每个 phase 更新完成后必须 commit。

