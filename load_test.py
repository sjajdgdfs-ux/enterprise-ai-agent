import asyncio
import time
import aiohttp

# Target Live Streamlit App URL
URL = "https://enterprise-ai-agent-x54egp6faq6wtdgsaccxo8.streamlit.app/"

# Load Test Parameters
TOTAL_REQUESTS = 30  # إجمالي عدد الطلبات
CONCURRENCY = 10     # عدد المستخدمين المتزامنين في نفس اللحظة

async def send_request(session, request_id, results, semaphore):
    async with semaphore:
        start_time = time.time()
        try:
            async with session.get(URL, timeout=15) as response:
                latency = round((time.time() - start_time) * 1000, 2)
                status = response.status
                success = (status == 200)
                results.append({"id": request_id, "status": status, "latency_ms": latency, "success": success})
                print(f"➡️ Request #{request_id:02d} -> Status: {status} | Latency: {latency} ms")
        except Exception as e:
            latency = round((time.time() - start_time) * 1000, 2)
            results.append({"id": request_id, "status": "ERROR", "latency_ms": latency, "success": False})
            print(f"❌ Request #{request_id:02d} -> Failed: {str(e)}")

async def main():
    print(f"🚀 Starting Python Stress Test on Live App:\n   {URL}\n")
    print(f"📊 Config: {TOTAL_REQUESTS} Total Requests | {CONCURRENCY} Concurrent Users\n" + "-"*55)
    
    results = []
    semaphore = asyncio.Semaphore(CONCURRENCY)
    
    start_total = time.time()
    async with aiohttp.ClientSession() as session:
        tasks = [send_request(session, i + 1, results, semaphore) for i in range(TOTAL_REQUESTS)]
        await asyncio.gather(*tasks)
        
    total_time = round(time.time() - start_total, 2)
    
    # Analyze Statistics
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    latencies = [r["latency_ms"] for r in results if r["latency_ms"] > 0]
    avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0
    rps = round(len(results) / total_time, 2)

    print("\n" + "="*55)
    print("📈 LOAD TEST PERFORMANCE REPORT")
    print("="*55)
    print(f"✅ Successful Responses (200 OK): {len(successful)} / {TOTAL_REQUESTS}")
    print(f"❌ Failed Requests:               {len(failed)}")
    print(f"⏱️ Total Execution Duration:     {total_time} seconds")
    print(f"🚀 Throughput (RPS):             {rps} Requests/sec")
    print(f"⚡ Average Latency:              {avg_latency} ms")
    print("="*55)

if __name__ == "__main__":
    asyncio.run(main())