import io
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.users.models import User
from .models import Resume
from .services.validators import validate_resume_file
from .services.storage import ResumeStorageService


class ResumeValidatorTests(TestCase):
    """Test resume file validation"""
    
    def test_valid_pdf_file(self):
        """Test that a valid PDF file passes validation"""
        # Create a minimal valid PDF file
        pdf_content = b"%PDF-1.4\n%fake pdf content"
        file = SimpleUploadedFile("resume.pdf", pdf_content, content_type="application/pdf")
        
        # Should not raise ValidationError
        try:
            validate_resume_file(file)
        except ValidationError as e:
            self.fail(f"validate_resume_file raised {e} unexpectedly")
    
    def test_valid_docx_file(self):
        """Test that a valid DOCX file passes validation"""
        # Create a minimal valid DOCX file (ZIP archive)
        docx_content = b"PK\x03\x04" + b"\x00" * 100  # ZIP signature
        file = SimpleUploadedFile("resume.docx", docx_content, content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        
        # Should not raise ValidationError
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
        exe_content = b"MZ\x90\x00"  # EXE signature
        file = SimpleUploadedFile("malware.exe", exe_content, content_type="application/x-msdownload")
        
        with self.assertRaises(ValidationError) as context:
            validate_resume_file(file)
        self.assertIn("Invalid file extension", str(context.exception))
    
    def test_oversized_file(self):
        """Test that files larger than 10MB are rejected"""
        # Create a file larger than 10MB
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
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
        # File has .pdf extension but doesn't start with %PDF
        fake_pdf = b"NOT A PDF"
        file = SimpleUploadedFile("fake.pdf", fake_pdf, content_type="application/pdf")
        
        with self.assertRaises(ValidationError) as context:
            validate_resume_file(file)
        self.assertIn("Invalid PDF file", str(context.exception))
    
    def test_invalid_docx_signature(self):
        """Test that files with .docx extension but invalid signature are rejected"""
        # File has .docx extension but doesn't start with PK (ZIP)
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
        
        # Filenames should be different
        self.assertNotEqual(filename1, filename2)
        
        # Both should have .pdf extension
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


class ResumeUploadViewTests(TestCase):
    """Test resume upload endpoint"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create candidate user
        self.candidate = User.objects.create_user(
            email="candidate@example.com",
            password="testpass123",
            full_name="Candidate User",
            role=User.Roles.CANDIDATE,
        )
        
        # Create recruiter user
        self.recruiter = User.objects.create_user(
            email="recruiter@example.com",
            password="testpass123",
            full_name="Recruiter User",
            role=User.Roles.RECRUITER,
        )
    
    def test_candidate_upload_pdf_success(self):
        """Test that candidate can upload PDF successfully"""
        # Authenticate as candidate
        self.client.force_authenticate(user=self.candidate)
        
        # Create a valid PDF file
        pdf_content = b"%PDF-1.4\n%fake pdf content"
        file = SimpleUploadedFile("resume.pdf", pdf_content, content_type="application/pdf")
        
        # Upload file
        response = self.client.post("/api/resumes/upload/", {"file": file}, format="multipart")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertEqual(response.data["filename"], "resume.pdf")
        self.assertIn("file_size", response.data)
        self.assertIn("uploaded_at", response.data)
        self.assertTrue(response.data["is_active"])
    
    def test_candidate_upload_docx_success(self):
        """Test that candidate can upload DOCX successfully"""
        # Authenticate as candidate
        self.client.force_authenticate(user=self.candidate)
        
        # Create a valid DOCX file
        docx_content = b"PK\x03\x04" + b"\x00" * 100
        file = SimpleUploadedFile("resume.docx", docx_content, content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        
        # Upload file
        response = self.client.post("/api/resumes/upload/", {"file": file}, format="multipart")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["filename"], "resume.docx")
    
    def test_recruiter_blocked(self):
        """Test that recruiters cannot upload resumes"""
        # Authenticate as recruiter
        self.client.force_authenticate(user=self.recruiter)
        
        # Create a valid PDF file
        pdf_content = b"%PDF-1.4\n%fake pdf content"
        file = SimpleUploadedFile("resume.pdf", pdf_content, content_type="application/pdf")
        
        # Try to upload file
        response = self.client.post("/api/resumes/upload/", {"file": file}, format="multipart")
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_anonymous_blocked(self):
        """Test that anonymous users cannot upload resumes"""
        # Don't authenticate
        
        # Create a valid PDF file
        pdf_content = b"%PDF-1.4\n%fake pdf content"
        file = SimpleUploadedFile("resume.pdf", pdf_content, content_type="application/pdf")
        
        # Try to upload file
        response = self.client.post("/api/resumes/upload/", {"file": file}, format="multipart")
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_invalid_extension_rejected(self):
        """Test that invalid file extensions are rejected"""
        # Authenticate as candidate
        self.client.force_authenticate(user=self.candidate)
        
        # Create a .txt file
        txt_content = b"some text"
        file = SimpleUploadedFile("resume.txt", txt_content, content_type="text/plain")
        
        # Try to upload file
        response = self.client.post("/api/resumes/upload/", {"file": file}, format="multipart")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_oversized_file_rejected(self):
        """Test that oversized files are rejected"""
        # Authenticate as candidate
        self.client.force_authenticate(user=self.candidate)
        
        # Create a file larger than 10MB
        large_content = b"x" * (11 * 1024 * 1024)
        file = SimpleUploadedFile("large.pdf", large_content, content_type="application/pdf")
        
        # Try to upload file
        response = self.client.post("/api/resumes/upload/", {"file": file}, format="multipart")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_active_resume_logic(self):
        """Test that new resume becomes active and previous ones are deactivated"""
        # Authenticate as candidate
        self.client.force_authenticate(user=self.candidate)
        
        # Upload first resume
        pdf_content1 = b"%PDF-1.4\n%first pdf"
        file1 = SimpleUploadedFile("resume1.pdf", pdf_content1, content_type="application/pdf")
        response1 = self.client.post("/api/resumes/upload/", {"file": file1}, format="multipart")
        
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        resume1_id = response1.data["id"]
        
        # Verify first resume is active
        resume1 = Resume.objects.get(id=resume1_id)
        self.assertTrue(resume1.is_active)
        
        # Upload second resume
        pdf_content2 = b"%PDF-1.4\n%second pdf"
        file2 = SimpleUploadedFile("resume2.pdf", pdf_content2, content_type="application/pdf")
        response2 = self.client.post("/api/resumes/upload/", {"file": file2}, format="multipart")
        
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        resume2_id = response2.data["id"]
        
        # Verify second resume is active
        resume2 = Resume.objects.get(id=resume2_id)
        self.assertTrue(resume2.is_active)
        
        # Verify first resume is now inactive
        resume1.refresh_from_db()
        self.assertFalse(resume1.is_active)
    
    def test_unique_filenames_generated(self):
        """Test that unique filenames are generated for uploads"""
        # Authenticate as candidate
        self.client.force_authenticate(user=self.candidate)
        
        # Upload first resume with name "resume.pdf"
        pdf_content1 = b"%PDF-1.4\n%first pdf"
        file1 = SimpleUploadedFile("resume.pdf", pdf_content1, content_type="application/pdf")
        response1 = self.client.post("/api/resumes/upload/", {"file": file1}, format="multipart")
        
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        resume1 = Resume.objects.get(id=response1.data["id"])
        
        # Upload second resume with same name "resume.pdf"
        pdf_content2 = b"%PDF-1.4\n%second pdf"
        file2 = SimpleUploadedFile("resume.pdf", pdf_content2, content_type="application/pdf")
        response2 = self.client.post("/api/resumes/upload/", {"file": file2}, format="multipart")
        
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        resume2 = Resume.objects.get(id=response2.data["id"])
        
        # Verify stored filenames are different
        self.assertNotEqual(resume1.stored_filename, resume2.stored_filename)
    
    def test_resume_metadata_saved(self):
        """Test that resume metadata is saved correctly"""
        # Authenticate as candidate
        self.client.force_authenticate(user=self.candidate)
        
        # Upload resume
        pdf_content = b"%PDF-1.4\n%test pdf content"
        file = SimpleUploadedFile("my_resume.pdf", pdf_content, content_type="application/pdf")
        response = self.client.post("/api/resumes/upload/", {"file": file}, format="multipart")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify metadata in database
        resume = Resume.objects.get(id=response.data["id"])
        self.assertEqual(resume.user, self.candidate)
        self.assertEqual(resume.original_filename, "my_resume.pdf")
        self.assertEqual(resume.file_size, len(pdf_content))
        self.assertEqual(resume.mime_type, "application/pdf")
        self.assertTrue(resume.is_active)
        self.assertIsNotNone(resume.uploaded_at)
    
    def test_missing_file_field(self):
        """Test that request without file field is rejected"""
        # Authenticate as candidate
        self.client.force_authenticate(user=self.candidate)

        # Try to upload without file
        response = self.client.post("/api/resumes/upload/", {}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ResumeManagementTests(TestCase):
    """Test resume management endpoints"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()

        # Create candidate users
        self.candidate1 = User.objects.create_user(
            email="candidate1@example.com",
            password="testpass123",
            full_name="Candidate One",
            role=User.Roles.CANDIDATE,
        )

        self.candidate2 = User.objects.create_user(
            email="candidate2@example.com",
            password="testpass123",
            full_name="Candidate Two",
            role=User.Roles.CANDIDATE,
        )

        # Create recruiter user
        self.recruiter = User.objects.create_user(
            email="recruiter@example.com",
            password="testpass123",
            full_name="Recruiter User",
            role=User.Roles.RECRUITER,
        )

        # Create resumes for candidate1
        pdf_content1 = b"%PDF-1.4\n%first pdf"
        file1 = SimpleUploadedFile("resume1.pdf", pdf_content1, content_type="application/pdf")
        self.resume1 = Resume.objects.create(
            user=self.candidate1,
            original_filename="resume1.pdf",
            stored_filename="uuid1.pdf",
            file=file1,
            file_size=len(pdf_content1),
            mime_type="application/pdf",
            is_active=True,
        )

        pdf_content2 = b"%PDF-1.4\n%second pdf"
        file2 = SimpleUploadedFile("resume2.pdf", pdf_content2, content_type="application/pdf")
        self.resume2 = Resume.objects.create(
            user=self.candidate1,
            original_filename="resume2.pdf",
            stored_filename="uuid2.pdf",
            file=file2,
            file_size=len(pdf_content2),
            mime_type="application/pdf",
            is_active=False,
        )

        # Create resume for candidate2
        pdf_content3 = b"%PDF-1.4\n%third pdf"
        file3 = SimpleUploadedFile("resume3.pdf", pdf_content3, content_type="application/pdf")
        self.resume3 = Resume.objects.create(
            user=self.candidate2,
            original_filename="resume3.pdf",
            stored_filename="uuid3.pdf",
            file=file3,
            file_size=len(pdf_content3),
            mime_type="application/pdf",
            is_active=True,
        )

    def test_candidate_list_resumes(self):
        """Test that candidate can list their own resumes"""
        self.client.force_authenticate(user=self.candidate1)

        response = self.client.get("/api/resumes/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        # Should be ordered newest first
        self.assertEqual(response.data[0]["id"], str(self.resume2.id))
        self.assertEqual(response.data[1]["id"], str(self.resume1.id))

    def test_candidate_list_only_own_resumes(self):
        """Test that candidate only sees their own resumes"""
        self.client.force_authenticate(user=self.candidate1)

        response = self.client.get("/api/resumes/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        # Should not include candidate2's resume
        resume_ids = [r["id"] for r in response.data]
        self.assertNotIn(str(self.resume3.id), resume_ids)

    def test_candidate_retrieve_own_resume(self):
        """Test that candidate can retrieve their own resume"""
        self.client.force_authenticate(user=self.candidate1)

        response = self.client.get(f"/api/resumes/{self.resume1.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.resume1.id))
        self.assertEqual(response.data["filename"], "resume1.pdf")
        self.assertIn("mime_type", response.data)

    def test_candidate_cannot_retrieve_other_user_resume(self):
        """Test that candidate cannot retrieve another user's resume"""
        self.client.force_authenticate(user=self.candidate1)

        response = self.client.get(f"/api/resumes/{self.resume3.id}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_active_resume_endpoint(self):
        """Test that active resume endpoint returns active resume"""
        self.client.force_authenticate(user=self.candidate1)

        response = self.client.get("/api/resumes/active/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.resume1.id))
        self.assertTrue(response.data["is_active"])

    def test_active_resume_not_found(self):
        """Test that active resume returns 404 when none exists"""
        # Deactivate all resumes for candidate2
        Resume.objects.filter(user=self.candidate2).update(is_active=False)

        self.client.force_authenticate(user=self.candidate2)

        response = self.client.get("/api/resumes/active/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_activate_resume(self):
        """Test that candidate can activate a resume"""
        self.client.force_authenticate(user=self.candidate1)

        response = self.client.patch(f"/api/resumes/{self.resume2.id}/activate/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_active"])

        # Verify in database
        self.resume1.refresh_from_db()
        self.resume2.refresh_from_db()
        self.assertFalse(self.resume1.is_active)
        self.assertTrue(self.resume2.is_active)

    def test_activate_switches_active_flag(self):
        """Test that activating a resume switches the active flag"""
        self.client.force_authenticate(user=self.candidate1)

        # Initially resume1 is active
        self.assertTrue(self.resume1.is_active)
        self.assertFalse(self.resume2.is_active)

        # Activate resume2
        response = self.client.patch(f"/api/resumes/{self.resume2.id}/activate/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify flags switched
        self.resume1.refresh_from_db()
        self.resume2.refresh_from_db()
        self.assertFalse(self.resume1.is_active)
        self.assertTrue(self.resume2.is_active)

    def test_delete_resume(self):
        """Test that candidate can delete their resume"""
        self.client.force_authenticate(user=self.candidate1)

        response = self.client.delete(f"/api/resumes/{self.resume2.id}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify resume is deleted from database
        self.assertFalse(Resume.objects.filter(id=self.resume2.id).exists())

    def test_delete_removes_file(self):
        """Test that deleting resume removes file from storage"""
        from django.core.files.storage import default_storage

        self.client.force_authenticate(user=self.candidate1)

        file_path = self.resume2.file.name

        # Verify file exists before deletion
        self.assertTrue(default_storage.exists(file_path))

        response = self.client.delete(f"/api/resumes/{self.resume2.id}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify file is deleted from storage
        self.assertFalse(default_storage.exists(file_path))

    def test_recruiter_blocked_from_list(self):
        """Test that recruiters cannot list resumes"""
        self.client.force_authenticate(user=self.recruiter)

        response = self.client.get("/api/resumes/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_recruiter_blocked_from_retrieve(self):
        """Test that recruiters cannot retrieve resumes"""
        self.client.force_authenticate(user=self.recruiter)

        response = self.client.get(f"/api/resumes/{self.resume1.id}/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_recruiter_blocked_from_active(self):
        """Test that recruiters cannot access active resume endpoint"""
        self.client.force_authenticate(user=self.recruiter)

        response = self.client.get("/api/resumes/active/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_recruiter_blocked_from_activate(self):
        """Test that recruiters cannot activate resumes"""
        self.client.force_authenticate(user=self.recruiter)

        response = self.client.patch(f"/api/resumes/{self.resume1.id}/activate/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_recruiter_blocked_from_delete(self):
        """Test that recruiters cannot delete resumes"""
        self.client.force_authenticate(user=self.recruiter)

        response = self.client.delete(f"/api/resumes/{self.resume1.id}/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_blocked_from_list(self):
        """Test that anonymous users cannot list resumes"""
        response = self.client.get("/api/resumes/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_anonymous_blocked_from_retrieve(self):
        """Test that anonymous users cannot retrieve resumes"""
        response = self.client.get(f"/api/resumes/{self.resume1.id}/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_anonymous_blocked_from_active(self):
        """Test that anonymous users cannot access active resume endpoint"""
        response = self.client.get("/api/resumes/active/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_anonymous_blocked_from_activate(self):
        """Test that anonymous users cannot activate resumes"""
        response = self.client.patch(f"/api/resumes/{self.resume1.id}/activate/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_anonymous_blocked_from_delete(self):
        """Test that anonymous users cannot delete resumes"""
        response = self.client.delete(f"/api/resumes/{self.resume1.id}/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_ordering_newest_first(self):
        """Test that resumes are ordered newest first"""
        self.client.force_authenticate(user=self.candidate1)

        response = self.client.get("/api/resumes/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # resume2 was created after resume1 (based on test setup order)
        self.assertEqual(response.data[0]["id"], str(self.resume2.id))
        self.assertEqual(response.data[1]["id"], str(self.resume1.id))

    def test_transaction_behavior_on_activate(self):
        """Test that activation is transactional"""
        from django.db import transaction

        self.client.force_authenticate(user=self.candidate1)

        # Manually test transaction behavior by checking database state
        with transaction.atomic():
            # Activate resume2
            response = self.client.patch(f"/api/resumes/{self.resume2.id}/activate/")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            # Verify only one active resume exists
            active_count = Resume.objects.filter(user=self.candidate1, is_active=True).count()
            self.assertEqual(active_count, 1)

    def test_delete_nonexistent_resume(self):
        """Test that deleting non-existent resume returns 404"""
        self.client.force_authenticate(user=self.candidate1)

        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = self.client.delete(f"/api/resumes/{fake_uuid}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_activate_nonexistent_resume(self):
        """Test that activating non-existent resume returns 404"""
        self.client.force_authenticate(user=self.candidate1)

        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = self.client.patch(f"/api/resumes/{fake_uuid}/activate/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ResumeParsingTests(TestCase):
    """Test resume parsing functionality"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()

        # Create candidate user
        self.candidate = User.objects.create_user(
            email="candidate@example.com",
            password="testpass123",
            full_name="Candidate User",
            role=User.Roles.CANDIDATE,
        )

        # Create recruiter user
        self.recruiter = User.objects.create_user(
            email="recruiter@example.com",
            password="testpass123",
            full_name="Recruiter User",
            role=User.Roles.RECRUITER,
        )

        # Create a PDF resume
        pdf_content = b"%PDF-1.4\n%fake pdf content"
        self.pdf_file = SimpleUploadedFile("resume.pdf", pdf_content, content_type="application/pdf")
        self.pdf_resume = Resume.objects.create(
            user=self.candidate,
            original_filename="resume.pdf",
            stored_filename="uuid1.pdf",
            file=self.pdf_file,
            file_size=len(pdf_content),
            mime_type="application/pdf",
            is_active=True,
        )

        # Create a DOCX resume
        docx_content = b"PK\x03\x04" + b"\x00" * 100
        self.docx_file = SimpleUploadedFile("resume.docx", docx_content, content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        self.docx_resume = Resume.objects.create(
            user=self.candidate,
            original_filename="resume.docx",
            stored_filename="uuid2.docx",
            file=self.docx_file,
            file_size=len(docx_content),
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            is_active=False,
        )

    def test_parse_pdf_resume_success(self):
        """Test that PDF resume can be parsed successfully"""
        from unittest.mock import patch
        
        self.client.force_authenticate(user=self.candidate)

        # Mock the PDF parser to return valid text
        with patch('apps.resumes.parsers.pdf_parser.PDFResumeParser.extract_text') as mock_extract:
            mock_extract.return_value = "John Doe\nSoftware Engineer\nExperience: 5 years"
            
            response = self.client.post(f"/api/resumes/{self.pdf_resume.id}/parse/")

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn("resume_id", response.data)
            self.assertIn("status", response.data)
            self.assertIn("text_length", response.data)
            self.assertEqual(response.data["status"], "SUCCESS")
            self.assertGreater(response.data["text_length"], 0)

            # Verify ParsedResume was created
            from .models import ParsedResume
            parsed_resume = ParsedResume.objects.get(resume=self.pdf_resume)
            self.assertEqual(parsed_resume.status, ParsedResume.ParseStatus.SUCCESS)
            self.assertIsNotNone(parsed_resume.raw_text)
            self.assertIsNotNone(parsed_resume.parsed_at)

    def test_parse_docx_resume_success(self):
        """Test that DOCX resume can be parsed successfully"""
        from unittest.mock import patch
        
        self.client.force_authenticate(user=self.candidate)

        # Mock the DOCX parser to return valid text
        with patch('apps.resumes.parsers.docx_parser.DOCXResumeParser.extract_text') as mock_extract:
            mock_extract.return_value = "Jane Smith\nData Scientist\nSkills: Python, SQL"
            
            response = self.client.post(f"/api/resumes/{self.docx_resume.id}/parse/")

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["status"], "SUCCESS")

            # Verify ParsedResume was created
            from .models import ParsedResume
            parsed_resume = ParsedResume.objects.get(resume=self.docx_resume)
            self.assertEqual(parsed_resume.status, ParsedResume.ParseStatus.SUCCESS)

    def test_unsupported_mime_type_rejected(self):
        """Test that unsupported MIME types are rejected"""
        # Create a resume with unsupported MIME type
        txt_content = b"some text"
        txt_file = SimpleUploadedFile("resume.txt", txt_content, content_type="text/plain")
        txt_resume = Resume.objects.create(
            user=self.candidate,
            original_filename="resume.txt",
            stored_filename="uuid3.txt",
            file=txt_file,
            file_size=len(txt_content),
            mime_type="text/plain",
            is_active=False,
        )

        self.client.force_authenticate(user=self.candidate)

        response = self.client.post(f"/api/resumes/{txt_resume.id}/parse/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Unsupported resume MIME type", response.data["detail"])

        # Verify ParsedResume was marked as failed
        from .models import ParsedResume
        parsed_resume = ParsedResume.objects.get(resume=txt_resume)
        self.assertEqual(parsed_resume.status, ParsedResume.ParseStatus.FAILED)
        self.assertIsNotNone(parsed_resume.error_message)

    def test_corrupted_pdf_rejected(self):
        """Test that corrupted PDF files are rejected"""
        from unittest.mock import patch
        from .parsers.exceptions import CorruptedResumeError
        
        # Create a corrupted PDF file
        corrupted_pdf = b"NOT A PDF FILE"
        corrupted_file = SimpleUploadedFile("corrupted.pdf", corrupted_pdf, content_type="application/pdf")
        corrupted_resume = Resume.objects.create(
            user=self.candidate,
            original_filename="corrupted.pdf",
            stored_filename="uuid4.pdf",
            file=corrupted_file,
            file_size=len(corrupted_pdf),
            mime_type="application/pdf",
            is_active=False,
        )

        self.client.force_authenticate(user=self.candidate)

        # Mock the PDF parser to raise CorruptedResumeError
        with patch('apps.resumes.parsers.pdf_parser.PDFResumeParser.extract_text') as mock_extract:
            mock_extract.side_effect = CorruptedResumeError("Corrupted PDF file")
            
            response = self.client.post(f"/api/resumes/{corrupted_resume.id}/parse/")

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            # Verify ParsedResume was marked as failed
            from .models import ParsedResume
            parsed_resume = ParsedResume.objects.get(resume=corrupted_resume)
            self.assertEqual(parsed_resume.status, ParsedResume.ParseStatus.FAILED)

    def test_corrupted_docx_rejected(self):
        """Test that corrupted DOCX files are rejected"""
        from unittest.mock import patch
        from .parsers.exceptions import CorruptedResumeError
        
        # Create a corrupted DOCX file
        corrupted_docx = b"NOT A DOCX FILE"
        corrupted_file = SimpleUploadedFile("corrupted.docx", corrupted_docx, content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        corrupted_resume = Resume.objects.create(
            user=self.candidate,
            original_filename="corrupted.docx",
            stored_filename="uuid5.docx",
            file=corrupted_file,
            file_size=len(corrupted_docx),
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            is_active=False,
        )

        self.client.force_authenticate(user=self.candidate)

        # Mock the DOCX parser to raise CorruptedResumeError
        with patch('apps.resumes.parsers.docx_parser.DOCXResumeParser.extract_text') as mock_extract:
            mock_extract.side_effect = CorruptedResumeError("Corrupted DOCX file")
            
            response = self.client.post(f"/api/resumes/{corrupted_resume.id}/parse/")

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            # Verify ParsedResume was marked as failed
            from .models import ParsedResume
            parsed_resume = ParsedResume.objects.get(resume=corrupted_resume)
            self.assertEqual(parsed_resume.status, ParsedResume.ParseStatus.FAILED)

    def test_parsed_resume_created(self):
        """Test that ParsedResume record is created"""
        from unittest.mock import patch
        
        self.client.force_authenticate(user=self.candidate)

        # Verify no ParsedResume exists initially
        from .models import ParsedResume
        self.assertFalse(ParsedResume.objects.filter(resume=self.pdf_resume).exists())

        # Mock the parser
        with patch('apps.resumes.parsers.pdf_parser.PDFResumeParser.extract_text') as mock_extract:
            mock_extract.return_value = "Sample resume text"
            
            # Parse the resume
            response = self.client.post(f"/api/resumes/{self.pdf_resume.id}/parse/")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            # Verify ParsedResume was created
            self.assertTrue(ParsedResume.objects.filter(resume=self.pdf_resume).exists())

    def test_parse_endpoint_works(self):
        """Test that parse endpoint works end-to-end"""
        from unittest.mock import patch
        
        self.client.force_authenticate(user=self.candidate)

        # Mock the parser
        with patch('apps.resumes.parsers.pdf_parser.PDFResumeParser.extract_text') as mock_extract:
            mock_extract.return_value = "Sample resume text"
            
            response = self.client.post(f"/api/resumes/{self.pdf_resume.id}/parse/")

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["status"], "SUCCESS")
            self.assertIn("resume_id", response.data)
            self.assertIn("text_length", response.data)
            self.assertIsInstance(response.data["text_length"], int)

    def test_parse_retrieval_endpoint_works(self):
        """Test that parsed resume retrieval endpoint works"""
        from unittest.mock import patch
        
        # First parse the resume
        self.client.force_authenticate(user=self.candidate)
        
        with patch('apps.resumes.parsers.pdf_parser.PDFResumeParser.extract_text') as mock_extract:
            mock_extract.return_value = "Sample resume text"
            self.client.post(f"/api/resumes/{self.pdf_resume.id}/parse/")

        # Retrieve parsed resume info
        response = self.client.get(f"/api/resumes/{self.pdf_resume.id}/parsed/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("resume_id", response.data)
        self.assertIn("status", response.data)
        self.assertIn("text_length", response.data)
        self.assertIn("parsed_at", response.data)
        # Should NOT include raw_text
        self.assertNotIn("raw_text", response.data)

    def test_ownership_enforced_on_parse(self):
        """Test that ownership is enforced on parse endpoint"""
        # Create another candidate
        other_candidate = User.objects.create_user(
            email="other@example.com",
            password="testpass123",
            full_name="Other User",
            role=User.Roles.CANDIDATE,
        )

        # Try to parse as other candidate
        self.client.force_authenticate(user=other_candidate)
        response = self.client.post(f"/api/resumes/{self.pdf_resume.id}/parse/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_recruiter_blocked_from_parse(self):
        """Test that recruiters cannot parse resumes"""
        self.client.force_authenticate(user=self.recruiter)

        response = self.client.post(f"/api/resumes/{self.pdf_resume.id}/parse/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_blocked_from_parse(self):
        """Test that anonymous users cannot parse resumes"""
        response = self.client.post(f"/api/resumes/{self.pdf_resume.id}/parse/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_text_normalization_works(self):
        """Test that text normalization works correctly"""
        from .parsers.utils import normalize_resume_text

        # Test with multiple spaces and tabs
        text = "Hello    World\t\tTest"
        normalized = normalize_resume_text(text)
        self.assertEqual(normalized, "Hello World Test")

        # Test with multiple blank lines
        text = "Line 1\n\n\n\nLine 2"
        normalized = normalize_resume_text(text)
        self.assertEqual(normalized, "Line 1\n\nLine 2")

        # Test with leading/trailing whitespace
        text = "  Text  "
        normalized = normalize_resume_text(text)
        self.assertEqual(normalized, "Text")

    def test_re_parse_updates_existing_record(self):
        """Test that re-parsing an existing resume updates the record"""
        from unittest.mock import patch
        import time
        
        self.client.force_authenticate(user=self.candidate)

        # First parse
        with patch('apps.resumes.parsers.pdf_parser.PDFResumeParser.extract_text') as mock_extract:
            mock_extract.return_value = "First parse text"
            response1 = self.client.post(f"/api/resumes/{self.pdf_resume.id}/parse/")
            self.assertEqual(response1.status_code, status.HTTP_200_OK)

        from .models import ParsedResume
        parsed_resume = ParsedResume.objects.get(resume=self.pdf_resume)
        first_parsed_at = parsed_resume.parsed_at

        # Wait a bit to ensure timestamp difference
        time.sleep(0.01)

        # Second parse (should update existing record)
        with patch('apps.resumes.parsers.pdf_parser.PDFResumeParser.extract_text') as mock_extract:
            mock_extract.return_value = "Second parse text"
            response2 = self.client.post(f"/api/resumes/{self.pdf_resume.id}/parse/")
            self.assertEqual(response2.status_code, status.HTTP_200_OK)

        # Verify it's the same record
        parsed_resume.refresh_from_db()
        self.assertEqual(ParsedResume.objects.filter(resume=self.pdf_resume).count(), 1)
        # Verify parsed_at was updated
        self.assertGreater(parsed_resume.parsed_at, first_parsed_at)


class TextNormalizationTests(TestCase):
    """Test text normalization utility"""

    def test_normalize_whitespace(self):
        """Test that whitespace is normalized"""
        from .parsers.utils import normalize_resume_text

        text = "Multiple    spaces\t\tand\ttabs"
        normalized = normalize_resume_text(text)
        self.assertEqual(normalized, "Multiple spaces and tabs")

    def test_collapse_blank_lines(self):
        """Test that repeated blank lines are collapsed"""
        from .parsers.utils import normalize_resume_text

        text = "Line 1\n\n\n\n\nLine 2"
        normalized = normalize_resume_text(text)
        self.assertEqual(normalized, "Line 1\n\nLine 2")

    def test_trim_whitespace(self):
        """Test that leading/trailing whitespace is trimmed"""
        from .parsers.utils import normalize_resume_text

        text = "  \n  Text with spaces  \n  "
        normalized = normalize_resume_text(text)
        self.assertEqual(normalized, "Text with spaces")

    def test_empty_string(self):
        """Test that empty string is handled"""
        from .parsers.utils import normalize_resume_text

        text = ""
        normalized = normalize_resume_text(text)
        self.assertEqual(normalized, "")

    def test_none_input(self):
        """Test that None input is handled"""
        from .parsers.utils import normalize_resume_text

        text = None
        normalized = normalize_resume_text(text)
        self.assertEqual(normalized, "")
