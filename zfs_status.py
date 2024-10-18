"""Get status information about your ZFS datasets"""
import subprocess

from rich.console import Console
from rich.table import Table


def get_zfs_data():
    """
    Execute the ZFS command to retrieve dataset information.

    Returns:
        list: A list of strings, each representing a line of ZFS command output.
    """
    cmd = ["zfs", "get", "-t", "filesystem,volume", "-Hp", "name,quota,used,avail,mountpoint,type"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return result.stdout.strip().split('\n')


def parse_zfs_data(data):
    """
    Parse the raw ZFS command output into a structured format.

    Args:
        data (list): A list of strings, each representing a line of ZFS command output.

    Returns:
        dict: A dictionary where
            keys are dataset names and values are dictionaries of dataset properties.
    """
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
    """
    Convert bytes to gigabytes.

    Args:
        bytes_value (int): The value in bytes to convert.

    Returns:
        float: The value converted to gigabytes, rounded to two decimal places.
    """
    return round(bytes_value / (1024 ** 3), 2)


def create_table(data):
    """
    Create a Rich table with detailed ZFS dataset information.

    Args:
        data (dict): A dictionary of parsed ZFS dataset information.

    Returns:
        rich.table.Table: A Rich table object containing the detailed dataset information.
    """
    table = Table(title="ZFS Dataset Information")
    table.add_column("Name", style="cyan")
    table.add_column("Quota (GB)", justify="right", style="magenta")
    table.add_column("Used (GB)", justify="right", style="green")
    table.add_column("Available (GB)", justify="right", style="yellow")
    table.add_column("Mountpoint", style="blue")
    table.add_column("Type", style="red")

    for name, props in data.items():
        table.add_row(
            name,
            str(bytes_to_gb(props.get("quota", 0))) if props.get("quota", 0) != 0 else "Unlimited",
            str(bytes_to_gb(props.get("used", 0))),
            str(bytes_to_gb(props.get("avail", 0))),
            props.get("mountpoint", "-"),
            props.get("type", "-")
        )

    return table


def create_summary_table(data) -> Table:
    """
    Create a Rich table with summarized ZFS dataset information for main dataset groups.

    Args:
        data (dict): A dictionary of parsed ZFS dataset information.

    Returns:
        rich.table.Table: A Rich table object containing the summarized dataset information.
    """
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
    """
    Main function to execute the ZFS dataset information retrieval and display process.
    """
    raw_data = get_zfs_data()
    parsed_data = parse_zfs_data(raw_data)

    console = Console()
    detail_table = create_table(parsed_data)
    console.print(detail_table)
    console.print()
    summary_table = create_summary_table(parsed_data)
    console.print(summary_table)


if __name__ == "__main__":
    main()
