"""Evaluation set for skill extraction precision and recall.

This module contains a small hand-labeled evaluation set of 10 synthetic
resume texts to measure precision and recall of the skill extraction engine.

Note: This is a small evaluation set (10 samples) for demonstration.
It is NOT production-grade evaluation. Real evaluation would require
much larger datasets with diverse resume formats and domains.
"""


# Hand-labeled evaluation set
# Each entry has: resume_text, expected_skills (canonical names)
# IMPORTANT: Expected skills must be EXHAUSTIVE for all skills explicitly supported by the text
# Domain keywords are measured separately - this evaluation focuses on technical skill extraction only
EVALUATION_SET = [
    {
        "text": """
        Software Engineer with 3 years of experience in full-stack development.
        Proficient in Python, Django, PostgreSQL, and React. Experienced with
        Docker and Kubernetes for containerization. Familiar with AWS cloud services.
        """,
        "expected_skills": [
            "AWS",
            "Django",
            "Docker",
            "Kubernetes",
            "PostgreSQL",
            "Python",
            "React",
        ],
    },
    {
        "text": """
        Data Scientist specializing in machine learning and NLP.
        Experience with TensorFlow, PyTorch, and scikit-learn. Worked with
        Apache Spark for big data processing. Knowledge of SQL and Python.
        """,
        "expected_skills": [
            "Apache Spark",
            "Machine Learning",
            "NLP",
            "Python",
            "PyTorch",
            "Scikit-learn",
            "SQL",
            "TensorFlow",
        ],
    },
    {
        "text": """
        DevOps Engineer with expertise in CI/CD pipelines and infrastructure automation.
        Proficient in Terraform, Ansible, and Jenkins. Experience with Docker,
        Kubernetes, and AWS. Strong knowledge of Linux and shell scripting.
        """,
        "expected_skills": [
            "Ansible",
            "AWS",
            "Bash",
            "Docker",
            "Jenkins",
            "Kubernetes",
            "Linux",
            "Terraform",
        ],
    },
    {
        "text": """
        Frontend Developer focused on modern JavaScript frameworks.
        Expert in React, TypeScript, and Vue.js. Experience with Next.js
        and Tailwind CSS. Familiar with Jest and Cypress for testing.
        """,
        "expected_skills": [
            "CSS",
            "Cypress",
            "Jest",
            "JavaScript",
            "Next.js",
            "React",
            "Tailwind CSS",
            "TypeScript",
            "Vue",
        ],
    },
    {
        "text": """
        Backend Developer experienced in building REST APIs and microservices.
        Proficient in Java, Spring Boot, and PostgreSQL. Experience with
        Redis for caching and Elasticsearch for search. Knowledge of Docker.
        """,
        "expected_skills": [
            "Docker",
            "Elasticsearch",
            "Java",
            "PostgreSQL",
            "Redis",
            "REST",
            "Spring",
        ],
    },
    {
        "text": """
        Mobile Developer with experience in cross-platform development.
        Proficient in React Native and Flutter. Familiar with iOS (Swift)
        and Android (Kotlin) native development. Experience with Firebase.
        """,
        "expected_skills": [
            "Android",
            "Cross-Platform",
            "Firebase",
            "Flutter",
            "iOS",
            "Kotlin",
            "React",
            "React Native",
            "Swift",
        ],
    },
    {
        "text": """
        Full Stack Developer with expertise in JavaScript ecosystem.
        Proficient in Node.js, Express, and MongoDB. Experience with React
        and Redux for frontend. Knowledge of GraphQL and REST APIs.
        """,
        "expected_skills": [
            "Express",
            "GraphQL",
            "JavaScript",
            "MongoDB",
            "Node.js",
            "React",
            "Redux",
            "REST",
        ],
    },
    {
        "text": """
        Security Engineer focused on application security and penetration testing.
        Experience with Burp Suite, OWASP ZAP, and Nmap. Knowledge of
        cybersecurity best practices, OAuth, and JWT authentication.
        """,
        "expected_skills": [
            "Application Security",
            "Burp Suite",
            "JWT",
            "Nmap",
            "OAuth",
            "OWASP ZAP",
            "Penetration Testing",
        ],
    },
    {
        "text": """
        Machine Learning Engineer working on computer vision projects.
        Proficient in Python, OpenCV, and TensorFlow. Experience with
        PyTorch and Keras. Knowledge of Docker and Kubernetes for deployment.
        """,
        "expected_skills": [
            "Computer Vision",
            "Docker",
            "Keras",
            "Kubernetes",
            "Machine Learning",
            "PyTorch",
            "Python",
            "TensorFlow",
        ],
    },
    {
        "text": """
        QA Engineer with experience in test automation and quality assurance.
        Proficient in Selenium, Cypress, and Jest. Knowledge of Python
        and Java for test scripting. Experience with CI/CD pipelines.
        """,
        "expected_skills": [
            "Cypress",
            "Jest",
            "Java",
            "Python",
            "Selenium",
        ],
    },
]


class TestSkillExtractionEvaluation:
    """Evaluation tests for skill extraction precision and recall."""

    def test_evaluation_set_size(self):
        """Test that evaluation set has 10 samples."""
        assert len(EVALUATION_SET) == 10

    def test_all_samples_have_expected_skills(self):
        """Test that all samples have expected skills defined."""
        for sample in EVALUATION_SET:
            assert "text" in sample
            assert "expected_skills" in sample
            assert isinstance(sample["expected_skills"], list)
            assert len(sample["expected_skills"]) > 0

    def test_compute_precision_and_recall(self):
        """Compute and report precision and recall for the evaluation set.

        This test reports precision and recall metrics but does not assert
        specific values, as the evaluation set is small and for demonstration.

        Metrics:
        - Precision = TP / (TP + FP) - How many extracted skills are correct
        - Recall = TP / (TP + FN) - How many expected skills were found
        - F1 Score = 2 * (Precision * Recall) / (Precision + Recall)

        Where:
        - TP (True Positive): Expected skill that was extracted
        - FP (False Positive): Extracted skill not in expected
        - FN (False Negative): Expected skill not extracted
        """
        from api.ingestion.skill_extraction import (
            extract_skills as legacy_extract_skills,
        )

        total_tp = 0
        total_fp = 0
        total_fn = 0

        print("\n" + "=" * 60)
        print("Skill Extraction Evaluation Results (Per-Resume)")
        print("=" * 60)

        for i, sample in enumerate(EVALUATION_SET, 1):
            text = sample["text"]
            expected = set(sample["expected_skills"])

            # Extract skills using legacy wrapper (returns strings)
            extracted = set(legacy_extract_skills(text))

            # Calculate metrics for this sample
            tp = len(expected.intersection(extracted))
            fp = len(extracted - expected)
            fn = len(expected - extracted)

            total_tp += tp
            total_fp += fp
            total_fn += fn

            # Calculate per-sample metrics
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = (
                2 * (precision * recall) / (precision + recall)
                if (precision + recall) > 0
                else 0
            )

            print(f"\nSample {i}:")
            print(f"  TP: {tp}, FP: {fp}, FN: {fn}")
            print(f"  Precision: {precision:.2%}, Recall: {recall:.2%}, F1: {f1:.2%}")
            if fp > 0:
                print(f"  False Positives: {sorted(extracted - expected)}")
            if fn > 0:
                print(f"  False Negatives: {sorted(expected - extracted)}")

        # Calculate overall metrics
        precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
        recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
        f1 = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0
        )

        # Report aggregate metrics
        print("\n" + "=" * 60)
        print("Aggregate Metrics")
        print("=" * 60)
        print(f"Total samples: {len(EVALUATION_SET)}")
        print(f"True Positives: {total_tp}")
        print(f"False Positives: {total_fp}")
        print(f"False Negatives: {total_fn}")
        print(f"Precision: {precision:.2%}")
        print(f"Recall: {recall:.2%}")
        print(f"F1 Score: {f1:.2%}")
        print("=" * 60)

        # Document evaluation methodology
        print("\nEvaluation Methodology:")
        print("- Expected labels: Hand-labeled by human (author)")
        print("- True Positive: Expected skill extracted correctly")
        print("- False Positive: Extracted skill not in expected set")
        print("- False Negative: Expected skill not extracted")
        print("- Note: Small evaluation set (10 samples) for demonstration")
        print("- Not production-grade evaluation")
        print("- Real evaluation requires larger, diverse datasets")

        # Document limitations
        print("\nLimitations:")
        print("- Small sample size (10 resumes)")
        print("- Synthetic/idealized resume text")
        print("- Limited domain coverage")
        print("- Hand-labeled by single author (potential bias)")
        print("- Not representative of real-world resume diversity")
        print("- Does not test edge cases or ambiguous descriptions")

        # This test does not assert specific metric values
        # because the evaluation set is for demonstration only
        # In production, you would:
        # 1. Use a much larger evaluation set (100+ samples)
        # 2. Have multiple annotators for labels
        # 3. Use diverse, real-world resume samples
        # 4. Establish minimum precision/recall thresholds
        # 5. Test on held-out data from different sources

    def test_sample_1_extraction(self):
        """Test extraction for sample 1 (Full-stack Python/React)."""
        from api.ingestion.skill_extraction import (
            extract_skills as legacy_extract_skills,
        )

        sample = EVALUATION_SET[0]
        extracted = set(legacy_extract_skills(sample["text"]))
        expected = set(sample["expected_skills"])

        # Check that key skills are found
        assert "Python" in extracted
        assert "Django" in extracted
        assert "React" in extracted

        # Report missing and extra skills
        missing = expected - extracted
        extra = extracted - expected

        if missing:
            print(f"\nSample 1 Missing skills: {missing}")
        if extra:
            print(f"\nSample 1 Extra skills: {extra}")

    def test_sample_2_extraction(self):
        """Test extraction for sample 2 (Data Science/ML)."""
        from api.ingestion.skill_extraction import (
            extract_skills as legacy_extract_skills,
        )

        sample = EVALUATION_SET[1]
        extracted = set(legacy_extract_skills(sample["text"]))
        set(sample["expected_skills"])

        # Check that key skills are found
        assert "Python" in extracted
        assert "TensorFlow" in extracted or "PyTorch" in extracted

    def test_sample_3_extraction(self):
        """Test extraction for sample 3 (DevOps)."""
        from api.ingestion.skill_extraction import (
            extract_skills as legacy_extract_skills,
        )

        sample = EVALUATION_SET[2]
        extracted = set(legacy_extract_skills(sample["text"]))
        set(sample["expected_skills"])

        # Check that key skills are found
        assert "Docker" in extracted
        assert "Kubernetes" in extracted
        assert "Terraform" in extracted or "Ansible" in extracted

    def test_all_samples_extract_something(self):
        """Test that all samples extract at least some skills."""
        from api.ingestion.skill_extraction import (
            extract_skills as legacy_extract_skills,
        )

        for sample in EVALUATION_SET:
            extracted = legacy_extract_skills(sample["text"])
            assert len(extracted) > 0, f"No skills extracted from sample: {sample['text'][:50]}..."

    def test_false_positive_rejection_misleading_mentions(self):
        """Test that extractor correctly rejects misleading or incidental mentions.

        This ensures the extractor doesn't over-match on words that look like
        skill names but are used in ordinary contexts.

        Note: Very short single-letter skills (C, R, Go) have edge cases where
        they may match in ordinary prose. This is a known limitation of the
        current boundary-based approach.
        """
        from api.ingestion.skill_extraction import (
            extract_skills as legacy_extract_skills,
        )

        # Example 1: "R" in "car" or "area" should not match
        text1 = "The car is parked in the area."
        extracted1 = set(legacy_extract_skills(text1))
        assert "R" not in extracted1, "Should not extract 'R' from ordinary prose"

        # Example 2: "C" in "cat" or "music" should not match
        text2 = "The cat likes music."
        extracted2 = set(legacy_extract_skills(text2))
        assert "C" not in extracted2, "Should not extract 'C' from ordinary prose"

        # Example 3: "Python" in "pythonic" should not match
        text3 = "The code is written in a pythonic style."
        extracted3 = set(legacy_extract_skills(text3))
        assert "Python" not in extracted3, "Should not extract 'Python' from 'pythonic'"

        # Example 4: "SQL" in "sequel" should not match
        text4 = "This is the sequel to the previous movie."
        extracted4 = set(legacy_extract_skills(text4))
        assert "SQL" not in extracted4, "Should not extract 'SQL' from 'sequel'"

        # Example 5: "React" in "reaction" should not match
        text5 = "The chemical reaction was explosive."
        extracted5 = set(legacy_extract_skills(text5))
        assert "React" not in extracted5, "Should not extract 'React' from 'reaction'"
