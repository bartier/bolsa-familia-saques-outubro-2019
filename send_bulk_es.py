import os
import json
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk


def find_files_to_process(directory, files_prefix):
    files_to_process = []

    index = 0
    while True:

        filename = f'{directory}/{files_prefix}_{str(index).zfill(2)}.json'

        if os.path.exists(filename):
            files_to_process.append(filename)
            index += 1
        else:
            return files_to_process


def gendata():
    files = find_files_to_process('dataset', 'saque')
    for file in files:
        with open(file) as json_file:
            data = json.load(json_file)
            for item in data:
                yield item


def main():
    es = Elasticsearch(["https://df6373d3b55d45c4b40b5ea0a42b1bd3.us-east-1.aws.found.io:9243"],
                       api_key=("aENcfnABZdiolyHWSTVz", "ROIXYtDBTkaJqIbDO8KZ2g"))

    print(es.info())

    bulk(es, gendata(), index="bolsafamilia-saques-2019.10")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('Killed by user')
