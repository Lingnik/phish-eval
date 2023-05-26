import os
import sys
import csv
import gzip
import io
import time
import json
import random

import requests
import openai
import dotenv


dotenv.load_dotenv()

#LOCAL_DATASET = "online_valid_2023_05_06_08_55_12.csv"
#LOCAL_DATASET = 'hand.csv'
LOCAL_DATASET = 'failed_results_shuffled_bareurl_2023_05_06_15_02_49.csv'

# CSV data looks like this:
# phish_id,url,phish_detail_url,submission_time,verified,verification_time,online,target
# 123456,https://www.example.com/,http://www.phishtank.com/phish_detail.php?phish_id=123456,2009-06-19T15:15:47+00:00,yes,2009-06-19T15:37:31+00:00,yes,1st National Example Bank
DATASET_SOURCE = 'https://data.phishtank.com/data/online-valid.csv.gz'


class PhishEval:

    def eval(self, download_latest: bool = False):
        path = LOCAL_DATASET
        if download_latest is True:
            path = self._download_latest_dataset()
        dataset = self._read_csv(path)

        random.shuffle(dataset)
        full_results_file = f"results_shuffled_bareurl_{time.strftime('%Y_%m_%d_%H_%M_%S')}.json"
        failed_results_file = f"failed_results_shuffled_bareurl_{time.strftime('%Y_%m_%d_%H_%M_%S')}.json"
        results = []
        failed_results = []
        for i, row in enumerate(dataset):
            prompt = self._generate_prompt(row)
            response = self._gpt_generate(prompt)
            if not response:
                time.sleep(1)
                print(f"⚠️ timeout - {row['url']}")
                continue
            answer = response['choices'][0]['message']['content']
            if answer != 'TRUE':
                failed_results.append({'row': row, 'result': response})
                print(f"🔴 {answer} - {row['url']}")
                if len(failed_results) > 200:
                    print("Found 200 failing URLs. Stopping.")
                    self._write_dict_to_json_file(failed_results_file, failed_results)
                    break
            else:
                print(f"✔️ {answer} - {row['url']}")
            results.append({'row': row, 'result': response})
            time.sleep(1)

        self._write_dict_to_json_file(full_results_file, results)

        print(results)

    @staticmethod
    def _gpt_generate(messages: dict) -> dict:
        openai.organization = "org-nAxqvVYeP9LfuEhGpvPHZkA1"
        openai.api_key = os.getenv("OPENAI_API_KEY")
        try_count = 0
        while try_count < 3:
            try:
                result = openai.ChatCompletion.create(
                    model='gpt-4',
                    messages=messages,
                    max_tokens=10,
                    temperature=0.8,
                )
                return result
            except Exception as e:
                print(e)
                time.sleep(5)
                try_count += 1
        return None

    def json_to_csv(self, json_filename, csv_filename):
        # Read JSON file
        with open(json_filename, 'r') as json_file:
            json_data = json.load(json_file)

        # Extract the required columns
        csv_data = self.extract_required_columns(json_data)

        # Write CSV file
        PhishEval._write_csv(csv_filename, csv_data)

    @staticmethod
    def extract_required_columns(json_data):
        csv_data = []
        for entry in json_data:
            row = entry["row"]
            csv_data.append({
                "phish_id": row["phish_id"],
                "url": row["url"],
                "target": row["target"]
            })
        return csv_data

    def _generate_prompt(self, row: dict) -> dict:
        _messages = self._generate_prompt_messages(row)
        return _messages

    def _generate_eval(self, row: dict) -> dict:
        _messages = self._generate_prompt_messages(row)
        messages = {"input": _messages, "ideal": "TRUE"}
        return messages

    @staticmethod
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

    def _download_latest_dataset(self) -> str:
        gzip_content = self._download_file(DATASET_SOURCE)
        csv_content = self._gunzip_file(gzip_content)
        all_rows = self._csv_str_to_rows(csv_content)
        filtered_rows = self._filter_rows(all_rows)
        out_path = f"online_valid_{time.strftime('%Y_%m_%d_%H_%M_%S')}.csv"
        self._write_csv(out_path, filtered_rows)
        return out_path

    @staticmethod
    def _write_dict_to_json_file(filename, data):
        with open(filename, 'w') as outfile:
            json.dump(data, outfile, indent=4)

    @staticmethod
    def _csv_str_to_rows(csv_str: str) -> list[dict[str, str]]:
        return list(csv.DictReader(io.StringIO(csv_str)))

    @staticmethod
    def _read_csv(path: str) -> list[dict[str, str]]:
        with open(path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            return list(reader)

    @staticmethod
    def _write_csv(path: str, rows: list[dict[str, str]]) -> None:
        with open(path, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    @staticmethod
    def _filter_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
        new_rows = rows
        # new_rows = [row for row in new_rows if row['target'] != 'Other' and row['verified'] == 'yes']
        new_rows = [{k: v for k, v in row.items() if k in ['phish_id', 'url', 'target']} for row in new_rows]
        return new_rows

    @staticmethod
    def _download_file(url: str) -> bytes:
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            file_content = response.content
        return file_content

    @staticmethod
    def _gunzip_file(input_gzip_content: bytes) -> str:
        with gzip.open(io.BytesIO(input_gzip_content), 'rb') as gzipped_file:
            decompressed_content = gzipped_file.read().decode('utf-8')
        return decompressed_content


if __name__ == '__main__':
    # Check if "download" was passed as the sole command-line argument.
    download = False
    if len(sys.argv) == 2:
        if sys.argv[1] == 'download':
            download = True
    phish_eval = PhishEval()
    phish_eval.eval(download)
