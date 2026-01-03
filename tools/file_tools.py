"""File operation tools for the CLI agent."""

import os
from pathlib import Path

from .registry import registry


def _is_safe_path(path: str, base_dir: Path) -> bool:
    """Check if the path is within the allowed base directory.

    Args:
        path: The path to check.
        base_dir: The base directory that paths must be within.

    Returns:
        True if the path is safe, False otherwise.
    """
    try:
        resolved = Path(path).resolve()
        return str(resolved).startswith(str(base_dir.resolve()))
    except (OSError, ValueError):
        return False


# Get the working directory (project root)
WORKING_DIR = Path.cwd()


@registry.register("read_file", "读取文件内容")
def read_file(path: str) -> str:
    """Read the contents of a file.

    Args:
        path: The path to the file to read. Can be absolute or relative to the working directory.

    Returns:
        The contents of the file, or an error message if the file cannot be read.
    """
    try:
        file_path = Path(path)
        if not file_path.is_absolute():
            file_path = WORKING_DIR / file_path

        if not _is_safe_path(str(file_path), WORKING_DIR):
            return f"错误: 无法访问工作目录外的文件: {path}"

        if not file_path.exists():
            return f"错误: 文件不存在: {path}"

        if not file_path.is_file():
            return f"错误: 路径不是文件: {path}"

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        return content
    except PermissionError:
        return f"错误: 没有权限读取文件: {path}"
    except UnicodeDecodeError:
        return f"错误: 无法以文本方式读取文件 (可能是二进制文件): {path}"
    except Exception as e:
        return f"错误: 读取文件失败: {e}"


@registry.register("write_file", "写入/创建文件")
def write_file(path: str, content: str) -> str:
    """Write content to a file. Creates the file if it doesn't exist.

    Args:
        path: The path to the file to write. Can be absolute or relative to the working directory.
        content: The content to write to the file.

    Returns:
        A success message, or an error message if the file cannot be written.
    """
    try:
        file_path = Path(path)
        if not file_path.is_absolute():
            file_path = WORKING_DIR / file_path

        if not _is_safe_path(str(file_path), WORKING_DIR):
            return f"错误: 无法在工作目录外创建文件: {path}"

        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return f"成功: 已写入文件 {path}"
    except PermissionError:
        return f"错误: 没有权限写入文件: {path}"
    except Exception as e:
        return f"错误: 写入文件失败: {e}"


@registry.register("list_directory", "列出目录内容")
def list_directory(path: str = ".") -> str:
    """List the contents of a directory.

    Args:
        path: The path to the directory to list. Defaults to the current working directory.

    Returns:
        A formatted list of directory contents, or an error message.
    """
    try:
        dir_path = Path(path)
        if not dir_path.is_absolute():
            dir_path = WORKING_DIR / dir_path

        if not _is_safe_path(str(dir_path), WORKING_DIR):
            return f"错误: 无法访问工作目录外的目录: {path}"

        if not dir_path.exists():
            return f"错误: 目录不存在: {path}"

        if not dir_path.is_dir():
            return f"错误: 路径不是目录: {path}"

        items = []
        for item in sorted(dir_path.iterdir()):
            if item.name.startswith("."):
                continue  # Skip hidden files
            item_type = "📁" if item.is_dir() else "📄"
            size = ""
            if item.is_file():
                size_bytes = item.stat().st_size
                if size_bytes < 1024:
                    size = f" ({size_bytes} B)"
                elif size_bytes < 1024 * 1024:
                    size = f" ({size_bytes / 1024:.1f} KB)"
                else:
                    size = f" ({size_bytes / (1024 * 1024):.1f} MB)"
            items.append(f"{item_type} {item.name}{size}")

        if not items:
            return f"目录 {path} 为空"

        return f"目录 {path} 的内容:\n" + "\n".join(items)
    except PermissionError:
        return f"错误: 没有权限访问目录: {path}"
    except Exception as e:
        return f"错误: 列出目录失败: {e}"


@registry.register("delete_file", "删除文件")
def delete_file(path: str) -> str:
    """Delete a file.

    Args:
        path: The path to the file to delete. Can be absolute or relative to the working directory.

    Returns:
        A success message, or an error message if the file cannot be deleted.
    """
    try:
        file_path = Path(path)
        if not file_path.is_absolute():
            file_path = WORKING_DIR / file_path

        if not _is_safe_path(str(file_path), WORKING_DIR):
            return f"错误: 无法删除工作目录外的文件: {path}"

        if not file_path.exists():
            return f"错误: 文件不存在: {path}"

        if not file_path.is_file():
            return f"错误: 路径不是文件 (不能删除目录): {path}"

        file_path.unlink()
        return f"成功: 已删除文件 {path}"
    except PermissionError:
        return f"错误: 没有权限删除文件: {path}"
    except Exception as e:
        return f"错误: 删除文件失败: {e}"


@registry.register("file_exists", "检查文件是否存在")
def file_exists(path: str) -> str:
    """Check if a file or directory exists.

    Args:
        path: The path to check. Can be absolute or relative to the working directory.

    Returns:
        Information about whether the path exists and its type.
    """
    try:
        file_path = Path(path)
        if not file_path.is_absolute():
            file_path = WORKING_DIR / file_path

        if not _is_safe_path(str(file_path), WORKING_DIR):
            return f"错误: 无法检查工作目录外的路径: {path}"

        if not file_path.exists():
            return f"路径不存在: {path}"

        if file_path.is_file():
            return f"存在: {path} (文件)"
        elif file_path.is_dir():
            return f"存在: {path} (目录)"
        else:
            return f"存在: {path} (其他类型)"
    except Exception as e:
        return f"错误: 检查路径失败: {e}"


@registry.register("list_tools", "列出当前可用工具")
def list_tools() -> str:
    """List available built-in and MCP tools."""
    lines = ["内置工具:"]
    for name, desc in registry.get_tool_descriptions():
        if desc:
            lines.append(f"- {name}: {desc}")
        else:
            lines.append(f"- {name}")

    lines.extend(registry.format_mcp_tools())
    return "\n".join(lines)
