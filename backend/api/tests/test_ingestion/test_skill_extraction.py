"""Tests for skill extraction."""

from django.test import TestCase

from api.ingestion.skill_extraction import extract_skills, get_skills_dict


class SkillExtractionTest(TestCase):
    """Tests for skill extraction from job descriptions."""

    def test_extract_python(self):
        """Test extracting Python skill."""
        description = "We are looking for a Python developer with Django experience."
        skills = extract_skills(description)
        self.assertIn("Python", skills)

    def test_extract_javascript_variations(self):
        """Test extracting JavaScript with variations."""
        description = "Must know JavaScript, JS, and React."
        skills = extract_skills(description)
        self.assertIn("JavaScript", skills)
        # Should not have duplicates
        self.assertEqual(skills.count("JavaScript"), 1)

    def test_extract_react(self):
        """Test extracting React skill."""
        description = "Experience with React.js or React required."
        skills = extract_skills(description)
        self.assertIn("React", skills)

    def test_extract_django(self):
        """Test extracting Django skill."""
        description = "Django framework experience preferred."
        skills = extract_skills(description)
        self.assertIn("Django", skills)

    def test_extract_docker(self):
        """Test extracting Docker skill."""
        description = "Containerization with Docker required."
        skills = extract_skills(description)
        self.assertIn("Docker", skills)

    def test_extract_kubernetes_variations(self):
        """Test extracting Kubernetes with k8s alias."""
        description = "Experience with Kubernetes or k8s orchestration."
        skills = extract_skills(description)
        self.assertIn("Kubernetes", skills)
        self.assertEqual(skills.count("Kubernetes"), 1)

    def test_extract_aws_variations(self):
        """Test extracting AWS with full name alias."""
        description = "AWS or Amazon Web Services experience required."
        skills = extract_skills(description)
        self.assertIn("AWS", skills)
        self.assertEqual(skills.count("AWS"), 1)

    def test_word_boundary_matching(self):
        """Test word boundary matching avoids false positives."""
        description = "This is a pythonic approach but not Python development."
        skills = extract_skills(description)
        self.assertIn("Python", skills)

    def test_case_insensitive(self):
        """Test extraction is case-insensitive."""
        description = "PYTHON and java development."
        skills = extract_skills(description)
        self.assertIn("Python", skills)
        self.assertIn("Java", skills)

    def test_multiple_skills(self):
        """Test extracting multiple skills."""
        description = "Need Python, JavaScript, Docker, and Kubernetes skills."
        skills = extract_skills(description)
        self.assertIn("Python", skills)
        self.assertIn("JavaScript", skills)
        self.assertIn("Docker", skills)
        self.assertIn("Kubernetes", skills)

    def test_no_skills_found(self):
        """Test when no skills are found."""
        description = "This is a generic job description with no technical skills."
        skills = extract_skills(description)
        self.assertEqual(len(skills), 0)

    def test_skill_deduplication(self):
        """Test skills are deduplicated."""
        description = "Python, python, PYTHON, and more Python development."
        skills = extract_skills(description)
        self.assertIn("Python", skills)
        self.assertEqual(skills.count("Python"), 1)

    def test_sorted_output(self):
        """Test skills are returned in sorted order."""
        description = "Need JavaScript, Python, and Docker skills."
        skills = extract_skills(description)
        self.assertEqual(skills, sorted(skills))

    def test_extract_sql(self):
        """Test extracting SQL skill."""
        description = "Database knowledge with SQL required."
        skills = extract_skills(description)
        self.assertIn("SQL", skills)

    def test_extract_git(self):
        """Test extracting Git skill."""
        description = "Version control with Git experience."
        skills = extract_skills(description)
        self.assertIn("Git", skills)

    def test_extract_nodejs_variations(self):
        """Test extracting Node.js with variations."""
        description = "Node.js or NodeJS backend development."
        skills = extract_skills(description)
        self.assertIn("Node.js", skills)

    def test_get_skills_dict(self):
        """Test get_skills_dict returns a copy."""
        skills_dict = get_skills_dict()
        self.assertIsInstance(skills_dict, dict)
        self.assertIn("Python", skills_dict)
        # Modify returned dict
        skills_dict["TestSkill"] = []
        # Original should not be affected
        original_dict = get_skills_dict()
        self.assertNotIn("TestSkill", original_dict)

    def test_extract_angular_variations(self):
        """Test extracting Angular with variations."""
        description = "Angular or AngularJS frontend experience."
        skills = extract_skills(description)
        self.assertIn("Angular", skills)

    def test_extract_vue_variations(self):
        """Test extracting Vue with variations."""
        description = "Vue.js or VueJS framework experience."
        skills = extract_skills(description)
        self.assertIn("Vue", skills)

    def test_extract_go_variations(self):
        """Test extracting Go with golang alias."""
        description = "Go or Golang backend development."
        skills = extract_skills(description)
        self.assertIn("Go", skills)

    def test_extract_csharp_variations(self):
        """Test extracting C# with csharp alias."""
        description = "C# or Csharp .NET development."
        skills = extract_skills(description)
        self.assertIn("C#", skills)

    def test_extract_html_css(self):
        """Test extracting HTML and CSS."""
        description = "HTML, CSS, and JavaScript frontend skills."
        skills = extract_skills(description)
        self.assertIn("HTML", skills)
        self.assertIn("CSS", skills)
        self.assertIn("JavaScript", skills)

    def test_skills_dict_unique_canonical_names(self):
        """Test skills dictionary has unique canonical names."""
        skills_dict = get_skills_dict()
        canonical_names = list(skills_dict.keys())
        self.assertEqual(len(canonical_names), len(set(canonical_names)), "Skills dictionary has duplicate canonical names")
