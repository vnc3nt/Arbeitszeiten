import csv

#data -> newdata

input_file = r'C:\Users\vnc3n\Downloads\data_rows.csv'
output_file = r'C:\Users\vnc3n\Downloads\transformed_data.csv'

categories = {
    'fat': 1,
    'weight': 2,
    'muscle': 3
}

with open(input_file, mode='r', newline='') as infile, open(output_file, mode='w', newline='') as outfile:
    reader = csv.DictReader(infile)
    fieldnames = ['userId', 'date', 'categoryId', 'data']
    writer = csv.DictWriter(outfile, fieldnames=fieldnames)

    writer.writeheader()

    for row in reader:
        user_id = row['userid']
        date = row['date']

        for category, category_id in categories.items():
            if row[category]:
                writer.writerow({
                    'userid': user_id,
                    'date': date,
                    'categoryId': category_id,
                    'data': row[category]
                })