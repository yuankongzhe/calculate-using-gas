import datetime
from web3 import Web3
import multiprocessing

def connect_to_rpc(rpc_url):
    """连接到RPC节点"""
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    return w3

def calculate_block_range(w3, start_timestamp, end_timestamp):
    """计算开始和结束区块高度"""
    latest_block = w3.eth.get_block('latest')
    latest_block_number = latest_block.number
    previous_block = w3.eth.get_block(latest_block_number - 1000)
    previous_block_timestamp = previous_block.timestamp
    avg_block_time = (latest_block.timestamp - previous_block_timestamp) / 1000

    cal_start_block = latest_block_number - int((latest_block.timestamp - start_timestamp) / avg_block_time)
    cal_end_block = latest_block_number - int((latest_block.timestamp - end_timestamp) / avg_block_time)

    for _ in range(100):
        cal_start_block_time = w3.eth.get_block(cal_start_block).timestamp
        if abs(cal_start_block_time - start_timestamp) < 1000:
            start_block = cal_start_block
            break
        cal_start_block = cal_start_block + int((start_timestamp - cal_start_block_time) / avg_block_time)

    for _ in range(100):
        cal_end_block_time = w3.eth.get_block(cal_end_block).timestamp
        if abs(end_timestamp - cal_end_block_time) < 1000:
            end_block = cal_end_block
            break
        cal_end_block = cal_end_block + int((end_timestamp - cal_end_block_time) / avg_block_time)

    return start_block, end_block

def calculate_gas_used_for_block_range(rpc_url, start_block, end_block):
    """计算给定区块范围内的总gas消耗"""
    w3 = connect_to_rpc(rpc_url)  # 在这里创建新的Web3实例
    total_gas_used = 0
    for block_number in range(start_block, end_block + 1):
        # print(f"Processing block {block_number}")
        block = w3.eth.get_block(block_number, full_transactions=True)
        gas_used_in_block = block.gasUsed
        gas_prices = [tx.gasPrice for tx in block.transactions]
        total_gas_used += w3.from_wei(max(gas_prices), 'ether') * gas_used_in_block
    return total_gas_used

def main():
    rpc_url = "https://dev-rpc.zkfair.io"
    start_timestamp = int(datetime.datetime(2024, 4, 2, 0).timestamp())
    end_timestamp = int(datetime.datetime(2024, 4, 3, 0).timestamp())
    w3 = connect_to_rpc(rpc_url)  # 仍然需要一个Web3实例来计算区块范围
    start_block, end_block = calculate_block_range(w3, start_timestamp, end_timestamp)
    print(f"开始区块: {start_block}, 结束区块: {end_block}")
    # 将区块范围划分为多个子范围
    num_processes = 10
    block_ranges = []
    block_range_size = (end_block - start_block + 1) // num_processes
    for i in range(num_processes):
        start = start_block + i * block_range_size
        end = start + block_range_size - 1
        if i == num_processes - 1:
            end = end_block
        block_ranges.append((start, end))

    # 使用多进程计算每个子范围的gas消耗
    pool = multiprocessing.Pool(processes=num_processes)
    results = [pool.apply_async(calculate_gas_used_for_block_range, args=(rpc_url, start, end)) for start, end in block_ranges]
    pool.close()
    pool.join()

    # 汇总所有子范围的gas消耗
    total_gas_used = sum(result.get() for result in results)

    print(f"从 {datetime.datetime.fromtimestamp(start_timestamp)} 到 {datetime.datetime.fromtimestamp(end_timestamp)}")
    print(f"总gas消耗: {total_gas_used}")

if __name__ == "__main__":
    main()