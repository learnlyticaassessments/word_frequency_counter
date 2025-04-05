import importlib.util
import datetime
import os
import inspect
import re
import random
import string
from collections import Counter

def generate_random_text():
    words = ["".join(random.choices(string.ascii_lowercase, k=random.randint(3, 7))) for _ in range(random.randint(10, 20))]
    text = " ".join(random.choices(words, k=random.randint(20, 50)))
    return text

def get_expected_preprocess(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    return text.split()

def get_expected_word_frequency(words):
    return dict(Counter(words))

def get_expected_most_frequent(freq_dict):
    return max(freq_dict.items(), key=lambda x: x[1]) if freq_dict else None

def get_expected_filtered(freq_dict, n):
    return {k: v for k, v in freq_dict.items() if v >= n}

def test_student_code(solution_path):
    report_dir = os.path.join(os.path.dirname(__file__), "..", "student_workspace")
    report_path = os.path.join(report_dir, "report.txt")
    os.makedirs(report_dir, exist_ok=True)

    spec = importlib.util.spec_from_file_location("student_module", solution_path)
    student_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(student_module)

    CounterClass = student_module.WordFrequencyCounter
    counter = CounterClass()

    report_lines = [f"\n=== Word Frequency Counter Test Run at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ==="]

    visible_cases = [
        {"desc": "Basic Word Frequency", "func": "compute_word_frequency", "input": ['hello', 'hello', 'how', 'are', 'you'], "expected": {'hello': 2, 'how': 1, 'are': 1, 'you': 1}},
        {"desc": "Preprocess with punctuation", "func": "preprocess_text", "input": "Hello, hello! How are you?", "expected": ['hello', 'hello', 'how', 'are', 'you']},
        {"desc": "Most frequent word", "func": "get_most_frequent_word", "input": {'hello': 2, 'how': 1, 'are': 1, 'you': 1}, "expected": ('hello', 2)},
        {"desc": "Filter by frequency (no match)", "func": "filter_words_by_frequency", "input": ({'hello': 2, 'how': 1, 'are': 1, 'you': 1}, 3), "expected": {}},
        {"desc": "Large input frequency", "func": "compute_word_frequency", "input": ['a'] * 1000 + ['b'] * 500, "expected": {'a': 1000, 'b': 500}}
    ]

    logic_keywords = {
        "preprocess_text": ["split", "re.sub"],
        "compute_word_frequency": ["for", "get"],
        "get_most_frequent_word": ["max"],
        "filter_words_by_frequency": ["for"]
    }

    def detect_hardcoded(src, expected):
        # Step 1: Clean source
        lines = src.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.split('#')[0]
            if line.strip():
                cleaned_lines.append(line)
        flat_src = ''.join(cleaned_lines).replace(" ", "").lower()

        # Step 2: Normalize expected value
        normalized_expected = repr(expected).replace(" ", "").lower().replace("'", "\"")

        # Step 3: Check direct return
        if f"return{normalized_expected}" in flat_src:
            return True

        # Step 4: Check for variable assignment and return
        # Pattern: var_name = literal (tuple, list, dict, str, int, etc.)
        assignments = re.findall(r'(\w+)=([\[\(\{].*?[\]\)\}])', flat_src)  # e.g., kk = {...}
        for var_name, literal_value in assignments:
            # Normalize the value
            norm_val = literal_value.replace(" ", "").replace("'", "\"").lower()
            if norm_val == normalized_expected and f"return{var_name}" in flat_src:
                return True

        return False

    def run_randomized_hidden_tests():
        try:
            test_instance = CounterClass()

            # preprocess_text
            rand_text = generate_random_text()
            expected = get_expected_preprocess(rand_text)
            result = test_instance.preprocess_text(rand_text)
            if result != expected:
                raise Exception("preprocess_text failed on randomized input")

            # compute_word_frequency
            expected = get_expected_word_frequency(result)
            result_freq = test_instance.compute_word_frequency(result)
            if result_freq != expected:
                raise Exception("compute_word_frequency failed on randomized input")

            # get_most_frequent_word
            expected = get_expected_most_frequent(result_freq)
            result_most = test_instance.get_most_frequent_word(result_freq)
            if result_most != expected:
                raise Exception("get_most_frequent_word failed on randomized input")

            # filter_words_by_frequency
            expected = get_expected_filtered(result_freq, 2)
            result_filter = test_instance.filter_words_by_frequency(result_freq, 2)
            if result_filter != expected:
                raise Exception("filter_words_by_frequency failed on randomized input")
        except Exception as e:
            report_lines.append(f"⚠️ Hidden randomized test failed internally: {str(e)}")

    # 🔒 Run Anti-Hardcoding Randomized Check
    run_randomized_hidden_tests()

    # 🌟 Main Visible Case Evaluation with Edge Checks
    for i, case in enumerate(visible_cases, 1):
        try:
            func_name = case["func"]
            method = getattr(counter, func_name)
            src = inspect.getsource(getattr(CounterClass, func_name)).lower()

            # Edge case 1: Only pass
            if "pass" in src and len(src.strip()) < 80:
                msg = f"❌ Test Case {i} Failed: {case['desc']} | Reason: Function contains only 'pass'"
                print(msg)
                report_lines.append(msg)
                continue

            # Edge case 2: Hardcoded return
            if detect_hardcoded(src, case["expected"]):
                msg = f"❌ Test Case {i} Failed: {case['desc']} | Reason: Hardcoded return detected"
                print(msg)
                report_lines.append(msg)
                continue

            # Edge case 3: Missing logic
            expected_keywords = logic_keywords.get(func_name, [])
            if all(kw not in src for kw in expected_keywords):
                msg = f"❌ Test Case {i} Failed: {case['desc']} | Reason: Missing logic: {expected_keywords}"
                print(msg)
                report_lines.append(msg)
                continue

            # Execute function
            result = method(case["input"]) if not isinstance(case["input"], tuple) else method(*case["input"])

            if result == case["expected"]:
                msg = f"✅ Test Case {i} Passed: {case['desc']}"
            else:
                msg = f"❌ Test Case {i} Failed: {case['desc']} | Expected={case['expected']} | Actual={result}"

            print(msg)
            report_lines.append(msg)

        except Exception as e:
            msg = f"❌ Test Case {i} Crashed: {case['desc']} | Error: {str(e)}"
            print(msg)
            report_lines.append(msg)

    with open(report_path, "a", encoding="utf-8") as f:
        f.write("\n".join(report_lines) + "\n")

if __name__ == "__main__":
    solution_file = os.path.join(os.path.dirname(__file__), "..", "student_workspace", "solution.py")
    test_student_code(solution_file)
