# ModularResearchDocWriter

ModularResearchDocWriter là **agent toolkit hoàn chỉnh** để biến yêu cầu nghiên cứu/tài liệu thành hệ thống Markdown module hóa, dễ đọc với con người và an toàn cho AI downstream.

Repo đã được tách rõ thành 4 lớp:

1. **Skill** — hành vi tái sử dụng cho agent.
2. **Workflow** — quy trình thao tác từ scope đến validate/assemble.
3. **Contracts** — chuẩn output và rubric chất lượng.
4. **Adapters** — file hướng dẫn cài vào Codex, Claude Code, Gemini, Copilot, Cursor và agent IDE khác.

## Điểm vào chính

| Nhu cầu | File |
|---|---|
| Đọc tổng quan toolkit | [`mrm-toolkit/README.md`](mrm-toolkit/README.md) |
| Manifest máy đọc được | [`mrm-toolkit/manifest.yaml`](mrm-toolkit/manifest.yaml) |
| Skill canonical | [`mrm-toolkit/skills/modular-research-doc-writer/SKILL.md`](mrm-toolkit/skills/modular-research-doc-writer/SKILL.md) |
| Workflow agent | [`mrm-toolkit/workflows/MRM-WORKFLOW.md`](mrm-toolkit/workflows/MRM-WORKFLOW.md) |
| Output contract | [`mrm-toolkit/contracts/OUTPUT-CONTRACT.md`](mrm-toolkit/contracts/OUTPUT-CONTRACT.md) |
| Quality rubric | [`mrm-toolkit/contracts/QUALITY-RUBRIC.md`](mrm-toolkit/contracts/QUALITY-RUBRIC.md) |
| Prompt cũ/legacy | [`mrm-toolkit/docs/MRM-Skill-ModularResearchDocWriter.md`](mrm-toolkit/docs/MRM-Skill-ModularResearchDocWriter.md) |
| Kế hoạch nâng cấp cũ/legacy | [`mrm-toolkit/docs/UPGRADE-PLAN-AgentSkill.md`](mrm-toolkit/docs/UPGRADE-PLAN-AgentSkill.md) |

## Cài adapter cho agent

```bash
# Codex / AGENTS.md
python mrm-toolkit/scripts/mrm_validator.py install-adapter codex /path/to/project

# Claude Code / CLAUDE.md
python mrm-toolkit/scripts/mrm_validator.py install-adapter claude /path/to/project

# Gemini / GEMINI.md
python mrm-toolkit/scripts/mrm_validator.py install-adapter gemini /path/to/project

# GitHub Copilot / .github/copilot-instructions.md
python mrm-toolkit/scripts/mrm_validator.py install-adapter copilot /path/to/project

# Cursor / .cursor/rules/mrm.mdc
python mrm-toolkit/scripts/mrm_validator.py install-adapter cursor /path/to/project
```

Thêm `--overwrite` nếu muốn ghi đè file adapter đã tồn tại.

## Kiểm định MRM

```bash
python mrm-toolkit/scripts/mrm_validator.py validate mrm-toolkit/research
python mrm-toolkit/scripts/mrm_validator.py generate-index mrm-toolkit/research
python mrm-toolkit/scripts/mrm_validator.py assemble mrm-toolkit/research mrm-toolkit/research/outputs/final-report.md
```

## Khi nào dùng toolkit này?

- Tách tài liệu dài thành atomic modules.
- Chuẩn hóa research notes cho nhiều agent cùng đọc.
- Tạo file hướng dẫn local cho Codex, Claude Code, Gemini, Copilot, Cursor.
- Validate frontmatter, TL;DR, AI context, line limit và cross-reference.
- Assemble module đã review thành báo cáo cuối.

## License

MIT License.
