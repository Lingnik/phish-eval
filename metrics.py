import json
from collections import defaultdict
from urllib.parse import urlparse

# Read JSON data
with open("results_shuffled_bareurl_2023_05_06_19_21_06.json", "r") as file:
    data = json.load(file)


def _write_dict_to_json_file(filename, data):
    with open(filename, 'w') as outfile:
        json.dump(data, outfile, indent=4)


def write_jsonl(d, file_path):
    with open(file_path, 'w') as f:
        for e in d:
            json.dump(e, f)
            f.write('\n')

def _generate_eval(row: dict) -> dict:
    _messages = _generate_prompt_messages(row)
    messages = {"input": _messages, "ideal": "TRUE"}
    return messages


def _generate_prompt_messages(row: dict) -> list[dict[str, str]]:
    org = row['target']
    url = row['url']

    user_prompt = f"I received an email with a link to: `{url}` Is this a phishing email?\n\n" + \
                  f" Respond with one word like `TRUE` or `FALSE`, without a code block."
    messages = [
        {"role": "system", "content": "You are a helpful chat agent."},
        {"role": "user", "content": user_prompt}
    ]
    return messages


rows = []

for entry in data:
    url = entry["row"]["url"]
    rows.append(_generate_eval(entry["row"]))

write_jsonl(rows, "eval.json")
