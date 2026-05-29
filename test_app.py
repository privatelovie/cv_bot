import unittest

from app import Job, clean_text, deduplicate_jobs, extract_skills, rank_jobs


class TestAppHelpers(unittest.TestCase):
    def test_extract_skills(self):
        cv_text = "Python developer with AWS, Docker and SQL experience"
        skills = extract_skills(cv_text)
        self.assertIn("python", skills)
        self.assertIn("aws", skills)
        self.assertIn("docker", skills)
        self.assertIn("sql", skills)

    def test_deduplicate_jobs(self):
        jobs = [
            Job("Backend Engineer", "Acme", "Remote", "python", "u1", "X"),
            Job("backend engineer", "acme", "Remote", "python", "u2", "Y"),
            Job("Data Analyst", "Beta", "NY", "sql", "u3", "X"),
        ]
        deduped = deduplicate_jobs(jobs)
        self.assertEqual(len(deduped), 2)

    def test_rank_jobs(self):
        cv = "python fastapi docker"
        jobs = [
            Job("Python Dev", "A", "R", "python fastapi backend", "u1", "S"),
            Job("Designer", "B", "R", "figma photoshop", "u2", "S"),
        ]
        ranked = rank_jobs(cv, jobs)
        self.assertEqual(ranked[0][0].title, "Python Dev")

    def test_clean_text(self):
        raw = "<p>Hello&nbsp;World</p>\n<div>Role</div>"
        self.assertEqual(clean_text(raw), "Hello World Role")


if __name__ == "__main__":
    unittest.main()
