import json
import time
from datetime import datetime
from pathlib import Path

class AgentTracer:
    def __init__(self, log_file="capstone_traces.jsonl"):
        self.log_file = Path(log_file)
        self.current_trace = None

    def start_trace(self, user_input, agent_name="capstone_agent"):
        self.current_trace = {
            "trace_id": f"trace_{int(time.time() * 1000)}",
            "agent": agent_name,
            "input": user_input,
            "steps": [],
            "start_time": datetime.now().isoformat(),
            "status": "running"
        }
        return self.current_trace["trace_id"]

    def log_step(self, step_name, input_data, output_data, duration=None):
        if self.current_trace is None:
            return

        step = {
            "step_number": len(self.current_trace["steps"]) + 1,
            "name": step_name,
            "input": str(input_data)[:500],
            "output": str(output_data)[:500],
            "duration_seconds": duration,
            "timestamp": datetime.now().isoformat()
        }
        self.current_trace["steps"].append(step)

    def end_trace(self, final_output, status="success"):
        if self.current_trace is None:
            return

        self.current_trace["end_time"] = datetime.now().isoformat()
        self.current_trace["output"] = str(final_output)[:1000]
        self.current_trace["status"] = status
        
        start_dt = datetime.fromisoformat(self.current_trace["start_time"])
        end_dt = datetime.fromisoformat(self.current_trace["end_time"])
        self.current_trace["total_duration"] = round((end_dt - start_dt).total_seconds(), 2)

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(self.current_trace, ensure_ascii=False) + "\n")

        self.current_trace = None