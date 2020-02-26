from DataSetHandler import DataSetHandler


def main():
    d = DataSetHandler(files_prefix="saque", directory="dataset")
    d.process_dataset()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('Killed by user')