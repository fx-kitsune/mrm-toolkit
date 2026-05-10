# MRM Toolkit - Bộ Công cụ Modular Research Markdown

## Giới thiệu

MRM (Modular Research Markdown) Toolkit là bộ công cụ hỗ trợ viết và quản lý tài liệu nghiên cứu theo kiến trúc module hóa, tối ưu cho cả **người đọc** và **AI xử lý**.

## Cài đặt Nhanh

### Yêu cầu Hệ thống

- Python 3.8+
- PyYAML (`pip install pyyaml`)

### Cấu trúc Thư mục

```
mrm-toolkit/
├── scripts/              # Python validation scripts
│   └── mrm_validator.py  # Tool chính
├── templates/            # Template chuẩn
│   └── note-template.md
├── research/             # Thư mục nghiên cứu mẫu
│   ├── index.md          # Mục lục tự động
│   ├── meta/             # Metadata & overview
│   ├── notes/            # Atomic notes
│   ├── core/             # Nội dung chính
│   └── outputs/          # Báo cáo đã assemble
└── docs/                 # Tài liệu hướng dẫn
    └── MRM-Skill-ModularResearchDocWriter.md
```

## Sử dụng Cơ bản

### 1. Kiểm định File/Thư mục

```bash
# Kiểm tra toàn bộ thư mục
python scripts/mrm_validator.py validate research/

# Kiểm tra file đơn lẻ
python scripts/mrm_validator.py validate-file research/core/core-01-atomic-structure.md

# Đếm số dòng nội dung
python scripts/mrm_validator.py count-lines research/core/core-01-atomic-structure.md
```

### 2. Tự động sinh Index

```bash
# Tạo index.md từ cây thư mục
python scripts/mrm_validator.py generate-index research/

# Hoặc chỉ định output path
python scripts/mrm_validator.py generate-index research/ docs/custom-index.md
```

### 3. Ghép Báo cáo Hoàn chỉnh

```bash
# Assemble tất cả module thành báo cáo
python scripts/mrm_validator.py assemble research/ outputs/final-report.md
```

## Checklist Chuẩn MRM

Trước khi commit file, đảm bảo:

- [ ] YAML frontmatter đầy đủ 6 trường bắt buộc
- [ ] `ai_context` mô tả rõ task downstream
- [ ] TL;DR ≤ 1 dòng
- [ ] Summary ≤ 2 câu
- [ ] Số dòng nội dung ≤ 300
- [ ] Cross-reference dùng `[[id]]` hoặc markdown link kiểm chứng
- [ ] Không có heading rỗng

## Tích hợp Workflow

### VS Code

Thêm vào `.vscode/settings.json`:

```json
{
  "markdownlint.config": {
    "MD041": false,
    "MD025": false
  },
  "files.associations": {
    "*.md": "markdown"
  }
}
```

### Git Hooks

Tạo `.git/hooks/pre-commit`:

```bash
#!/bin/bash
python scripts/mrm_validator.py validate research/
if [ $? -ne 0 ]; then
  echo "❌ Validation failed. Please fix errors before commit."
  exit 1
fi
```

### GitHub Actions

Tạo `.github/workflows/mrm-validate.yml`:

```yaml
name: MRM Validation

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install pyyaml
      - name: Validate MRM files
        run: python scripts/mrm_validator.py validate research/
```

## Template Usage

Copy template và điền thông tin:

```bash
cp templates/note-template.md research/notes/note-YYYY-MM-DD-topic.md
```

Sau đó chỉnh sửa:
1. Thay `[Tiêu đề]` bằng tiêu đề thực tế
2. Điền `id`, `tags`, `summary`, `ai_context` trong frontmatter
3. Viết TL;DR (1 dòng)
4. Viết nội dung chính theo sections
5. Chạy validation trước khi lưu

## Ví dụ Frontmatter Chuẩn

```yaml
---
id: core-01-atomic-structure
title: "Atomic File Structure - Cấu trúc File Nguyên tử"
status: draft | review | final
tags: [atomicity, chunking, file-structure]
summary: "Quy tắc tổ chức file theo nguyên tắc atomic: 1 file = 1 chủ đề, giới hạn 300 dòng."
ai_context: "Dùng cho AI hiểu và áp dụng quy tắc chunking. Khi gặp nội dung dài, tự động đề xuất tách file con."
---
```

## Tài liệu Tham khảo

- [Skill ModularResearchDocWriter](docs/MRM-Skill-ModularResearchDocWriter.md) - System prompt chi tiết
- [research/index.md](research/index.md) - Mục lục ví dụ
- [templates/note-template.md](templates/note-template.md) - Template gốc

## License

MIT License - Tự do sử dụng và chỉnh sửa.
