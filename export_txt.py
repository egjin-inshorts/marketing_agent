# export_txt.py
import argparse
from datetime import datetime
from difflib import unified_diff

from core.commons import load_config, get_research_history_path, load_research


def export_version(research_id: str, version: int, research_history_path, output_path: str = None) -> str:
    """Export a specific version to TXT."""
    data = load_research(research_id, research_history_path)
    versions = data.get("versions", [])

    if version < 1 or version > len(versions):
        raise ValueError(f"Version {version} not found. Available: 1-{len(versions)}")

    v = versions[version - 1]

    content = f"""{'='*80}
Research ID: {research_id}
Version: {v['version']}
Timestamp: {v['timestamp']}
Query: {v['query']}
{'='*80}

{v['findings']}

{'='*80}
Sources: {', '.join(v.get('sources', []))}
Delta: {v.get('delta', 'N/A')}
{'='*80}
"""

    if output_path is None:
        output_path = f"{research_id}_v{version}.txt"

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return output_path


def export_diff(research_id: str, v1: int, v2: int, research_history_path, output_path: str = None) -> str:
    """Export diff between two versions to TXT."""
    data = load_research(research_id, research_history_path)
    versions = data.get("versions", [])
    max_v = len(versions)

    if v1 < 1 or v1 > max_v or v2 < 1 or v2 > max_v:
        raise ValueError(f"Invalid version. Available: 1-{max_v}")

    ver1 = versions[v1 - 1]
    ver2 = versions[v2 - 1]

    findings1 = ver1['findings']
    findings2 = ver2['findings']

    # Generate unified diff
    diff_lines = list(unified_diff(
        findings1.splitlines(keepends=True),
        findings2.splitlines(keepends=True),
        fromfile=f"Version {v1} ({ver1['timestamp']})",
        tofile=f"Version {v2} ({ver2['timestamp']})",
        lineterm=''
    ))

    # Count changes
    added = sum(1 for line in diff_lines if line.startswith('+') and not line.startswith('+++'))
    removed = sum(1 for line in diff_lines if line.startswith('-') and not line.startswith('---'))

    content = f"""{'='*80}
DIFF REPORT
Research ID: {research_id}
Comparison: Version {v1} → Version {v2}
Generated: {datetime.now().isoformat()}
{'='*80}

[Version {v1}]
  Timestamp: {ver1['timestamp']}
  Query: {ver1['query']}

[Version {v2}]
  Timestamp: {ver2['timestamp']}
  Query: {ver2['query']}

{'='*80}
SUMMARY
{'='*80}
  Lines added:   +{added}
  Lines removed: -{removed}

{'='*80}
UNIFIED DIFF
{'='*80}
"""

    content += ''.join(diff_lines)

    # Add side-by-side summary
    content += f"""

{'='*80}
VERSION {v1} FULL TEXT
{'='*80}
{findings1}

{'='*80}
VERSION {v2} FULL TEXT
{'='*80}
{findings2}
"""

    if output_path is None:
        output_path = f"{research_id}_diff_v{v1}_v{v2}.txt"

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return output_path


def list_versions(research_id: str, research_history_path):
    """List all versions for a research ID."""
    data = load_research(research_id, research_history_path)
    versions = data.get("versions", [])

    print(f"\nResearch ID: {research_id}")
    print(f"Total versions: {len(versions)}\n")
    print(f"{'Ver':<5} {'Timestamp':<25} {'Query':<40}")
    print("-" * 70)

    for v in versions:
        query_short = v['query'][:37] + "..." if len(v['query']) > 40 else v['query']
        print(f"{v['version']:<5} {v['timestamp'][:19]:<25} {query_short:<40}")


def main():
    parser = argparse.ArgumentParser(description="Export research versions to TXT")
    parser.add_argument("--mode", choices=["version", "diff", "list"], required=True,
                        help="version: export single version, diff: export diff, list: show versions")
    parser.add_argument("--id", required=True, help="Research ID")
    parser.add_argument("--version", "-v", type=int, help="Version number (for version mode)")
    parser.add_argument("--old", dest="old_ver", type=int, help="Source version (for diff mode)")
    parser.add_argument("--new", dest="new_ver", type=int, help="Target version (for diff mode)")
    parser.add_argument("--output", "-o", help="Output file path (optional)")
    parser.add_argument("--config", "-c", default="config.yaml", help="Config file path (default: config.yaml)")

    args = parser.parse_args()

    # Load config and get research history path
    config = load_config(args.config)
    research_history_path = get_research_history_path(config)

    try:
        if args.mode == "list":
            list_versions(args.id, research_history_path)

        elif args.mode == "version":
            if not args.version:
                parser.error("--version required for version mode")
            output = export_version(args.id, args.version, research_history_path, args.output)
            print(f"✓ Exported to: {output}")

        elif args.mode == "diff":
            if not args.old_ver or not args.new_ver:
                parser.error("--old and --new required for diff mode")
            output = export_diff(args.id, args.old_ver, args.new_ver, research_history_path, args.output)
            print(f"✓ Exported to: {output}")

    except FileNotFoundError as e:
        print(f"Error: {e}")
    except ValueError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
