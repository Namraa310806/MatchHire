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
