import json
from pathlib import Path

def display_traces(log_file="capstone_traces.jsonl"):
    path = Path(log_file)
    if not path.exists():
        print(f"No traces file found at {log_file}. Run some queries first!")
        return

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    print("\n" + "=" * 70)
    print(f" 📊 CAPSTONE AGENT OBSERVABILITY REPORT ({len(lines)} Traces Found)")
    print("=" * 70)

    for i, line in enumerate(lines, 1):
        try:
            trace = json.loads(line)
            print(f"\n🔍 TRACE #{i} | ID: {trace.get('trace_id')} | Agent: {trace.get('agent')}")
            print(f"  📥 User Input:   {trace.get('input')}")
            print(f"  ⏱️ Total Duration: {trace.get('total_duration')}s")
            print(f"  🚦 Status:         {trace.get('status')}")
            print("  🪜 Steps Executed:")

            for step in trace.get("steps", []):
                print(f"     └─ Step {step['step_number']}: [{step['name']}] ({step['duration_seconds']}s)")
                print(f"        Output snippet: {str(step['output'])[:120]}...")

            print("-" * 70)
        except Exception as e:
            print(f"Error parsing trace line #{i}: {e}")

if __name__ == "__main__":
    display_traces()