#!/usr/bin/env python3
"""
MRM Toolkit - Validation Scripts
Bộ công cụ kiểm định và tự động hóa cho Modular Research Markdown Framework

Các chức năng chính:
1. validate_frontmatter: Kiểm tra YAML frontmatter đầy đủ và hợp lệ
2. count_lines: Đếm số dòng nội dung (không tính frontmatter & comment)
3. check_links: Phát hiện broken links và cross-references
4. check_ai_context: Xác minh trường ai_context có task downstream rõ ràng
5. generate_index: Tự động sinh index.md từ tree thư mục
6. assemble_report: Ghép nhiều module thành báo cáo hoàn chỉnh

Usage:
    python mrm_validator.py validate <path>
    python mrm_validator.py count-lines <file>
    python mrm_validator.py check-links <directory>
    python mrm_validator.py generate-index <directory>
"""

import os
import sys
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ValidationResult:
    """Kết quả kiểm định một file MRM"""
    file_path: str
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    line_count: int
    has_frontmatter: bool
    has_ai_context: bool


class MRMValidator:
    """Bộ kiểm định chuẩn MRM cho file Markdown"""
    
    MAX_LINES = 300
    REQUIRED_FRONTMATTER_FIELDS = ['id', 'title', 'status', 'tags', 'summary', 'ai_context']
    VALID_STATUSES = ['draft', 'review', 'final', 'auto-generated']
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
    
    def log(self, message: str):
        if self.verbose:
            print(message)
    
    def extract_frontmatter(self, content: str) -> Tuple[Optional[Dict], str]:
        """Tách YAML frontmatter khỏi nội dung Markdown"""
        pattern = r'^---\n(.*?)\n---\n(.*)'
        match = re.match(pattern, content, re.DOTALL)
        
        if not match:
            return None, content
        
        try:
            frontmatter = yaml.safe_load(match.group(1))
            body = match.group(2)
            return frontmatter, body
        except yaml.YAMLError as e:
            self.log(f"⚠️  Lỗi parse YAML: {e}")
            return None, content
    
    def count_content_lines(self, content: str) -> int:
        """Đếm số dòng nội dung (không tính frontmatter, comment, dòng trống liên tiếp)"""
        _, body = self.extract_frontmatter(content)
        
        lines = body.split('\n')
        content_lines = []
        empty_count = 0
        
        for line in lines:
            # Bỏ qua comment HTML và dòng trống
            if line.strip().startswith('<!--') or line.strip().endswith('-->'):
                continue
            if line.strip() == '':
                empty_count += 1
                if empty_count <= 2:  # Cho phép tối đa 2 dòng trống liên tiếp
                    content_lines.append(line)
            else:
                empty_count = 0
                content_lines.append(line)
        
        return len(content_lines)
    
    def validate_frontmatter(self, frontmatter: Optional[Dict]) -> Tuple[bool, List[str], List[str]]:
        """Kiểm tra frontmatter có đủ trường bắt buộc và giá trị hợp lệ"""
        errors = []
        warnings = []
        
        if frontmatter is None:
            errors.append("❌ Thiếu YAML frontmatter")
            return False, errors, warnings
        
        # Kiểm tra trường bắt buộc
        for field in self.REQUIRED_FRONTMATTER_FIELDS:
            if field not in frontmatter:
                errors.append(f"❌ Thiếu trường bắt buộc: {field}")
        
        # Validate status
        if 'status' in frontmatter and frontmatter['status'] not in self.VALID_STATUSES:
            errors.append(f"❌ Status '{frontmatter['status']}' không hợp lệ. Chỉ chấp nhận: {self.VALID_STATUSES}")
        
        # Validate summary độ dài
        if 'summary' in frontmatter:
            summary_sentences = frontmatter['summary'].split('.')
            if len([s for s in summary_sentences if s.strip()]) > 2:
                warnings.append(f"⚠️  Summary nên ≤2 câu (hiện tại: {len(summary_sentences)} câu)")
        
        # Validate ai_context
        if 'ai_context' not in frontmatter:
            errors.append("❌ Thiếu trường ai_context - bắt buộc cho AI-Native Boundary")
        elif len(frontmatter.get('ai_context', '').strip()) < 10:
            warnings.append("⚠️  ai_context quá ngắn, nên mô tả rõ task downstream")
        
        # Validate tags
        if 'tags' in frontmatter:
            if not isinstance(frontmatter['tags'], list):
                errors.append("❌ Tags phải là danh sách (list)")
            elif len(frontmatter['tags']) == 0:
                warnings.append("⚠️  Nên có ít nhất 1 tag")
        
        is_valid = len(errors) == 0
        return is_valid, errors, warnings
    
    def check_tldr(self, content: str) -> Tuple[bool, List[str]]:
        """Kiểm tra sự tồn tại của TL;DR section"""
        errors = []
        
        # Tìm TL;DR pattern
        tldr_pattern = r'>\s*\*\*TL;DR\*\*:?\s*.+'
        if not re.search(tldr_pattern, content, re.IGNORECASE):
            errors.append("❌ Thiếu section TL;DR (bắt buộc theo Progressive Disclosure)")
            return False, errors
        
        # Kiểm tra độ dài TL;DR (nên 1 dòng)
        tldr_matches = re.findall(r'>\s*\*\*TL;DR\*\*:?\s*(.+)', content, re.IGNORECASE)
        if tldr_matches:
            tldr_text = tldr_matches[0]
            if '\n' in tldr_text or len(tldr_text.split('.')) > 2:
                errors.append("⚠️  TL;DR nên ngắn gọn, tối đa 1-2 câu")
        
        return len(errors) == 0, errors
    
    def check_cross_references(self, content: str, directory: str) -> Tuple[bool, List[str]]:
        """Kiểm tra cross-references trỏ đến file tồn tại"""
        errors = []
        warnings = []
        
        # Tìm [[id]] references
        wikilink_pattern = r'\[\[(.+?)\]\]'
        wikilinks = re.findall(wikilink_pattern, content)
        
        # Tìm markdown links tương đối
        mdlink_pattern = r'\[([^\]]+)\]\((\.?/?[^\)]+\.(md|MD))\)'
        mdlinks = re.findall(mdlink_pattern, content)
        
        # Kiểm tra wikilinks (chỉ cảnh báo nếu không phải là reference đến file chưa tạo)
        # Wikilink trong MRM có thể là placeholder cho nội dung tương lai
        for link_id in wikilinks:
            # Bỏ qua các wikilink đặc biệt
            if link_id in ['id', 'id-file-goc', 'id-lien-quan', 'id-lien-quan-1', 'id-lien-quan-2']:
                continue
            
            # Tìm file có id này trong frontmatter
            found = False
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith('.md'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                file_content = f.read()
                                frontmatter, _ = self.extract_frontmatter(file_content)
                                if frontmatter and frontmatter.get('id') == link_id:
                                    found = True
                                    break
                        except Exception:
                            pass
                if found:
                    break
            
            # Chỉ warning nếu link có pattern child hoặc số, không warning link tương lai
            if not found:
                # Kiểm tra xem đây có phải là reference "sẽ tạo" không
                context_pattern = rf'\[\[{link_id}\]\].*\(sẽ tạo|placeholder|tương lai\)'
                if re.search(context_pattern, content, re.IGNORECASE):
                    continue  # Bỏ qua warning cho reference tương lai
                warnings.append(f"⚠️  Wikilink [[{link_id}]] không tìm thấy file đích (có thể là placeholder)")
        
        # Kiểm tra markdown links
        for link_text, link_path, _ in mdlinks:
            # Resolve relative path
            abs_path = os.path.abspath(os.path.join(directory, link_path))
            if not os.path.exists(abs_path):
                errors.append(f"❌ Broken link: [{link_text}]({link_path})")
        
        return len(errors) == 0, errors + warnings
    
    def check_heading_structure(self, content: str) -> Tuple[bool, List[str]]:
        """Kiểm tra cấu trúc heading không bị lỗi"""
        errors = []
        
        _, body = self.extract_frontmatter(content)
        lines = body.split('\n')
        
        # Tìm heading rỗng hoặc thừa cấp
        prev_level = 0
        for i, line in enumerate(lines):
            heading_match = re.match(r'^(#{1,6})\s*(.*)', line)
            if heading_match:
                level = len(heading_match.group(1))
                text = heading_match.group(2).strip()
                
                if not text:
                    errors.append(f"❌ Heading rỗng ở dòng {i+1}")
                
                # Cảnh báo nếu nhảy cấp quá lớn (optional)
                if level > prev_level + 1 and prev_level > 0:
                    errors.append(f"⚠️  Nhảy cấp heading từ H{prev_level} lên H{level} ở dòng {i+1}")
                
                prev_level = level
        
        return len(errors) == 0, errors
    
    def validate_file(self, file_path: str, check_links: bool = False) -> ValidationResult:
        """Kiểm định một file MRM đơn lẻ"""
        errors = []
        warnings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return ValidationResult(
                file_path=file_path,
                is_valid=False,
                errors=[f"❌ Không đọc được file: {e}"],
                warnings=[],
                line_count=0,
                has_frontmatter=False,
                has_ai_context=False
            )
        
        # Extract frontmatter
        frontmatter, _ = self.extract_frontmatter(content)
        has_frontmatter = frontmatter is not None
        has_ai_context = frontmatter is not None and 'ai_context' in frontmatter
        
        # Validate frontmatter
        fm_valid, fm_errors, fm_warnings = self.validate_frontmatter(frontmatter)
        errors.extend(fm_errors)
        warnings.extend(fm_warnings)
        
        # Check line count
        line_count = self.count_content_lines(content)
        if line_count > self.MAX_LINES:
            errors.append(f"❌ Vượt quá số dòng tối đa ({line_count}/{self.MAX_LINES}). Cần tách file.")
        
        # Check TL;DR
        tldr_valid, tldr_errors = self.check_tldr(content)
        errors.extend(tldr_errors)
        
        # Check heading structure
        heading_valid, heading_errors = self.check_heading_structure(content)
        errors.extend(heading_errors)
        
        # Check cross-references (nếu yêu cầu)
        if check_links:
            directory = os.path.dirname(file_path) or '.'
            link_valid, link_errors = self.check_cross_references(content, directory)
            errors.extend(link_errors)
        
        return ValidationResult(
            file_path=file_path,
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            line_count=line_count,
            has_frontmatter=has_frontmatter,
            has_ai_context=has_ai_context
        )
    
    def validate_directory(self, directory: str) -> List[ValidationResult]:
        """Kiểm định tất cả file .md trong thư mục"""
        results = []
        
        for root, dirs, files in os.walk(directory):
            # Bỏ qua thư mục ẩn và outputs
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'outputs']
            
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    result = self.validate_file(file_path, check_links=True)
                    results.append(result)
        
        return results
    
    def print_report(self, results: List[ValidationResult]):
        """In báo cáo kiểm định"""
        total = len(results)
        valid = sum(1 for r in results if r.is_valid)
        invalid = total - valid
        
        print("\n" + "="*60)
        print("📊 BÁO CÁO KIỂM ĐỊNH MRM")
        print("="*60)
        print(f"Tổng số file: {total}")
        print(f"✅ Hợp lệ: {valid}")
        print(f"❌ Không hợp lệ: {invalid}")
        print(f"Tỷ lệ đạt: {valid/total*100:.1f}%")
        print("="*60)
        
        # Chi tiết file lỗi
        error_files = [r for r in results if not r.is_valid]
        if error_files:
            print("\n🔴 FILE CÓ LỖI:")
            for result in error_files:
                print(f"\n📄 {result.file_path}")
                print(f"   Dòng nội dung: {result.line_count}")
                print(f"   Có frontmatter: {'✅' if result.has_frontmatter else '❌'}")
                print(f"   Có ai_context: {'✅' if result.has_ai_context else '❌'}")
                
                if result.errors:
                    print("   Lỗi:")
                    for err in result.errors:
                        print(f"     - {err}")
                
                if result.warnings:
                    print("   Cảnh báo:")
                    for warn in result.warnings:
                        print(f"     - {warn}")
        
        # File hợp lệ
        valid_files = [r for r in results if r.is_valid]
        if valid_files:
            print(f"\n✅ FILE HỢP LỆ ({len(valid_files)}):")
            for result in valid_files:
                print(f"   ✓ {result.file_path} ({result.line_count} dòng)")
        
        print("\n" + "="*60)


def generate_index(directory: str, output_path: Optional[str] = None) -> str:
    """Tự động sinh index.md từ cây thư mục MRM"""
    index_content = f"""---
id: index
title: "Mục lục Nghiên cứu"
status: auto-generated
tags: [index, navigation]
summary: "Mục lục tự động sinh từ cây thư mục MRM."
ai_context: "Dùng để điều hướng và hiểu cấu trúc tổng thể của dự án nghiên cứu."
---

# Mục lục Nghiên cứu

> **TL;DR**: Tổng quan cấu trúc tài liệu nghiên cứu với {len(list(Path(directory).rglob('*.md')))} file.

## Cấu trúc Thư mục

```
"""
    
    # Generate tree structure
    tree_lines = []
    for root, dirs, files in os.walk(directory):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        level = root.replace(directory, '').count(os.sep)
        indent = '│   ' * level
        tree_lines.append(f"{indent}📁 {os.path.basename(root)}/")
        
        subindent = '│   ' * (level + 1)
        for file in sorted(files):
            if file.endswith('.md'):
                tree_lines.append(f"{subindent}📄 {file}")
    
    index_content += '\n'.join(tree_lines)
    index_content += """
```

## Danh sách File theo Trạng thái

"""
    
    # Group files by status
    validator = MRMValidator(verbose=False)
    results = validator.validate_directory(directory)
    
    status_groups = {'draft': [], 'review': [], 'final': [], 'unknown': []}
    
    for result in results:
        if 'index.md' in result.file_path:
            continue
        
        try:
            with open(result.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                frontmatter, _ = validator.extract_frontmatter(content)
                
                if frontmatter:
                    status = frontmatter.get('status', 'unknown')
                    title = frontmatter.get('title', os.path.basename(result.file_path))
                    file_id = frontmatter.get('id', '')
                    
                    if status in status_groups:
                        status_groups[status].append((title, result.file_path, file_id))
                    else:
                        status_groups['unknown'].append((title, result.file_path, file_id))
        except Exception:
            status_groups['unknown'].append(('Unknown', result.file_path, ''))
    
    for status, files in status_groups.items():
        if files:
            status_emoji = {'draft': '🟡', 'review': '🟠', 'final': '✅', 'unknown': '⚪'}
            index_content += f"\n### {status_emoji.get(status, '')} {status.upper()}\n\n"
            for title, path, file_id in sorted(files, key=lambda x: x[0]):
                rel_path = os.path.relpath(path, os.path.dirname(output_path) if output_path else directory)
                index_content += f"- [{title}]({rel_path})"
                if file_id:
                    index_content += f" `[[{file_id}]]`"
                index_content += "\n"
    
    index_content += f"\n---\n\n*Tự động sinh bởi MRM Toolkit vào {datetime.now().strftime('%Y-%m-%d %H:%M')}.*\n"
    
    # Write to file
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
        print(f"✅ Đã sinh index.md tại: {output_path}")
    else:
        output_path = os.path.join(directory, 'index.md')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
        print(f"✅ Đã sinh index.md tại: {output_path}")
    
    return index_content


def assemble_report(input_dir: str, output_path: str, include_toc: bool = True):
    """Ghép nhiều module thành báo cáo hoàn chỉnh"""
    validator = MRMValidator(verbose=False)
    results = validator.validate_directory(input_dir)
    
    # Sort by file ID or path
    file_contents = []
    for result in sorted(results, key=lambda r: r.file_path):
        if 'index.md' in result.file_path:
            continue
        
        try:
            with open(result.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                frontmatter, body = validator.extract_frontmatter(content)
                
                if frontmatter:
                    title = frontmatter.get('title', 'Untitled')
                    file_id = frontmatter.get('id', '')
                    
                    file_contents.append({
                        'title': title,
                        'id': file_id,
                        'body': body,
                        'path': result.file_path
                    })
        except Exception as e:
            print(f"⚠️  Bỏ qua file {result.file_path}: {e}")
    
    # Build report
    report = f"""---
title: "Báo cáo Nghiên cứu Hoàn chỉnh"
author: "MRM Auto-Assembler"
date: "{datetime.now().strftime('%Y-%m-%d')}"
tags: [report, assembled]
---

# Báo cáo Nghiên cứu Hoàn chỉnh

> **Generated by MRM Toolkit** | {len(file_contents)} modules | {datetime.now().strftime('%Y-%m-%d %H:%M')}

"""
    
    if include_toc:
        report += "## Mục lục\n\n"
        for i, fc in enumerate(file_contents, 1):
            safe_title = fc['title'].replace(' ', '-').lower()
            report += f"{i}. [{fc['title']}](#{safe_title})\n"
        report += "\n---\n\n"
    
    for fc in file_contents:
        report += f"\n## {fc['title']}\n"
        if fc['id']:
            report += f"*File ID: `{fc['id']}`*\n"
        report += fc['body']
        report += "\n---\n"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ Đã ghép báo cáo: {output_path} ({len(file_contents)} modules)")


def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    validator = MRMValidator()
    
    if command == 'validate':
        if len(sys.argv) < 3:
            print("Usage: python mrm_validator.py validate <directory>")
            sys.exit(1)
        directory = sys.argv[2]
        results = validator.validate_directory(directory)
        validator.print_report(results)
        sys.exit(0 if all(r.is_valid for r in results) else 1)
    
    elif command == 'validate-file':
        if len(sys.argv) < 3:
            print("Usage: python mrm_validator.py validate-file <file.md>")
            sys.exit(1)
        file_path = sys.argv[2]
        result = validator.validate_file(file_path, check_links=True)
        
        print(f"\n📄 {file_path}")
        print(f"Dòng nội dung: {result.line_count}")
        print(f"Có frontmatter: {'✅' if result.has_frontmatter else '❌'}")
        print(f"Có ai_context: {'✅' if result.has_ai_context else '❌'}")
        
        if result.errors:
            print("\nLỗi:")
            for err in result.errors:
                print(f"  - {err}")
        
        if result.warnings:
            print("\nCảnh báo:")
            for warn in result.warnings:
                print(f"  - {warn}")
        
        sys.exit(0 if result.is_valid else 1)
    
    elif command == 'count-lines':
        if len(sys.argv) < 3:
            print("Usage: python mrm_validator.py count-lines <file.md>")
            sys.exit(1)
        file_path = sys.argv[2]
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            line_count = validator.count_content_lines(content)
            print(f"📊 Số dòng nội dung: {line_count}/{validator.MAX_LINES}")
            if line_count > validator.MAX_LINES:
                print(f"⚠️  Vượt quá giới hạn! Cần tách file.")
                sys.exit(1)
            else:
                print("✅ Đạt giới hạn dòng.")
                sys.exit(0)
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            sys.exit(1)
    
    elif command == 'generate-index':
        if len(sys.argv) < 3:
            print("Usage: python mrm_validator.py generate-index <directory> [output_path]")
            sys.exit(1)
        directory = sys.argv[2]
        output_path = sys.argv[3] if len(sys.argv) > 3 else None
        generate_index(directory, output_path)
    
    elif command == 'assemble':
        if len(sys.argv) < 4:
            print("Usage: python mrm_validator.py assemble <input_dir> <output_path>")
            sys.exit(1)
        input_dir = sys.argv[2]
        output_path = sys.argv[3]
        assemble_report(input_dir, output_path)
    
    else:
        print(f"❌ Command không hợp lệ: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()
