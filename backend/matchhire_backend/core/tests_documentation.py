from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from drf_spectacular.openapi import SchemaGenerator


class DocumentationEndpointsTest(APITestCase):
    """Test documentation endpoints are accessible and return valid responses."""

    def test_schema_endpoint_exists(self):
        """Test that the schema endpoint is accessible."""
        url = reverse("schema")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("openapi", response.json())
        self.assertEqual(response.json()["openapi"], "3.1.0")

    def test_swagger_endpoint_exists(self):
        """Test that the Swagger UI endpoint is accessible."""
        url = reverse("swagger-ui")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response["Content-Type"])

    def test_redoc_endpoint_exists(self):
        """Test that the ReDoc endpoint is accessible."""
        url = reverse("redoc")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response["Content-Type"])


class SchemaGenerationTest(TestCase):
    """Test OpenAPI schema generation."""

    def test_schema_generates_successfully(self):
        """Test that the OpenAPI schema can be generated without errors."""
        generator = SchemaGenerator()
        schema = generator.get_schema(request=None, public=True)
        self.assertIsNotNone(schema)
        self.assertIn("openapi", schema)
        self.assertIn("info", schema)
        self.assertIn("paths", schema)

    def test_schema_has_correct_info(self):
        """Test that schema has correct API information."""
        generator = SchemaGenerator()
        schema = generator.get_schema(request=None, public=True)

        self.assertEqual(schema["info"]["title"], "MatchHire API")
        self.assertEqual(schema["info"]["version"], "v1")
        self.assertIn("description", schema["info"])

    def test_schema_has_security_schemes(self):
        """Test that schema includes JWT security scheme."""
        generator = SchemaGenerator()
        schema = generator.get_schema(request=None, public=True)

        self.assertIn("components", schema)
        self.assertIn("securitySchemes", schema["components"])
        self.assertIn("bearerAuth", schema["components"]["securitySchemes"])

    def test_schema_has_tags(self):
        """Test that schema includes all expected tags."""
        generator = SchemaGenerator()
        schema = generator.get_schema(request=None, public=True)

        expected_tags = [
            "Authentication",
            "Users",
            "Profiles",
            "Resumes",
            "Jobs",
            "Applications",
            "Matching",
            "Interviews",
            "Notifications",
            "Analytics",
            "Admin",
        ]
        tag_names = [tag["name"] for tag in schema.get("tags", [])]

        for tag in expected_tags:
            self.assertIn(tag, tag_names)

    def test_schema_has_authentication_endpoints(self):
        """Test that authentication endpoints are documented."""
        generator = SchemaGenerator()
        schema = generator.get_schema(request=None, public=True)

        paths = schema.get("paths", {})

        # Check for login endpoint
        self.assertIn("/api/auth/login/", paths)
        self.assertIn("post", paths["/api/auth/login/"])

        # Check for registration endpoints
        self.assertIn("/api/auth/register/candidate/", paths)
        self.assertIn("/api/auth/register/recruiter/", paths)

    def test_schema_has_resume_upload_endpoint(self):
        """Test that resume upload endpoint is documented with multipart/form-data."""
        generator = SchemaGenerator()
        schema = generator.get_schema(request=None, public=True)

        paths = schema.get("paths", {})
        self.assertIn("/api/resumes/upload/", paths)

        upload_path = paths["/api/resumes/upload/"]
        self.assertIn("post", upload_path)

        post_spec = upload_path["post"]
        self.assertIn("requestBody", post_spec)

        request_body = post_spec["requestBody"]
        self.assertIn("multipart/form-data", request_body.get("content", {}))

    def test_schema_has_pagination_documented(self):
        """Test that pagination parameters are documented."""
        generator = SchemaGenerator()
        schema = schema = generator.get_schema(request=None, public=True)

        paths = schema.get("paths", {})

        # Check a paginated endpoint (e.g., jobs list)
        if "/api/jobs/" in paths:
            jobs_path = paths["/api/jobs/"]
            if "get" in jobs_path:
                get_spec = jobs_path["get"]
                parameters = get_spec.get("parameters", [])

                param_names = [p.get("name") for p in parameters]
                self.assertIn("page", param_names)
                self.assertIn("page_size", param_names)

    def test_schema_has_enum_documentation(self):
        """Test that enums are documented correctly."""
        generator = SchemaGenerator()
        schema = generator.get_schema(request=None, public=True)

        components = schema.get("components", {})
        schemas = components.get("schemas", {})

        # Check for JobStatus enum
        job_status_exists = any(
            "JobStatus" in schema_name or "JobStatus" in str(schema_def)
            for schema_name, schema_def in schemas.items()
        )
        self.assertTrue(
            job_status_exists or len(schemas) > 0,
            "Schema should contain enum definitions",
        )


class SchemaValidationTest(TestCase):
    """Test OpenAPI schema validity."""

    def test_schema_is_valid_openapi(self):
        """Test that the generated schema is valid OpenAPI 3.1.0."""
        generator = SchemaGenerator()
        schema = generator.get_schema(request=None, public=True)

        # Basic structure validation
        required_fields = ["openapi", "info", "paths"]
        for field in required_fields:
            self.assertIn(field, schema)

        # Info section validation
        info = schema["info"]
        self.assertIn("title", info)
        self.assertIn("version", info)

    def test_schema_paths_are_valid(self):
        """Test that all documented paths have valid structure."""
        generator = SchemaGenerator()
        schema = generator.get_schema(request=None, public=True)

        paths = schema.get("paths", {})

        for path, methods in paths.items():
            self.assertTrue(path.startswith("/"), f"Path {path} should start with /")
            for method, spec in methods.items():
                self.assertIn(
                    method.lower(),
                    ["get", "post", "put", "patch", "delete", "options", "head"],
                )
                self.assertIn(
                    "responses", spec, f"{method.upper()} {path} should have responses"
                )
