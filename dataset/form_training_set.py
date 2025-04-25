import json
import random

# Splits the output training data into training and validation at an 80/20 split.
def split_validation_data(input_file, output_file, num_lines):
    # Read all lines into memory
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if num_lines > len(lines):
        raise ValueError(f"Requested {num_lines} lines, but the file only contains {len(lines)} lines.")

    # Select x unique indices randomly
    selected_indices = set(random.sample(range(len(lines)), num_lines))

    validation_lines = []
    remaining_lines = []

    # Split the lines
    for idx, line in enumerate(lines):
        if idx in selected_indices:
            validation_lines.append(line)
        else:
            remaining_lines.append(line)

    # Write validation lines to new file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(validation_lines)

    # Overwrite the original file with remaining lines
    with open(input_file, 'w', encoding='utf-8') as f:
        f.writelines(remaining_lines)

    print(f"{num_lines} lines moved to {output_file} and removed from {input_file}.")

# Example usage
split_validation_data('training_data_gemini2-v4.jsonl', 'training_data_gemini2-v4-validate.jsonl', 660)