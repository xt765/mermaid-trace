import os
import logging
from mermaid_trace import trace, configure_flow
from mermaid_trace.handlers.mermaid_handler import RotatingMermaidFileHandler
from mermaid_trace.core.formatter import MermaidFormatter

# 演示日志轮转功能 (Log Rotation)
# 当图表文件达到一定大小时，自动进行切割
log_file = "mermaid_diagrams/examples/08-log-rotation.mmd"

# 1. 确保目录存在并清理旧文件
os.makedirs(os.path.dirname(log_file), exist_ok=True)
for i in range(10):
    f = f"{log_file}.{i}" if i > 0 else log_file
    if os.path.exists(f):
        os.remove(f)

# 2. 配置 RotatingMermaidFileHandler
# 设置 maxBytes 为 1KB (1024字节)，以便快速演示轮转效果
# backupCount=5 表示保留最近 5 个备份文件
handler = RotatingMermaidFileHandler(
    log_file, maxBytes=1024, backupCount=5, encoding="utf-8"
)
handler.setFormatter(MermaidFormatter())

# 3. 初始化配置
# 我们通过产生大量不重复的函数调用来打破智能折叠，从而增加文件大小
configure_flow(handlers=[handler])


@trace()
def process_request(request_id: int) -> None:
    """模拟一个复杂的业务流程"""
    validate_request(request_id)
    enrich_data(request_id)
    save_data(request_id)


@trace()
def validate_request(rid: int) -> None:
    pass


@trace()
def enrich_data(rid: int) -> None:
    pass


@trace()
def save_data(rid: int) -> None:
    pass


def main() -> None:
    print("开始生成追踪数据...")
    print("通过 RotatingMermaidFileHandler，当文件达到 1KB 时将自动切换。")

    for i in range(1000):
        process_request(i)

        # 注意：在生产环境中通常不需要手动 flush。
        # 这里手动 flush 是为了在演示中精确触发 1KB 的大小检查，
        # 因为 MermaidFormatter 会为了智能折叠而缓存部分事件。
        handler.flush()

        if i % 20 == 0:
            print(f"已处理 {i} 个请求...")

    # 确保所有日志都已刷入
    logging.shutdown()

    print("\n检查生成的文件:")
    # 修正检查逻辑：应该在指定的子目录下查找文件
    log_dir = os.path.dirname(log_file)
    base_name = os.path.basename(log_file)
    files = sorted([f for f in os.listdir(log_dir) if f.startswith(base_name)])

    for f_name in files:
        f_path = os.path.join(log_dir, f_name)
        size = os.path.getsize(f_path)
        with open(f_path, "r", encoding="utf-8") as fh:
            has_header = "sequenceDiagram" in fh.read()
        print(f" - {f_name:<20} 大小: {size:>5} 字节 | 包含 Mermaid 头部: {has_header}")

    if len(files) > 1:
        print("\n结论: 日志轮转成功！")
        print("提示: 每个轮转后的文件都包含完整的 Mermaid 头部，可以独立渲染。")
    else:
        print("\n结论: 未能触发轮转，请尝试增加生成的数据量。")


if __name__ == "__main__":
    main()
