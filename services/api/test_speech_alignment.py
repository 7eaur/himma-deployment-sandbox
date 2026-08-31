from speech_alignment import align_reference, alignment_counts, normalize_arabic


def test_arabic_normalization_ignores_diacritics_and_common_alef_variants():
    assert normalize_arabic("إِلَى الْمَدْرَسَةِ") == "الي المدرسة"
    assert normalize_arabic("أَكَلَ") == normalize_arabic("اكل")


def test_exact_reading_with_undiacritized_asr_is_correct():
    tokens = align_reference("ذَهَبَ سَالِمٌ إِلَى الْمَدْرَسَةِ", "ذهب سالم الى المدرسة")
    assert alignment_counts(tokens) == {
        "correct": 4,
        "deletion": 0,
        "insertion": 0,
        "substitution": 0,
    }


def test_deletion_is_classified():
    tokens = align_reference("ذهب سالم إلى المدرسة", "ذهب إلى المدرسة")
    counts = alignment_counts(tokens)
    assert counts["deletion"] == 1
    assert counts["substitution"] == 0


def test_insertion_is_classified():
    tokens = align_reference("ذهب سالم إلى المدرسة", "ذهب سالم اليوم إلى المدرسة")
    counts = alignment_counts(tokens)
    assert counts["insertion"] == 1
    assert counts["deletion"] == 0


def test_substitution_is_classified():
    tokens = align_reference("ذهب سالم إلى المدرسة", "ذهب خالد إلى المدرسة")
    counts = alignment_counts(tokens)
    assert counts["substitution"] == 1
    assert counts["deletion"] == 0
    assert counts["insertion"] == 0


def test_empty_hypothesis_deletes_all_reference_words():
    tokens = align_reference("قرأ خالد كتابا", "")
    assert alignment_counts(tokens)["deletion"] == 3
