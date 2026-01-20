# cli.py
import json
import sys
import argparse
from pathlib import Path
from core.agent import MarketingResearchAgent
from core.commons import InvalidResearchIdError


def list_versions(file_path: str) -> None:
    """List all versions in a research history JSON file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    versions = data.get("versions", [])
    research_id = path.stem

    print(f"\nFile: {file_path}")
    print(f"Research ID: {research_id}")
    print(f"Total versions: {len(versions)}\n")
    print(f"{'Ver':<5} {'Timestamp':<25} {'Query':<40}")
    print("-" * 70)

    for v in versions:
        query_short = v['query'][:37] + "..." if len(v['query']) > 40 else v['query']
        print(f"{v['version']:<5} {v['timestamp'][:19]:<25} {query_short:<40}")


def validate_args(args) -> bool:
    """Validate CLI arguments based on mode.

    Returns:
        True if validation passes, exits with error message otherwise.
    """
    if args.mode == "ingest":
        if not args.docs:
            print("Error: --docs is required for ingest mode", file=sys.stderr)
            return False
    elif args.mode in ["research", "update"]:
        if not args.query:
            print("Error: --query is required for research/update mode", file=sys.stderr)
            return False
        if not args.id:
            print("Error: --id is required for research/update mode", file=sys.stderr)
            return False
    elif args.mode == "diff":
        if not args.id:
            print("Error: --id is required for diff mode", file=sys.stderr)
            return False
        if args.old_ver is None or args.new_ver is None:
            print("Error: --old and --new are required for diff mode", file=sys.stderr)
            return False
        if args.old_ver < 1 or args.new_ver < 1:
            print("Error: Version numbers must be >= 1", file=sys.stderr)
            return False
    elif args.mode == "list":
        if not args.file:
            print("Error: --file is required for list mode", file=sys.stderr)
            return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Marketing Research Agent CLI")
    parser.add_argument("--mode", choices=["ingest", "research", "update", "diff", "list"], required=True)
    parser.add_argument("--docs", nargs="+", help="문서 경로 (ingest 모드)")
    parser.add_argument("--query", help="리서치 질문")
    parser.add_argument("--id", help="리서치 ID")
    parser.add_argument("--old", dest="old_ver", type=int, help="비교 소스 버전 (diff 모드)")
    parser.add_argument("--new", dest="new_ver", type=int, help="비교 대상 버전 (diff 모드)")
    parser.add_argument("--file", help="리서치 히스토리 JSON 파일 경로 (list 모드)")

    args = parser.parse_args()

    if not validate_args(args):
        sys.exit(1)

    # Handle list mode separately (doesn't require agent initialization)
    if args.mode == "list":
        try:
            list_versions(args.file)
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON file: {e}", file=sys.stderr)
            sys.exit(1)
        return

    try:
        agent = MarketingResearchAgent()
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error initializing agent: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        if args.mode == "ingest":
            agent.ingest_documents(args.docs)
            print(f"✓ {len(args.docs)}개 문서 추가 완료")

        elif args.mode in ["research", "update"]:
            result = agent.research(
                query=args.query,
                research_id=args.id,
                update_mode=(args.mode == "update")
            )
            print(f"\n{'='*80}\n리서치 결과 (ID: {args.id})\n{'='*80}")
            print(result["findings"])
            print(f"\n저장 위치: ./research_history/{args.id}.json")

        elif args.mode == "diff":
            agent.show_diff(args.id, args.old_ver, args.new_ver)

    except InvalidResearchIdError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
