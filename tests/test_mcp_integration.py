"""Test MCP integration functionality."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from extensions.mcp.manager import MCPManager


async def test_mcp_manager_load_config():
    """Test loading MCP configuration."""
    print("=" * 50)
    print("测试 1: 加载 MCP 配置")
    print("=" * 50)

    config_path = Path(__file__).parent / "test_mcp.json"
    manager = MCPManager(str(config_path))

    result = manager.load_config()
    assert result is True, "配置加载失败"
    print(f"✓ 配置加载成功")

    configs = manager.get_server_configs()
    assert len(configs) == 1, f"期望 1 个服务器配置，实际得到 {len(configs)}"
    print(f"✓ 找到 {len(configs)} 个服务器配置")

    server_names = manager.get_enabled_server_names()
    assert "Filesystem MCP" in server_names, "未找到 Filesystem MCP"
    print(f"✓ 已启用的服务器: {server_names}")

    print()
    return True


async def test_mcp_manager_missing_config():
    """Test handling of missing config file."""
    print("=" * 50)
    print("测试 2: 处理缺失的配置文件")
    print("=" * 50)

    manager = MCPManager("nonexistent.json")
    result = manager.load_config()
    assert result is False, "应该返回 False"
    print(f"✓ 正确处理缺失的配置文件")

    print()
    return True


async def test_mcp_server_initialization():
    """Test MCP server initialization and cleanup."""
    print("=" * 50)
    print("测试 3: MCP 服务器初始化与清理")
    print("=" * 50)

    config_path = Path(__file__).parent / "test_mcp.json"
    manager = MCPManager(str(config_path))

    if not manager.load_config():
        print("✗ 配置加载失败")
        return False

    print("正在初始化 MCP 服务器 (可能需要下载依赖)...")

    try:
        servers = await manager.initialize_all_servers()
        print(f"✓ 成功初始化 {len(servers)} 个 MCP 服务器")

        if servers:
            server = servers[0]
            print(f"✓ 服务器名称: {server.name}")

            # Check if server has tools
            tools = await server.list_tools()
            print(f"✓ 服务器提供 {len(tools)} 个工具:")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description[:50]}..." if len(tool.description) > 50 else f"  - {tool.name}: {tool.description}")

        # Cleanup
        print("\n正在清理服务器...")
        await manager.cleanup_servers()
        print("✓ 服务器清理成功")

        print()
        return True

    except Exception as e:
        print(f"✗ 初始化失败: {e}")
        await manager.cleanup_servers()
        return False


async def test_disabled_server():
    """Test that disabled servers are not initialized."""
    print("=" * 50)
    print("测试 4: 禁用的服务器不应被初始化")
    print("=" * 50)

    # Create a temporary config with disabled server
    import json
    import tempfile

    config = {
        "mcpServers": [
            {
                "name": "Disabled Server",
                "type": "stdio",
                "enabled": False,
                "params": {
                    "command": "echo",
                    "args": ["test"]
                }
            }
        ]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config, f)
        temp_path = f.name

    try:
        manager = MCPManager(temp_path)
        manager.load_config()

        servers = await manager.initialize_all_servers()
        assert len(servers) == 0, f"期望 0 个服务器，实际得到 {len(servers)}"
        print("✓ 禁用的服务器未被初始化")

        print()
        return True
    finally:
        Path(temp_path).unlink()


async def main():
    """Run all tests."""
    print("\n" + "=" * 50)
    print("MCP 集成测试")
    print("=" * 50 + "\n")

    results = []

    # Run tests
    results.append(await test_mcp_manager_load_config())
    results.append(await test_mcp_manager_missing_config())
    results.append(await test_disabled_server())
    results.append(await test_mcp_server_initialization())

    # Summary
    print("=" * 50)
    print("测试结果汇总")
    print("=" * 50)

    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"✓ 全部通过: {passed}/{total}")
        return 0
    else:
        print(f"✗ 部分失败: {passed}/{total}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
