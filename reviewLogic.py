def calculate_new_ef_interval(data, word):
    weighted_total = 8.7
    weighted_correct = 0.0
    if data["translation"] == data["definition"]:
        weighted_correct += 1.0
    