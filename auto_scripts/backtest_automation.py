import subprocess
import os

# Define the output directory
output_dir = os.path.join('', 'auto_outputs')

# Ensure the output directory exists
os.makedirs(output_dir, exist_ok=True)

commands = [
    f'docker compose run --rm freqtrade backtesting --config user_data/config.json --strategy MeanReversionStrategy --timerange 20230101-20240501 -i {i}' for i in ['1m', '5m', '15m', '1h']
]

output = {}

for idx, command in enumerate(commands, start=1):
    print(f"Running command {idx} of {len(commands)}")
    result = subprocess.run(command, shell=True,
                            capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Command {idx} completed successfully")
        output[command] = result.stdout
    else:
        print(f"Command {idx} failed with error:\n{result.stderr}")
        output[command] = result.stderr

# Define the output file path
output_file_path = os.path.join(output_dir, 'output.txt')

# Write the output to the file
with open(output_file_path, 'w') as f:
    for command, command_output in output.items():
        f.write(f"Command: {command}\n")
        f.write(f"Output:\n{command_output}\n")
        f.write("=" * 80 + "\n")

print(f"Output written to {output_file_path}")
