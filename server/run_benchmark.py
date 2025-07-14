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
    tool_sizes = [20]
    #tool_sizes = [1,2]
    models = ['gemini-live-2.5-flash-preview-native-audio', 'gemini-live-2.5-flash','gemini-2.0-flash-live-preview-04-09']
    results = {}

    for model in models:
        results[model] = {}

    for size in tool_sizes:
        print(f"\n--- Testing with {size} tools ---")

        # Step 1: Generate tools
        run_command(f"python3 generate_tool_data.py --num_tools {size}")

        # Step 2: Generate eval data
        run_command("python3 generate_eval_data.py")

        for model in models:
            print(f"\n--- Testing with model: {model} ---")
            if size not in results[model]:
                results[model][size] = {}

            # Step 3: Start server
            server_process = subprocess.Popen(["python3", "server_eval.py", "--no-save-audio", "--model", model])
            time.sleep(5)  # Give the server time to start

            # Step 4: Run test
            output = run_command("python3 run_test.py")

            # Kill the server process
            server_process.kill()

            # Extract accuracy from the output
            tool_accuracy = None
            param_accuracy = None
            for line in output.splitlines():
                if "Tool Call Accuracy:" in line:
                    tool_accuracy = float(line.split(":")[1].strip().replace("%", ""))
                if "Tool & Parameter Accuracy:" in line:
                    param_accuracy = float(line.split(":")[1].strip().replace("%", ""))

            if tool_accuracy is not None and param_accuracy is not None:
                results[model][size] = {
                    "tool_accuracy": tool_accuracy,
                    "param_accuracy": param_accuracy
                }
                print(f"Tool Accuracy for {size} tools with model {model}: {tool_accuracy}%")
                print(f"Tool & Param Accuracy for {size} tools with model {model}: {param_accuracy}%")
            else:
                print(f"Could not parse accuracy for {size} tools with model {model}")


    print("\n--- Benchmark Results ---")
    for model, model_results in results.items():
        print(f"\nModel: {model}")
        for size, acc_results in model_results.items():
            print(f"  Tools: {size}, Tool Accuracy: {acc_results.get('tool_accuracy')}%, Tool & Param Accuracy: {acc_results.get('param_accuracy')}%")

    # Save results to a file
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"benchmark_results_{timestamp}.json"
    with open(filename, "w") as f:
        json.dump(results, f, indent=4)
    print(f"\nBenchmark results saved to {filename}")

if __name__ == "__main__":
    main()
