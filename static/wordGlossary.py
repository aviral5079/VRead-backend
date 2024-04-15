import nltk
from collections import Counter
import json
from nltk.corpus import stopwords

nltk.download("punkt")
nltk.download("stopwords")


class WordCounter:
    def __init__(self):
        self.stopwords = set(stopwords.words("english"))

    def count_words_and_return_json(self, text):
        try:
            word_list = self.tokenize_text(text)
            word_counts = self.count_word_occurrences(word_list)
            json_result = self.format_word_counts_to_json(word_counts)
            return json_result
        except Exception as e:
            print(f"Error counting words: {str(e)}")
            return None

    def tokenize_text(self, text):
        words = nltk.word_tokenize(text)
        filtered_words = [
            word.lower()
            for word in words
            if word.isalpha() and word.lower() not in self.stopwords
        ]
        return filtered_words

    def count_word_occurrences(self, word_list):
        word_counts = Counter(word_list)
        return word_counts

    def format_word_counts_to_json(self, word_counts):
        formatted_list = [
            {"text": word, "value": count} for word, count in word_counts.items()
        ]
        json_result = json.dumps(formatted_list, indent=2)
        return json_result


# # Example usage:
# word_counter = WordCounter()
# input_text = "Your input text goes here."

# result_json = word_counter.count_words_and_return_json(input_text)

# if result_json:
#     print(result_json)
# else:
#     print("Error counting words.")
