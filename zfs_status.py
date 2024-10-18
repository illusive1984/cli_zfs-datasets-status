import subprocess
from rich.console import Console
from rich.table import Table

def get_zfs_data():
    cmd = ["zfs", "get", "-t", "filesystem,volume", "-Hp", "name,quota,used,avail,mountpoint,type"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip().split('\n')

def parse_zfs_data(data):
    parsed_data = {}
    for line in data:
        parts = line.split('\t')
        if len(parts) != 4:
            continue
        dataset, property_name, value, _ = parts
        if dataset not in parsed_data:
            parsed_data[dataset] = {}
        if property_name in ["quota", "used", "avail"]:
            try:
                parsed_data[dataset][property_name] = int(value)
            except ValueError:
                parsed_data[dataset][property_name] = 0
        else:
            parsed_data[dataset][property_name] = value
    return parsed_data

def bytes_to_gb(bytes_value):
    return round(bytes_value / (1024 ** 3), 2)

def create_table(data):
    table = Table(title="ZFS Dataset Information")
    table.add_column("Name", style="cyan")
    table.add_column("Quota (GB)", justify="right", style="magenta")
    table.add_column("Used (GB)", justify="right", style="green")
    table.add_column("Available (GB)", justify="right", style="yellow")
    table.add_column("Mountpoint", style="blue")
    table.add_column("Type", style="red")

    for name, properties in data.items():
        table.add_row(
            name,
            str(bytes_to_gb(properties.get("quota", 0))) if properties.get("quota", 0) != 0 else "Unlimited",
            str(bytes_to_gb(properties.get("used", 0))),
            str(bytes_to_gb(properties.get("avail", 0))),
            properties.get("mountpoint", "-"),
            properties.get("type", "-")
        )

    return table

def create_summary_table(data):
    summary_data = {
        "ROOT": data.get("rpool/ROOT", {}),
        "data": data.get("rpool/data", {}),
        "var-lib-vz": data.get("rpool/var-lib-vz", {})
    }

    table = Table(title="ZFS Dataset Summary")
    table.add_column("Dataset Group", style="cyan")
    table.add_column("Used (GB)", justify="right", style="green")
    table.add_column("Available (GB)", justify="right", style="yellow")

    for group, properties in summary_data.items():
        table.add_row(
            group,
            str(bytes_to_gb(properties.get("used", 0))),
            str(bytes_to_gb(properties.get("avail", 0)))
        )

    return table

def main():
    raw_data = get_zfs_data()
    parsed_data = parse_zfs_data(raw_data)
    
    console = Console()
    
    detail_table = create_table(parsed_data)
    console.print(detail_table)
    
    console.print()  # Add a blank line for separation
    
    summary_table = create_summary_table(parsed_data)
    console.print(summary_table)

if __name__ == "__main__":
    main()

