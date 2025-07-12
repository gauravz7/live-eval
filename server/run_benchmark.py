import subprocess
import time
import json
import os

def run_command(command, env=None):
    """Runs a command and waits for it to complete."""
    print(f"Running command: {command}")
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print(f"Error running command: {command}")
        print(stderr.decode())
    return stdout.decode()

def main():
    """Main function to run the benchmark."""
    tool_sizes = [5, 10, 15, 20, 25, 30]
    models = ['gemini-live-2.5-flash-preview-native-audio', 'gemini-live-2.5-flash']
    results = {}

    for size in tool_sizes:
        print(f"\n--- Testing with {size} tools ---")

        # Step 1: Generate tools
        run_command(f"python3 live-eval/server/generate_tool_data.py --num_tools {size}")

        # Step 2: Generate eval data
        run_command("python3 live-eval/server/generate_eval_data.py")

        for model in models:
            print(f"\n--- Testing with model: {model} ---")
            if model not in results:
                results[model] = {}

            # Step 3: Start server
            env = os.environ.copy()
            env["MODEL"] = model
            server_process = subprocess.Popen(["python3", "live-eval/server/server_eval.py", "--no-save-audio"], env=env)
            time.sleep(5)  # Give the server time to start

            # Step 4: Run test
            output = run_command("python3 live-eval/server/run_test.py")

            # Kill the server process
            server_process.kill()

            # Extract accuracy from the output
            for line in output.splitlines():
                if "Accuracy:" in line:
                    accuracy = float(line.split(":")[1].strip().replace("%", ""))
                    results[model][size] = accuracy
                    print(f"Accuracy for {size} tools with model {model}: {accuracy}%")
                    break

    print("\n--- Benchmark Results ---")
    for model, model_results in results.items():
        print(f"\nModel: {model}")
        for size, accuracy in model_results.items():
            print(f"Tools: {size}, Accuracy: {accuracy}%")

    # Save results to a file
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"benchmark_results_{timestamp}.json"
    with open(filename, "w") as f:
        json.dump(results, f, indent=4)
    print(f"\nBenchmark results saved to {filename}")

if __name__ == "__main__":
    main()
