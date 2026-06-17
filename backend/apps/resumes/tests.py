import io
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.users.models import User
from .models import Resume, ResumeVersion, ParsedResume, StructuredResume, ResumeSkill, ResumeEducation, ResumeExperience, ResumeProject, ResumeCertification
from .services.validators import validate_resume_file
from .services.storage import ResumeStorageService
from .services.extraction_service import ResumeExtractionService


class ResumeValidatorTests(TestCase):
    """Test resume file validation"""

    def test_valid_pdf_file(self):
        """Test that a valid PDF file passes validation"""
        pdf_content = b"%PDF-1.4\n%fake pdf content"
        file = SimpleUploadedFile("resume.pdf", pdf_content, content_type="application/pdf")

        try:
            validate_resume_file(file)
        except ValidationError as e:
            self.fail(f"validate_resume_file raised {e} unexpectedly")

    def test_valid_docx_file(self):
        """Test that a valid DOCX file passes validation"""
        docx_content = b"PK\x03\x04" + b"\x00" * 100
        file = SimpleUploadedFile("resume.docx", docx_content, content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

        try:
            validate_resume_file(file)
        except ValidationError as e:
            self.fail(f"validate_resume_file raised {e} unexpectedly")

    def test_invalid_extension_doc(self):
        """Test that .doc files are rejected"""
        doc_content = b"some content"
        file = SimpleUploadedFile("resume.doc", doc_content, content_type="application/msword")

        with self.assertRaises(ValidationError) as context:
            validate_resume_file(file)
        self.assertIn("Invalid file extension", str(context.exception))

    def test_invalid_extension_txt(self):
        """Test that .txt files are rejected"""
        txt_content = b"some text"
        file = SimpleUploadedFile("resume.txt", txt_content, content_type="text/plain")

        with self.assertRaises(ValidationError) as context:
            validate_resume_file(file)
        self.assertIn("Invalid file extension", str(context.exception))

    def test_invalid_extension_exe(self):
        """Test that .exe files are rejected"""
        exe_content = b"MZ\x90\x00"
        file = SimpleUploadedFile("malware.exe", exe_content, content_type="application/x-msdownload")

        with self.assertRaises(ValidationError) as context:
            validate_resume_file(file)
        self.assertIn("Invalid file extension", str(context.exception))

    def test_oversized_file(self):
        """Test that files larger than 10MB are rejected"""
        large_content = b"x" * (11 * 1024 * 1024)
        file = SimpleUploadedFile("large.pdf", large_content, content_type="application/pdf")

        with self.assertRaises(ValidationError) as context:
            validate_resume_file(file)
        self.assertIn("exceeds maximum limit", str(context.exception))

    def test_no_file_provided(self):
        """Test that missing file is rejected"""
        with self.assertRaises(ValidationError) as context:
            validate_resume_file(None)
        self.assertIn("No file provided", str(context.exception))

    def test_invalid_pdf_signature(self):
        """Test that files with .pdf extension but invalid signature are rejected"""
        fake_pdf = b"NOT A PDF"
        file = SimpleUploadedFile("fake.pdf", fake_pdf, content_type="application/pdf")

        with self.assertRaises(ValidationError) as context:
            validate_resume_file(file)
        self.assertIn("Invalid PDF file", str(context.exception))

    def test_invalid_docx_signature(self):
        """Test that files with .docx extension but invalid signature are rejected"""
        fake_docx = b"NOT A DOCX"
        file = SimpleUploadedFile("fake.docx", fake_docx, content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

        with self.assertRaises(ValidationError) as context:
            validate_resume_file(file)
        self.assertIn("Invalid DOCX file", str(context.exception))


class ResumeStorageServiceTests(TestCase):
    """Test resume storage service"""

    def test_generate_unique_filename(self):
        """Test that unique filenames are generated"""
        filename1 = ResumeStorageService.generate_unique_filename("resume.pdf")
        filename2 = ResumeStorageService.generate_unique_filename("resume.pdf")

        self.assertNotEqual(filename1, filename2)
        self.assertTrue(filename1.endswith(".pdf"))
        self.assertTrue(filename2.endswith(".pdf"))

    def test_generate_unique_filename_preserves_extension(self):
        """Test that original extension is preserved"""
        pdf_filename = ResumeStorageService.generate_unique_filename("document.pdf")
        docx_filename = ResumeStorageService.generate_unique_filename("document.docx")

        self.assertTrue(pdf_filename.endswith(".pdf"))
        self.assertTrue(docx_filename.endswith(".docx"))

    def test_generate_unique_filename_case_insensitive(self):
        """Test that extension is converted to lowercase"""
        filename = ResumeStorageService.generate_unique_filename("RESUME.PDF")
        self.assertTrue(filename.endswith(".pdf"))


class ResumeArchitectureTests(TestCase):
    """Test the new resume versioning architecture"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.candidate = User.objects.create_user(
            email="candidate@example.com",
            password="testpass123",
            full_name="Candidate User",
            role=User.Roles.CANDIDATE,
        )
        self.recruiter = User.objects.create_user(
            email="recruiter@example.com",
            password="testpass123",
            full_name="Recruiter User",
            role=User.Roles.RECRUITER,
        )

    def test_one_resume_per_user(self):
        """Test that a user can only have one Resume container"""
        self.client.force_authenticate(user=self.candidate)

        # Upload first resume
        pdf_content1 = b"%PDF-1.4\n%first pdf"
        file1 = SimpleUploadedFile("resume1.pdf", pdf_content1, content_type="application/pdf")
        response1 = self.client.post("/api/resumes/upload/", {"file": file1}, format="multipart")
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Upload second resume
        pdf_content2 = b"%PDF-1.4\n%second pdf"
        file2 = SimpleUploadedFile("resume2.pdf", pdf_content2, content_type="application/pdf")
        response2 = self.client.post("/api/resumes/upload/", {"file": file2}, format="multipart")
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)

        # Verify only one Resume exists for the user
        resume_count = Resume.objects.filter(user=self.candidate).count()
        self.assertEqual(resume_count, 1)

    def test_upload_creates_version_1(self):
        """Test that first upload creates Version 1"""
        self.client.force_authenticate(user=self.candidate)

        pdf_content = b"%PDF-1.4\n%test pdf"
        file = SimpleUploadedFile("resume.pdf", pdf_content, content_type="application/pdf")
        response = self.client.post("/api/resumes/upload/", {"file": file}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify ResumeVersion was created with version_number=1
        resume = Resume.objects.get(user=self.candidate)
        versions = ResumeVersion.objects.filter(resume=resume)
        self.assertEqual(versions.count(), 1)

        version = versions.first()
        self.assertEqual(version.version_number, 1)
        self.assertTrue(version.is_current)
        self.assertEqual(version.change_reason, "Initial upload")

    def test_second_upload_creates_version_2(self):
        """Test that second upload creates Version 2"""
        self.client.force_authenticate(user=self.candidate)

        # First upload
        pdf_content1 = b"%PDF-1.4\n%first pdf"
        file1 = SimpleUploadedFile("resume1.pdf", pdf_content1, content_type="application/pdf")
        response1 = self.client.post("/api/resumes/upload/", {"file": file1}, format="multipart")
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Second upload
        pdf_content2 = b"%PDF-1.4\n%second pdf"
        file2 = SimpleUploadedFile("resume2.pdf", pdf_content2, content_type="application/pdf")
        response2 = self.client.post("/api/resumes/upload/", {"file": file2}, format="multipart")
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)

        # Verify two versions exist
        resume = Resume.objects.get(user=self.candidate)
        versions = ResumeVersion.objects.filter(resume=resume).order_by('version_number')
        self.assertEqual(versions.count(), 2)

        # Verify version numbers
        self.assertEqual(versions[0].version_number, 1)
        self.assertEqual(versions[1].version_number, 2)

        # Verify only version 2 is current
        self.assertFalse(versions[0].is_current)
        self.assertTrue(versions[1].is_current)

    def test_third_upload_creates_version_3(self):
        """Test that third upload creates Version 3"""
        self.client.force_authenticate(user=self.candidate)

        # First upload
        pdf_content1 = b"%PDF-1.4\n%first pdf"
        file1 = SimpleUploadedFile("resume1.pdf", pdf_content1, content_type="application/pdf")
        self.client.post("/api/resumes/upload/", {"file": file1}, format="multipart")

        # Second upload
        pdf_content2 = b"%PDF-1.4\n%second pdf"
        file2 = SimpleUploadedFile("resume2.pdf", pdf_content2, content_type="application/pdf")
        self.client.post("/api/resumes/upload/", {"file": file2}, format="multipart")

        # Third upload
        pdf_content3 = b"%PDF-1.4\n%third pdf"
        file3 = SimpleUploadedFile("resume3.pdf", pdf_content3, content_type="application/pdf")
        response3 = self.client.post("/api/resumes/upload/", {"file": file3}, format="multipart")
        self.assertEqual(response3.status_code, status.HTTP_201_CREATED)

        # Verify three versions exist
        resume = Resume.objects.get(user=self.candidate)
        versions = ResumeVersion.objects.filter(resume=resume).order_by('version_number')
        self.assertEqual(versions.count(), 3)

        # Verify version numbers
        self.assertEqual(versions[0].version_number, 1)
        self.assertEqual(versions[1].version_number, 2)
        self.assertEqual(versions[2].version_number, 3)

        # Verify only version 3 is current
        self.assertFalse(versions[0].is_current)
        self.assertFalse(versions[1].is_current)
        self.assertTrue(versions[2].is_current)

    def test_exactly_one_current_version(self):
        """Test that exactly one version is current at any time"""
        self.client.force_authenticate(user=self.candidate)

        # Upload three times
        for i in range(1, 4):
            pdf_content = b"%PDF-1.4\n%pdf content"
            file = SimpleUploadedFile(f"resume{i}.pdf", pdf_content, content_type="application/pdf")
            self.client.post("/api/resumes/upload/", {"file": file}, format="multipart")

        # Verify exactly one current version exists
        resume = Resume.objects.get(user=self.candidate)
        current_count = ResumeVersion.objects.filter(resume=resume, is_current=True).count()
        self.assertEqual(current_count, 1)

    def test_resume_container_reused_across_uploads(self):
        """Test that the same Resume container is reused across uploads"""
        self.client.force_authenticate(user=self.candidate)

        # First upload
        pdf_content1 = b"%PDF-1.4\n%first pdf"
        file1 = SimpleUploadedFile("resume1.pdf", pdf_content1, content_type="application/pdf")
        response1 = self.client.post("/api/resumes/upload/", {"file": file1}, format="multipart")
        resume_id_1 = response1.data["resume_id"]

        # Second upload
        pdf_content2 = b"%PDF-1.4\n%second pdf"
        file2 = SimpleUploadedFile("resume2.pdf", pdf_content2, content_type="application/pdf")
        response2 = self.client.post("/api/resumes/upload/", {"file": file2}, format="multipart")
        resume_id_2 = response2.data["resume_id"]

        # Verify same Resume container was used
        self.assertEqual(resume_id_1, resume_id_2)

    def test_parsed_resume_linked_to_resume_version(self):
        """Test that ParsedResume is linked to ResumeVersion, not Resume"""
        from unittest.mock import patch

        self.client.force_authenticate(user=self.candidate)

        # Upload resume
        pdf_content = b"%PDF-1.4\n%test pdf"
        file = SimpleUploadedFile("resume.pdf", pdf_content, content_type="application/pdf")
        response = self.client.post("/api/resumes/upload/", {"file": file}, format="multipart")
        resume_id = response.data["resume_id"]
        version_id = response.data["id"]

        # Parse the version
        with patch('apps.resumes.parsers.pdf_parser.PDFResumeParser.extract_text') as mock_extract:
            mock_extract.return_value = "Sample resume text"
            parse_response = self.client.post(f"/api/resumes/versions/{version_id}/parse/")
            self.assertEqual(parse_response.status_code, status.HTTP_200_OK)

        # Verify ParsedResume is linked to ResumeVersion
        parsed_resume = ParsedResume.objects.get(resume_version_id=version_id)
        self.assertEqual(str(parsed_resume.resume_version.id), version_id)

    def test_parsing_version_1_does_not_affect_version_2(self):
        """Test that parsing one version doesn't affect other versions"""
        from unittest.mock import patch

        self.client.force_authenticate(user=self.candidate)

        # Upload first resume
        pdf_content1 = b"%PDF-1.4\n%first pdf"
        file1 = SimpleUploadedFile("resume1.pdf", pdf_content1, content_type="application/pdf")
        response1 = self.client.post("/api/resumes/upload/", {"file": file1}, format="multipart")
        version1_id = response1.data["id"]

        # Upload second resume
        pdf_content2 = b"%PDF-1.4\n%second pdf"
        file2 = SimpleUploadedFile("resume2.pdf", pdf_content2, content_type="application/pdf")
        response2 = self.client.post("/api/resumes/upload/", {"file": file2}, format="multipart")
        version2_id = response2.data["id"]

        # Parse version 1
        with patch('apps.resumes.parsers.pdf_parser.PDFResumeParser.extract_text') as mock_extract:
            mock_extract.return_value = "Text from version 1"
            self.client.post(f"/api/resumes/versions/{version1_id}/parse/")

        # Parse version 2
        with patch('apps.resumes.parsers.pdf_parser.PDFResumeParser.extract_text') as mock_extract:
            mock_extract.return_value = "Text from version 2"
            self.client.post(f"/api/resumes/versions/{version2_id}/parse/")

        # Verify each version has its own ParsedResume
        parsed1 = ParsedResume.objects.get(resume_version_id=version1_id)
        parsed2 = ParsedResume.objects.get(resume_version_id=version2_id)

        self.assertEqual(parsed1.raw_text, "Text from version 1")
        self.assertEqual(parsed2.raw_text, "Text from version 2")
        self.assertNotEqual(parsed1.raw_text, parsed2.raw_text)

    def test_rollback_works(self):
        """Test that rollback to a previous version works"""
        self.client.force_authenticate(user=self.candidate)

        # Upload three times
        pdf_content = b"%PDF-1.4\n%pdf content"
        for i in range(1, 4):
            file = SimpleUploadedFile(f"resume{i}.pdf", pdf_content, content_type="application/pdf")
            self.client.post("/api/resumes/upload/", {"file": file}, format="multipart")

        resume = Resume.objects.get(user=self.candidate)
        versions = list(ResumeVersion.objects.filter(resume=resume).order_by('version_number'))

        # Rollback to version 1
        response = self.client.post(
            f"/api/resumes/{resume.id}/versions/{versions[0].id}/rollback/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify version 1 is now current
        versions[0].refresh_from_db()
        versions[1].refresh_from_db()
        versions[2].refresh_from_db()

        self.assertTrue(versions[0].is_current)
        self.assertFalse(versions[1].is_current)
        self.assertFalse(versions[2].is_current)

    def test_ownership_enforced(self):
        """Test that users can only access their own resumes"""
        other_candidate = User.objects.create_user(
            email="other@example.com",
            password="testpass123",
            full_name="Other User",
            role=User.Roles.CANDIDATE,
        )

        self.client.force_authenticate(user=self.candidate)

        # Upload resume
        pdf_content = b"%PDF-1.4\n%test pdf"
        file = SimpleUploadedFile("resume.pdf", pdf_content, content_type="application/pdf")
        response = self.client.post("/api/resumes/upload/", {"file": file}, format="multipart")
        resume_id = response.data["resume_id"]

        # Try to access as other candidate
        self.client.force_authenticate(user=other_candidate)
        response = self.client.get(f"/api/resumes/{resume_id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_recruiter_blocked(self):
        """Test that recruiters are blocked from resume endpoints"""
        self.client.force_authenticate(user=self.recruiter)

        # Try to upload
        pdf_content = b"%PDF-1.4\n%test pdf"
        file = SimpleUploadedFile("resume.pdf", pdf_content, content_type="application/pdf")
        response = self.client.post("/api/resumes/upload/", {"file": file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Try to list
        response = self.client.get("/api/resumes/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_blocked(self):
        """Test that anonymous users are blocked from resume endpoints"""
        # Try to upload
        pdf_content = b"%PDF-1.4\n%test pdf"
        file = SimpleUploadedFile("resume.pdf", pdf_content, content_type="application/pdf")
        response = self.client.post("/api/resumes/upload/", {"file": file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Try to list
        response = self.client.get("/api/resumes/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_version_history_endpoint(self):
        """Test that version history endpoint works"""
        self.client.force_authenticate(user=self.candidate)

        # Upload three times
        for i in range(1, 4):
            pdf_content = b"%PDF-1.4\n%pdf content"
            file = SimpleUploadedFile(f"resume{i}.pdf", pdf_content, content_type="application/pdf")
            self.client.post("/api/resumes/upload/", {"file": file}, format="multipart")

        resume = Resume.objects.get(user=self.candidate)
        response = self.client.get(f"/api/resumes/{resume.id}/versions/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        # Should be ordered newest first
        self.assertEqual(response.data[0]["version_number"], 3)
        self.assertEqual(response.data[1]["version_number"], 2)
        self.assertEqual(response.data[2]["version_number"], 1)

    def test_current_version_endpoint(self):
        """Test that current version endpoint works"""
        self.client.force_authenticate(user=self.candidate)

        # Upload resume
        pdf_content = b"%PDF-1.4\n%test pdf"
        file = SimpleUploadedFile("resume.pdf", pdf_content, content_type="application/pdf")
        upload_response = self.client.post("/api/resumes/upload/", {"file": file}, format="multipart")
        resume_id = upload_response.data["resume_id"]

        response = self.client.get(f"/api/resumes/{resume_id}/versions/current/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_current"])
        self.assertEqual(response.data["version_number"], 1)

    def test_delete_resume_deletes_all_versions(self):
        """Test that deleting Resume deletes all versions"""
        self.client.force_authenticate(user=self.candidate)

        # Upload three times
        for i in range(1, 4):
            pdf_content = b"%PDF-1.4\n%pdf content"
            file = SimpleUploadedFile(f"resume{i}.pdf", pdf_content, content_type="application/pdf")
            self.client.post("/api/resumes/upload/", {"file": file}, format="multipart")

        resume = Resume.objects.get(user=self.candidate)
        version_count_before = ResumeVersion.objects.filter(resume=resume).count()
        self.assertEqual(version_count_before, 3)

        # Delete resume
        response = self.client.delete(f"/api/resumes/{resume.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify all versions are deleted (cascade)
        version_count_after = ResumeVersion.objects.filter(resume=resume).count()
        self.assertEqual(version_count_after, 0)

    def test_upload_returns_resume_version_data(self):
        """Test that upload endpoint returns ResumeVersion data"""
        self.client.force_authenticate(user=self.candidate)

        pdf_content = b"%PDF-1.4\n%test pdf"
        file = SimpleUploadedFile("resume.pdf", pdf_content, content_type="application/pdf")
        response = self.client.post("/api/resumes/upload/", {"file": file}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)  # version_id
        self.assertIn("resume_id", response.data)
        self.assertIn("version_number", response.data)
        self.assertIn("filename", response.data)
        self.assertIn("file_size", response.data)
        self.assertIn("is_current", response.data)
        self.assertTrue(response.data["is_current"])
        self.assertEqual(response.data["version_number"], 1)

    def test_resume_list_shows_current_version(self):
        """Test that resume list endpoint shows current version data"""
        self.client.force_authenticate(user=self.candidate)

        # Upload resume
        pdf_content = b"%PDF-1.4\n%test pdf"
        file = SimpleUploadedFile("resume.pdf", pdf_content, content_type="application/pdf")
        self.client.post("/api/resumes/upload/", {"file": file}, format="multipart")

        response = self.client.get("/api/resumes/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertIn("current_version", response.data[0])
        self.assertIsNotNone(response.data[0]["current_version"])

    def test_active_resume_endpoint_returns_resume_with_current_version(self):
        """Test that active resume endpoint returns resume with current version"""
        self.client.force_authenticate(user=self.candidate)

        # Upload resume
        pdf_content = b"%PDF-1.4\n%test pdf"
        file = SimpleUploadedFile("resume.pdf", pdf_content, content_type="application/pdf")
        self.client.post("/api/resumes/upload/", {"file": file}, format="multipart")

        response = self.client.get("/api/resumes/active/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("current_version", response.data)
        self.assertIsNotNone(response.data["current_version"])

    def test_parse_current_version_endpoint(self):
        """Test that parsing current version of resume works"""
        from unittest.mock import patch

        self.client.force_authenticate(user=self.candidate)

        # Upload resume
        pdf_content = b"%PDF-1.4\n%test pdf"
        file = SimpleUploadedFile("resume.pdf", pdf_content, content_type="application/pdf")
        upload_response = self.client.post("/api/resumes/upload/", {"file": file}, format="multipart")
        resume_id = upload_response.data["resume_id"]

        # Parse current version
        with patch('apps.resumes.parsers.pdf_parser.PDFResumeParser.extract_text') as mock_extract:
            mock_extract.return_value = "Sample resume text"
            response = self.client.post(f"/api/resumes/{resume_id}/parse/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("resume_version_id", response.data)
        self.assertIn("resume_id", response.data)
        self.assertEqual(response.data["status"], "SUCCESS")

    def test_parsed_resume_detail_for_current_version(self):
        """Test that parsed resume detail endpoint works for current version"""
        from unittest.mock import patch

        self.client.force_authenticate(user=self.candidate)

        # Upload and parse resume
        pdf_content = b"%PDF-1.4\n%test pdf"
        file = SimpleUploadedFile("resume.pdf", pdf_content, content_type="application/pdf")
        upload_response = self.client.post("/api/resumes/upload/", {"file": file}, format="multipart")
        resume_id = upload_response.data["resume_id"]

        with patch('apps.resumes.parsers.pdf_parser.PDFResumeParser.extract_text') as mock_extract:
            mock_extract.return_value = "Sample resume text"
            self.client.post(f"/api/resumes/{resume_id}/parse/")

        # Get parsed resume detail
        response = self.client.get(f"/api/resumes/{resume_id}/parsed/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("resume_version_id", response.data)
        self.assertIn("version_number", response.data)
        self.assertIn("status", response.data)

    def test_version_based_parse_endpoint(self):
        """Test that version-based parse endpoint works"""
        from unittest.mock import patch

        self.client.force_authenticate(user=self.candidate)

        # Upload resume
        pdf_content = b"%PDF-1.4\n%test pdf"
        file = SimpleUploadedFile("resume.pdf", pdf_content, content_type="application/pdf")
        upload_response = self.client.post("/api/resumes/upload/", {"file": file}, format="multipart")
        version_id = upload_response.data["id"]

        # Parse specific version
        with patch('apps.resumes.parsers.pdf_parser.PDFResumeParser.extract_text') as mock_extract:
            mock_extract.return_value = "Sample resume text"
            response = self.client.post(f"/api/resumes/versions/{version_id}/parse/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "SUCCESS")

    def test_version_based_parsed_resume_endpoint(self):
        """Test that version-based parsed resume endpoint works"""
        from unittest.mock import patch

        self.client.force_authenticate(user=self.candidate)

        # Upload and parse resume
        pdf_content = b"%PDF-1.4\n%test pdf"
        file = SimpleUploadedFile("resume.pdf", pdf_content, content_type="application/pdf")
        upload_response = self.client.post("/api/resumes/upload/", {"file": file}, format="multipart")
        version_id = upload_response.data["id"]

        with patch('apps.resumes.parsers.pdf_parser.PDFResumeParser.extract_text') as mock_extract:
            mock_extract.return_value = "Sample resume text"
            self.client.post(f"/api/resumes/versions/{version_id}/parse/")

        # Get parsed resume for specific version
        response = self.client.get(f"/api/resumes/versions/{version_id}/parsed/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("resume_version_id", response.data)
        self.assertEqual(response.data["resume_version_id"], version_id)


class ResumeExtractionTests(TestCase):
    """Test structured resume extraction functionality"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.candidate = User.objects.create_user(
            email="candidate@example.com",
            password="testpass123",
            full_name="Candidate User",
            role=User.Roles.CANDIDATE,
        )
        self.recruiter = User.objects.create_user(
            email="recruiter@example.com",
            password="testpass123",
            full_name="Recruiter User",
            role=User.Roles.RECRUITER,
        )
        self.other_candidate = User.objects.create_user(
            email="other@example.com",
            password="testpass123",
            full_name="Other User",
            role=User.Roles.CANDIDATE,
        )

    def _create_parsed_resume(self, raw_text):
        """Helper to create a parsed resume with given text"""
        self.client.force_authenticate(user=self.candidate)
        
        # Upload resume
        pdf_content = b"%PDF-1.4\n%test pdf"
        file = SimpleUploadedFile("resume.pdf", pdf_content, content_type="application/pdf")
        upload_response = self.client.post("/api/resumes/upload/", {"file": file}, format="multipart")
        version_id = upload_response.data["id"]
        
        # Parse with mock
        from unittest.mock import patch
        with patch('apps.resumes.parsers.pdf_parser.PDFResumeParser.extract_text') as mock_extract:
            mock_extract.return_value = raw_text
            self.client.post(f"/api/resumes/versions/{version_id}/parse/")
        
        return ParsedResume.objects.get(resume_version_id=version_id)

    def test_email_extraction(self):
        """Test that email is extracted from resume text"""
        raw_text = """
John Doe
Email: john.doe@example.com
Phone: (555) 123-4567
"""
        parsed_resume = self._create_parsed_resume(raw_text)
        
        # Extract
        structured_resume = ResumeExtractionService.extract(parsed_resume)
        
        self.assertEqual(structured_resume.email, "john.doe@example.com")

    def test_phone_extraction(self):
        """Test that phone number is extracted from resume text"""
        raw_text = """
Jane Smith
Email: jane@example.com
Phone: +1 (555) 987-6543
"""
        parsed_resume = self._create_parsed_resume(raw_text)
        
        # Extract
        structured_resume = ResumeExtractionService.extract(parsed_resume)
        
        self.assertIn("555", structured_resume.phone)
        self.assertIn("987", structured_resume.phone)

    def test_linkedin_extraction(self):
        """Test that LinkedIn URL is extracted from resume text"""
        raw_text = """
John Doe
Email: john@example.com
LinkedIn: https://www.linkedin.com/in/johndoe
"""
        parsed_resume = self._create_parsed_resume(raw_text)
        
        # Extract
        structured_resume = ResumeExtractionService.extract(parsed_resume)
        
        self.assertIn("linkedin.com", structured_resume.linkedin_url)
        self.assertIn("johndoe", structured_resume.linkedin_url)

    def test_github_extraction(self):
        """Test that GitHub URL is extracted from resume text"""
        raw_text = """
Jane Developer
Email: jane@example.com
GitHub: https://github.com/janedeveloper
"""
        parsed_resume = self._create_parsed_resume(raw_text)
        
        # Extract
        structured_resume = ResumeExtractionService.extract(parsed_resume)
        
        self.assertIn("github.com", structured_resume.github_url)
        self.assertIn("janedeveloper", structured_resume.github_url)

    def test_skills_extraction(self):
        """Test that skills are extracted from resume text"""
        raw_text = """
Skills
Python, Django, AWS, PostgreSQL, JavaScript, React
"""
        parsed_resume = self._create_parsed_resume(raw_text)
        
        # Extract
        structured_resume = ResumeExtractionService.extract(parsed_resume)
        
        skills = list(structured_resume.skills.values_list('name', flat=True))
        self.assertIn("Python", skills)
        self.assertIn("Django", skills)
        self.assertIn("AWS", skills)

    def test_education_extraction(self):
        """Test that education is extracted from resume text"""
        raw_text = """
Education
Bachelor of Science in Computer Science
Stanford University
2018 - 2022
"""
        parsed_resume = self._create_parsed_resume(raw_text)
        
        # Extract
        structured_resume = ResumeExtractionService.extract(parsed_resume)
        
        education = structured_resume.education.first()
        self.assertIsNotNone(education)
        # First line is treated as institution
        self.assertIn("Bachelor", education.institution)
        self.assertIn("Bachelor", education.degree)

    def test_experience_extraction(self):
        """Test that experience is extracted from resume text"""
        raw_text = """
Experience
Software Engineer at Google
June 2020 - Present
Developed scalable web applications
"""
        parsed_resume = self._create_parsed_resume(raw_text)
        
        # Extract
        structured_resume = ResumeExtractionService.extract(parsed_resume)
        
        experience = structured_resume.experience.first()
        self.assertIsNotNone(experience)
        self.assertIn("Google", experience.company)
        self.assertIn("Software Engineer", experience.job_title)

    def test_project_extraction(self):
        """Test that projects are extracted from resume text"""
        raw_text = """
Projects
E-commerce Platform
Built a full-stack e-commerce platform using Django and React
GitHub: https://github.com/user/ecommerce
"""
        parsed_resume = self._create_parsed_resume(raw_text)
        
        # Extract
        structured_resume = ResumeExtractionService.extract(parsed_resume)
        
        project = structured_resume.projects.first()
        self.assertIsNotNone(project)
        self.assertIn("E-commerce", project.title)
        self.assertIn("github.com", project.github_url)

    def test_certification_extraction(self):
        """Test that certifications are extracted from resume text"""
        raw_text = """
Certifications
AWS Certified Solutions Architect
Issued by Amazon Web Services
January 2023
"""
        parsed_resume = self._create_parsed_resume(raw_text)
        
        # Extract
        structured_resume = ResumeExtractionService.extract(parsed_resume)
        
        certification = structured_resume.certifications.first()
        self.assertIsNotNone(certification)
        self.assertIn("AWS", certification.name)
        self.assertIn("amazon", certification.issuer.lower())

    def test_re_extraction_updates_records(self):
        """Test that re-extraction replaces old records"""
        raw_text1 = """
Skills
Python, Django
"""
        parsed_resume = self._create_parsed_resume(raw_text1)
        
        # First extraction
        structured_resume1 = ResumeExtractionService.extract(parsed_resume)
        skills_count_1 = structured_resume1.skills.count()
        
        # Update raw text and re-extract
        raw_text2 = """
Skills
Python, Django, JavaScript, React
"""
        parsed_resume.raw_text = raw_text2
        parsed_resume.save()
        
        structured_resume2 = ResumeExtractionService.extract(parsed_resume)
        skills_count_2 = structured_resume2.skills.count()
        
        # Verify re-extraction replaced old records
        self.assertGreater(skills_count_2, skills_count_1)
        self.assertEqual(StructuredResume.objects.filter(resume_version=parsed_resume.resume_version).count(), 1)

    def test_extraction_endpoint_ownership_enforced(self):
        """Test that extraction endpoint enforces ownership"""
        raw_text = "John Doe\nEmail: john@example.com"
        parsed_resume = self._create_parsed_resume(raw_text)
        version_id = parsed_resume.resume_version.id
        
        # Try to extract as other candidate
        self.client.force_authenticate(user=self.other_candidate)
        response = self.client.post(f"/api/resumes/versions/{version_id}/extract/")
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_extraction_endpoint_recruiter_blocked(self):
        """Test that recruiters are blocked from extraction endpoint"""
        raw_text = "John Doe\nEmail: john@example.com"
        parsed_resume = self._create_parsed_resume(raw_text)
        version_id = parsed_resume.resume_version.id
        
        # Try to extract as recruiter
        self.client.force_authenticate(user=self.recruiter)
        response = self.client.post(f"/api/resumes/versions/{version_id}/extract/")
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_extraction_endpoint_anonymous_blocked(self):
        """Test that anonymous users are blocked from extraction endpoint"""
        raw_text = "John Doe\nEmail: john@example.com"
        parsed_resume = self._create_parsed_resume(raw_text)
        version_id = parsed_resume.resume_version.id
        
        # Try to extract as anonymous
        self.client.force_authenticate(user=None)
        response = self.client.post(f"/api/resumes/versions/{version_id}/extract/")
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_structured_endpoint_works(self):
        """Test that structured resume endpoint works"""
        raw_text = """
John Doe
Email: john@example.com
Skills
Python, Django
"""
        parsed_resume = self._create_parsed_resume(raw_text)
        
        # Extract
        structured_resume = ResumeExtractionService.extract(parsed_resume)
        version_id = parsed_resume.resume_version.id
        
        # Get structured data via API
        self.client.force_authenticate(user=self.candidate)
        response = self.client.get(f"/api/resumes/versions/{version_id}/structured/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("full_name", response.data)
        self.assertIn("email", response.data)
        self.assertIn("skills", response.data)
        self.assertEqual(len(response.data["skills"]), 2)

    def test_extraction_requires_successful_parse(self):
        """Test that extraction requires successful parsing"""
        raw_text = "John Doe\nEmail: john@example.com"
        parsed_resume = self._create_parsed_resume(raw_text)
        
        # Mark as failed
        parsed_resume.status = ParsedResume.ParseStatus.FAILED
        parsed_resume.save()
        version_id = parsed_resume.resume_version.id
        
        # Try to extract
        self.client.force_authenticate(user=self.candidate)
        response = self.client.post(f"/api/resumes/versions/{version_id}/extract/")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("successfully parsed", response.data["detail"])

    def test_structured_endpoint_ownership_enforced(self):
        """Test that structured endpoint enforces ownership"""
        raw_text = "John Doe\nEmail: john@example.com"
        parsed_resume = self._create_parsed_resume(raw_text)
        
        # Extract
        structured_resume = ResumeExtractionService.extract(parsed_resume)
        version_id = parsed_resume.resume_version.id
        
        # Try to access as other candidate
        self.client.force_authenticate(user=self.other_candidate)
        response = self.client.get(f"/api/resumes/versions/{version_id}/structured/")
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_structured_endpoint_recruiter_blocked(self):
        """Test that recruiters are blocked from structured endpoint"""
        raw_text = "John Doe\nEmail: john@example.com"
        parsed_resume = self._create_parsed_resume(raw_text)
        
        # Extract
        structured_resume = ResumeExtractionService.extract(parsed_resume)
        version_id = parsed_resume.resume_version.id
        
        # Try to access as recruiter
        self.client.force_authenticate(user=self.recruiter)
        response = self.client.get(f"/api/resumes/versions/{version_id}/structured/")
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_structured_endpoint_anonymous_blocked(self):
        """Test that anonymous users are blocked from structured endpoint"""
        raw_text = "John Doe\nEmail: john@example.com"
        parsed_resume = self._create_parsed_resume(raw_text)
        
        # Extract
        structured_resume = ResumeExtractionService.extract(parsed_resume)
        version_id = parsed_resume.resume_version.id
        
        # Try to access as anonymous
        self.client.force_authenticate(user=None)
        response = self.client.get(f"/api/resumes/versions/{version_id}/structured/")
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
