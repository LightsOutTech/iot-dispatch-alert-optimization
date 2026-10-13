import argparse
import csv
import sys
from datetime import datetime
from solution import parse_iso, is_flagged_s3

def evaluate_single(plant, category, signal, retry, drift_min):
    row = {
        'plant_code': plant,
        'device_category': category,
        'signal_dbm': float(signal),
        'retry_count': float(retry),
        'drift_min': float(drift_min)
    }
    defer = is_flagged_s3(row)
    action = 'DEFER_VERIFY (暂缓复核)' if defer else 'DIRECT_DISPATCH (立即派单)'
    reasons = []
    if plant == '一号总装厂':
        if row['drift_min'] >= 15.0:
            reasons.append(f"时钟漂移偏高: {row['drift_min']:.1f}min >= 15min")
        if row['signal_dbm'] <= 3.0 and row['retry_count'] >= 25.0:
            reasons.append(f"一号总装厂弱信号特征: 信号={row['signal_dbm']:.1f}dBm <= 3dBm, 重传={row['retry_count']:.1f} >= 25")
    else:
        if row['drift_min'] >= 15.0:
            reasons.append(f"时钟漂移偏高: {row['drift_min']:.1f}min >= 15min")
        if row['signal_dbm'] <= 5.0 and row['retry_count'] >= 70.0:
            reasons.append(f"弱信号与重传耦合: 信号={row['signal_dbm']:.1f}dBm, 重传={row['retry_count']:.1f}")
    
    reason_str = '; '.join(reasons) if reasons else '设备状态正常，通信信道良好'
    return action, reason_str

def main():
    parser = argparse.ArgumentParser(description='工业物联网告警派单分流决策工具 (IoT Dispatch Triage CLI)')
    subparsers = parser.add_subparsers(dest='command', help='子命令')

    eval_parser = subparsers.add_parser('evaluate', help='单条告警实时评估')
    eval_parser.add_argument('--plant', required=True, help='厂区名称')
    eval_parser.add_argument('--category', required=True, help='设备类别')
    eval_parser.add_argument('--signal', type=float, required=True, help='信号接收强度 (dBm)')
    eval_parser.add_argument('--retry', type=float, required=True, help='重传次数')
    eval_parser.add_argument('--drift', type=float, required=True, help='时钟漂移/延迟 (分钟)')

    batch_parser = subparsers.add_parser('batch', help='批量告警数据清洗分流')
    batch_parser.add_argument('--input', required=True, help='输入 CSV 路径')
    batch_parser.add_argument('--output', required=True, help='输出 CSV 路径')

    args = parser.parse_args()

    if args.command == 'evaluate':
        action, reason = evaluate_single(args.plant, args.category, args.signal, args.retry, args.drift)
        print(f"\n[决策结果]: {action}")
        print(f"[决策归因]: {reason}\n")
    elif args.command == 'batch':
        with open(args.input, 'r', encoding='utf-8') as fin, open(args.output, 'w', newline='', encoding='utf-8') as fout:
            reader = csv.DictReader(fin)
            fieldnames = reader.fieldnames + ['recommended_action', 'decision_reason']
            writer = csv.DictWriter(fout, fieldnames=fieldnames)
            writer.writeheader()
            cnt = 0
            for r in reader:
                te = parse_iso(r['event_ts']).timestamp()
                ts = parse_iso(r['synced_ts']).timestamp()
                drift_min = (te - ts) / 60.0
                action, reason = evaluate_single(r['plant_code'], r['device_category'], r['signal_dbm'], r['retry_count'], drift_min)
                r['recommended_action'] = action
                r['decision_reason'] = reason
                writer.writerow(r)
                cnt += 1
        print(f"批量处理完成: 共处理 {cnt} 条告警，输出至 {args.output}")
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
