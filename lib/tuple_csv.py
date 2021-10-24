import csv
def tuple_csv(data, path, headers=None):
    # note: If you use 'b' for the mode, you will get a TypeError
    # under Python3. You can just use 'w' for Python 3

    with open(path,'w', encoding='utf-8', newline='') as out:
        csv_out=csv.writer(out, delimiter=";")

        if headers is not None:
            csv_out.writerow(headers)

        for row in data:
            csv_out.writerow(list(row))

        # You can also do csv_out.writerows(data) instead of the for loop